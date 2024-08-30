import os
import queue
import re
import ssl
import sys
import threading

import librosa
import numpy as np
import sounddevice as sd
import whisper
import yaml
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
socketio = SocketIO(app)

model_path = '/models/'
model_size = os.getenv('WHISPER_MODEL', 'small')
model_file_name = f"{model_size}.pt"
model_file_path = os.path.join(model_path, model_file_name)

if not os.path.exists(model_path):
    os.makedirs(model_path, exist_ok=True)
    model = whisper.load_model(model_size, download_root=model_path)
else:
    model = whisper.load_model(model_file_path)

print(f"Loaded {model_size} model from {model_path}")

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

SAMPLE_RATE = config['chunking']['data_structure']['sample_rate']
MIC_SAMPLE_RATE = 44100
BUFFER_DURATION = config['chunking']['chunking_parameters']['chunk_size']
NUM_CHUNKS = config['chunking']['chunking_parameters']['num_chunks']

audio_queue = queue.Queue()
transcribing = threading.Event()

def clean_transcription(text):
    """
    Cleans the transcription text by removing unwanted characters.

    Args:
        text (str): The text to clean.

    Returns:
        str: The cleaned text with only allowed characters.
    """
    cleaned_text = re.sub(r'[^a-zA-Z0-9.,!?\'" ]+', '', text)
    return cleaned_text

def remove_duplicate_phrases(text):
    """
    Removes duplicate phrases from the transcription text.

    Args:
        text (str): The text with potential duplicate phrases.

    Returns:
        str: The text with duplicate phrases removed.
    """
    lines = text.splitlines()
    seen_lines = set()
    cleaned_lines = []
    
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line and cleaned_line not in seen_lines:
            cleaned_lines.append(cleaned_line)
            seen_lines.add(cleaned_line)
    
    return "\n".join(cleaned_lines)


def audio_callback(indata, frames, time, status):
    """
    Callback function for the audio stream to process incoming audio data.

    Args:
        indata (np.ndarray): The audio data array.
        frames (int): The number of frames in the buffer.
        time (CData): The timestamp of the buffer.
        status (sd.CallbackFlags): The status of the stream.

    Returns:
        None
    """
    if status:
        print(status, file=sys.stderr)
    # print("Audio data received:", indata.shape, file=sys.stderr)
    audio_queue.put(indata.copy())


def transcribe_chunk(audio_buffer):
    """
    Transcribes a chunk of audio data and emits the transcription through SocketIO.

    Args:
        audio_buffer (np.ndarray): The audio data to transcribe.

    Returns:
        None
    """
    try: 
        result = model.transcribe(audio_buffer)
        if result['text']:
            print(result['text'], flush=True)
            socketio.emit('transcription', {'text': result['text']})
    except Exception as e:
        print("Error during transmission:", str(e), file=sys.stderr)

def transcription_worker():
    """
    Worker function to handle audio data from the queue, perform transcription, 
    and emit results in sequence to maintain order.

    Returns:
        None
    """
    audio_buffer = np.array([], dtype=np.float32)
    
    while transcribing.is_set():
        if not audio_queue.empty():
            data = audio_queue.get()
            if data is None:
                break

            data = librosa.resample(data[:, 0], orig_sr=MIC_SAMPLE_RATE, target_sr=SAMPLE_RATE)
            audio_buffer = np.concatenate((audio_buffer, data))
            
            if len(audio_buffer) >= SAMPLE_RATE * BUFFER_DURATION:
                chunk_size = len(audio_buffer) // NUM_CHUNKS
                
                for i in range(0, len(audio_buffer), chunk_size):
                    chunk = audio_buffer[i:i + chunk_size]
                    try:
                        result = model.transcribe(chunk)
                        
                        if isinstance(result, dict) and 'text' in result:
                            cleaned_text = clean_transcription(result['text'])
                            cleaned_text = remove_duplicate_phrases(cleaned_text)
                            print(cleaned_text, flush=True)
                            socketio.emit('transcription', {'text': cleaned_text})
                    except Exception as e:
                        print("Error during transmission:", str(e), file=sys.stderr)
                
                audio_buffer = np.array([], dtype=np.float32)

@app.route('/')
def index():
    """
    Renders the main index page.

    Returns:
        str: Rendered HTML template for the index page.
    """
    return render_template('index.html')

@app.route('/v1/start_transcription', methods=['GET'])
def start_transcription():
    """
    Starts the transcription process by enabling the transcription flag 
    and initiating the transcription worker thread.

    Returns:
        Response: JSON response indicating transcription start status.
    """
    try:
        transcribing.set()
        transcription_thread = threading.Thread(target=transcription_worker)
        transcription_thread.start()
        with sd.InputStream(callback=audio_callback, dtype='float32', channels=1, samplerate=MIC_SAMPLE_RATE):
            print("Transcribing in real-time,\n"
                "press Ctrl+C to stop...")
            while transcribing.is_set():
                sd.sleep(1000)
        return jsonify({"message": "Transcription started"}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": f"Error querying device: {str(e)}"}), 500

@app.route('/v1/stop_transcription', methods=['GET'])
def stop_transcription():
    """
    Stops the transcription process by clearing the transcription flag and 
    signaling the transcription worker to terminate.

    Returns:
        Response: JSON response indicating transcription stop status.
    """
    try:
        transcribing.clear()
        audio_queue.put(None)
        print("Transcription stopped.")
        return jsonify({"message": "Transcription stopped"}), 200
    except Exception as e:
        return jsonify({"error": f"{str(e)}"}), 500


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

