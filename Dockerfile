FROM python:3.9.9-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    portaudio19-dev \
    libsndfile1 \
    pulseaudio \
    pulseaudio-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /models

# Configure PulseAudio to allow TCP connections and keep it running
RUN echo "load-module module-native-protocol-tcp auth-ip-acl=127.0.0.1; \
           load-module module-zeroconf-publish" >> /etc/pulse/default.pa

# Ensure PulseAudio daemon is running in the background
RUN pulseaudio --start --exit-idle-time=-1

EXPOSE 5000

# Start the PulseAudio server and the transcription service
CMD ["sh", "-c", "pulseaudio -D --exit-idle-time=-1 && python transcription_service.py"]

