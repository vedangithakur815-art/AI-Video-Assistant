import whisper
import os
import requests
from pydub import AudioSegment

SARVAM_PIECE_SECONDS = 25
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# CORRECTION 1:
# Old: /speech-to-text-translate
# New: /speech-to-text
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text"

# CORRECTION 2:
# Keep v3 fixed so .env cannot override it
SARVAM_MODEL = "saaras:v3"

_model = None


def load_model():
    global _model

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")

    return _model


def transcribe_chunk_whisper(chunk_path: str) -> str:
    model =