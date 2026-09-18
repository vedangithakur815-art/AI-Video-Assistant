import os
import shutil
import yt_dlp
from pydub import AudioSegment


DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Find FFmpeg automatically
_LOCAL_WINDOWS_FFMPEG = (
    r"C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build\bin"
)

if shutil.which("ffmpeg"):
    FFMPEG_DIR = None
elif os.path.isdir(_LOCAL_WINDOWS_FFMPEG):
    FFMPEG_DIR = _LOCAL_WINDOWS_FFMPEG
else:
    FFMPEG_DIR = None


def _youtube_options(output_path: str, format_selector: str) -> dict:
    """
    Build yt-dlp options for YouTube audio extraction.
    """

    options = {
        "format": format_selector,
        "outtmpl": output_path,

        # Network handling
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
        "file_access_retries": 5,

        # Continue partial downloads
        "continuedl": True,

        # Don't stop because of noisy console output
        "quiet": False,
        "no_warnings": False,

        # Extract audio after download
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
    }

    if FFMPEG_DIR:
        options["ffmpeg_location"] = FFMPEG_DIR

    return options


def download_youtube_audio(url: str) -> str:
    """
    Download audio from a public YouTube URL and convert it to WAV.

    Tries multiple format strategies because YouTube may expose
    different formats depending on the video.
    """

    if not url or not url.strip():
        raise ValueError("Please enter a valid YouTube URL.")

    url = url.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        raise ValueError("Please enter a valid YouTube URL.")

    output_path = os.path.join(
        DOWNLOAD_DIR,
        "%(title).150s.%(ext)s"
    )

    # Try the most compatible formats first.
    format_options = [
        "bestaudio/best",
        "ba/b",
        "best[ext=m4a]/best",
    ]

    last_error = None

    for format_selector in format_options:

        try:
            print(
                f"Trying YouTube format: {format_selector}"
            )

            ydl_opts = _youtube_options(
                output_path,
                format_selector
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                info = ydl.extract_info(
                    url,
                    download=True
                )

                if not info:
                    raise RuntimeError(
                        "YouTube did not return video information."
                    )

                original_path = ydl.prepare_filename(info)

                base_path = os.path.splitext(
                    original_path
                )[0]

                wav_path = base_path + ".wav"

            if os.path.exists(wav_path):
                print(
                    f"YouTube audio downloaded: {wav_path}"
                )
                return wav_path

        except Exception as exc:

            last_error = exc

            print(
                f"Format failed: {format_selector}"
            )
            print(exc)

            continue

    raise RuntimeError(
        "Unable to download audio from this YouTube video. "
        "The video may be private, age-restricted, "
        "geo-blocked, unavailable, or YouTube may be "
        "blocking requests from the hosting server. "
        "Please try another public video or use Upload File."
    ) from last_error


def convert_to_wav(input_path: str) -> str:
    """
    Convert any supported audio/video file to WAV.
    """

    output_path = (
        os.path.splitext(input_path)[0]
        + "_converted.wav"
    )

    audio = AudioSegment.from_file(input_path)

    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(16000)

    audio.export(
        output_path,
        format="wav"
    )

    print(
        f"Converted to WAV: {output_path}"
    )

    return output_path


def chunk_audio(
    wav_path: str,
    chunk_minutes: int = 10
) -> list:
    """
    Split WAV audio into chunks.
    """

    audio = AudioSegment.from_wav(wav_path)

    chunk_ms = chunk_minutes * 60 * 1000

    chunks = []

    for i, start in enumerate(
        range(0, len(audio), chunk_ms)
    ):

        chunk = audio[
            start:start + chunk_ms
        ]

        chunk_path = (
            f"{os.path.splitext(wav_path)[0]}"
            f"_chunk_{i}.wav"
        )

        chunk.export(
            chunk_path,
            format="wav"
        )

        chunks.append(chunk_path)

    return chunks


def process_input(source: str) -> list:
    """
    Process either:
    - YouTube URL
    - local uploaded audio/video file
    """

    if not source:
        raise ValueError(
            "No input source provided."
        )

    source = source.strip()

    if (
        source.startswith("http://")
        or source.startswith("https://")
    ):

        print(
            "Detected YouTube URL."
        )

        wav_path = download_youtube_audio(
            source
        )

    else:

        print(
            "Detected local file."
        )

        if not os.path.exists(source):
            raise FileNotFoundError(
                f"File not found: {source}"
            )

        wav_path = convert_to_wav(
            source
        )

    print(
        "Chunking audio..."
    )

    chunks = chunk_audio(
        wav_path
    )

    print(
        f"Audio ready — "
        f"{len(chunks)} chunk(s) created."
    )

    return chunks