import os
import shutil
import yt_dlp
from pydub import AudioSegment


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Use system ffmpeg if available (works on Streamlit Cloud / Linux servers).
# Falls back to the local Windows path only if that exact folder exists
# (so this still works on your own machine).
_LOCAL_WINDOWS_FFMPEG = (
    r"C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin"
)

if shutil.which("ffmpeg"):
    FFMPEG_DIR = None  # let yt-dlp/pydub find it on PATH
elif os.path.isdir(_LOCAL_WINDOWS_FFMPEG):
    FFMPEG_DIR = _LOCAL_WINDOWS_FFMPEG
else:
    FFMPEG_DIR = None


def download_youtube_audio(url: str) -> str:
    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "socket_timeout": 60,
        "retries": 10,
        "fragment_retries": 10,
        "continuedl": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
        "quiet": False,
        "noprogress": False,
    }

    if FFMPEG_DIR:
        ydl_opts["ffmpeg_location"] = FFMPEG_DIR

    print("Downloading YouTube audio...")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        original_path = ydl.prepare_filename(info)
        base_path = os.path.splitext(original_path)[0]
        wav_path = base_path + ".wav"

    if not os.path.exists(wav_path):
        raise FileNotFoundError(
            f"WAV file was not created: {wav_path}"
        )

    print(f"Audio downloaded successfully: {wav_path}")

    return wav_path


def convert_to_wav(input_path: str) -> str:
    """Convert any audio/video file to WAV."""

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)
    audio.export(output_path, format="wav")

    print(f"Converted to WAV: {output_path}")

    return output_path


def chunk_audio(wav_path: str, chunk_minutes: int = 10) -> list:

    audio = AudioSegment.from_wav(wav_path)
    chunk_ms = chunk_minutes * 60 * 1000
    chunks = []

    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start:start + chunk_ms]
        chunk_path = f"{os.path.splitext(wav_path)[0]}_chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:

    if source.startswith("http://") or source.startswith("https://"):
        print("Detected YouTube URL. Downloading audio...")
        wav_path = download_youtube_audio(source)
    else:
        print("Detected local file. Converting to WAV...")
        wav_path = convert_to_wav(source)

    print("Chunking audio...")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready — {len(chunks)} chunk(s) created.")

    return chunks