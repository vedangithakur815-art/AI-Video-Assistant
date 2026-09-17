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
    model = load_model()

    result = model.transcribe(
        chunk_path,
        task="transcribe"
    )

    return result["text"]


def _send_to_sarvam(piece_path: str) -> str:

    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    headers = {
        "api-subscription-key": SARVAM_API_KEY
    }

    with open(piece_path, "rb") as f:

        files = {
            "file": (
                os.path.basename(piece_path),
                f,
                "audio/wav"
            )
        }

        # CORRECTION 3:
        # No translate mode.
        # We want transcription in the spoken language.
        data = {
            "model": "saaras:v3"
        }

        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(
            f"\n❌ Sarvam returned {response.status_code}"
        )
        print(
            f"Response body: {response.text}\n"
        )
        response.raise_for_status()

    return response.json().get(
        "transcript",
        ""
    )


def transcribe_chunk_sarvam(chunk_path: str) -> str:

    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is not set in environment / .env"
        )

    audio = AudioSegment.from_wav(chunk_path)

    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""

    total_pieces = (
        (len(audio) + piece_ms - 1)
        // piece_ms
    )

    for i, start in enumerate(
        range(0, len(audio), piece_ms)
    ):

        piece = audio[
            start: start + piece_ms
        ]

        piece_path = f"{chunk_path}_sv_{i}.wav"

        piece.export(
            piece_path,
            format="wav"
        )

        try:
            print(
                f"  → Sarvam piece "
                f"{i + 1}/{total_pieces} ..."
            )

            full_text += (
                _send_to_sarvam(piece_path)
                + " "
            )

        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()


def transcribe_chunk(
    chunk_path: str,
    language: str = "english"
) -> str:

    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path)

    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(
    chunks: list,
