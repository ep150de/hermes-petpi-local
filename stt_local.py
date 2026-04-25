"""Local speech-to-text using whisper.cpp."""

import subprocess
import json
import os
import tempfile
import config_local as config

WAV_PATH = "/tmp/utterance.wav"


def transcribe(wav_path: str) -> str:
    """Run whisper.cpp CLI to transcribe WAV file."""
    if not config.ENABLE_OFFLINE_STT:
        raise RuntimeError("Offline STT disabled")

    if not os.path.exists(config.WHISPER_CPP_BIN):
        raise FileNotFoundError(f"whisper.cpp binary not found: {config.WHISPER_CPP_BIN}")

    cmd = [
        config.WHISPER_CPP_BIN,
        "-m", config.WHISPER_CPP_MODEL,
        "-f", wav_path,
        "-otxt",  # output to stdout as text
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"whisper.cpp failed: {result.stderr[:200]}")
        transcript = result.stdout.strip()
        print(f"[stt] local whisper result: {transcript[:120]}")
        return transcript
    except subprocess.TimeoutExpired:
        raise RuntimeError("whisper.cpp transcription timed out")


def check_health() -> bool:
    return os.path.exists(config.WHISPER_CPP_BIN)
