from faster_whisper import WhisperModel
import sounddevice as sd
import numpy as np

# Load model once
model = WhisperModel("tiny", compute_type="int8")

samplerate = 16000
duration = 5


def record_audio():

    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    return audio.flatten()


# -------- FUNCTION CALLED FROM MAIN -------- #

def run_live_transcription():

    print("🎤 Live transcription started")
    print("Press Ctrl+C to stop\n")

    try:

        while True:

            audio_data = record_audio()

            segments, info = model.transcribe(
                audio_data,
                language="en"
            )

            for segment in segments:
                print(segment.text)

    except KeyboardInterrupt:

        print("\n🛑 Transcription stopped")


# -------- OPTIONAL: RUN DIRECTLY -------- #

if __name__ == "__main__":
    run_live_transcription()