from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np

model = WhisperModel("tiny", compute_type="int8")

samplerate = 16000
duration = 5

print("🎤 Listening... Press Ctrl+C to stop\n")

while True:

    audio = sd.rec(int(duration * samplerate),
                   samplerate=samplerate,
                   channels=1,
                   dtype="float32")

    sd.wait()

    audio = audio.flatten()

    segments, _ = model.transcribe(audio)

    for segment in segments:
        print(segment.text)