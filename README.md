# Voice-to-Text Application

This repository contains a Python-based real-time voice-to-text transcription application using Whisper, Flask, and Flask-SocketIO. The application captures live audio input, processes it using Whisper for transcription, and streams the transcribed text in real-time to a web interface.

## Table of Contents

- [Installation](#installation)
- [Dependencies](#dependencies)
- [Configuration](#configuration)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Functions](#functions)
- [License](#license)

## Installation

1. **Clone the Repository**:

    ```
    git clone https://github.com/tirsogomezey/Voice-To-Text-App.git
    ```

2. **Set Up the Virtual Environment**:

    ```
    python -m venv venv
    venv\Scripts\activate
    ```

3. **Install the Required Dependencies**:

    ```
    pip install -r requirements.txt
    ```

## Dependencies

- **Python 3.9+**
- **Librosa**: For audio processing.
- **NumPy**: For numerical operations.
- **Sounddevice**: For capturing live audio input.
- **Whisper**: For speech-to-text transcription.
- **YAML**: For loading configuration files.
- **Flask**: For the web server.
- **Flask-SocketIO**: For real-time bi-directional communication between clients and the server.

## Configuration

The application requires a `config.yaml` file in the root directory. This file contains configuration settings for audio processing, such as sample rate and chunk size.

## Usage
1. **Start the Flask Server**:

Run the following command to start the Flask server:
```
    python transcription_service.py
```

2. **Access the Application**:

Open your web browser and navigate to http://localhost:5000 to access the voice-to-text transcription interface.

## Endpoints

###### GET /
*Description*: Renders the main index page.
*Response*: HTML page.

###### GET /v1/start_transcription
*Description*: Starts the transcription process by initializing the audio stream and transcription worker.
*Response*: JSON message indicating transcription start status.

###### GET /v1/stop_transcription
*Description*: Stops the transcription process and clears the transcription flag.
*Response*: JSON message indicating transcription stop status.

## Functions
* **clean_transcription(text: str) -> str**: Cleans the transcription text by removing unwanted characters.
* **remove_duplicate_phrases(text: str) -> str**: Removes duplicate phrases from the transcription text.
* **audio_callback(indata, frames, time, status)**: Callback function for processing incoming audio data.
* **transcribe_chunk(audio_buffer: np.ndarray)**: Transcribes a chunk of audio data and emits the transcription through SocketIO.
* **transcription_worker()**: Handles audio data from the queue, performs transcription, and maintains order of results.
* **index()**: Renders the main index page.
* **start_transcription()**: Starts the transcription process and initiates the worker thread.
* **stop_transcription()**: Stops the transcription process and signals the worker to terminate.
