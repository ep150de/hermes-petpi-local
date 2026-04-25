"""Configuration for local-only hermes-petpi (no external APIs)."""

import os
from dotenv import load_dotenv
load_dotenv()

# ── Local LLM Backend ─────────────────────────────────────────────────────────

# Choose backend: "hermes" | "ollama" | "llamacpp"
LOCAL_BACKEND = os.environ.get("LOCAL_BACKEND", "hermes").lower()

# Hermes Agent local URL (if backend=="hermes")
HERMES_LOCAL_URL = os.environ.get("HERMES_LOCAL_URL", "http://localhost:8000")
HERMES_LOCAL_TOKEN = os.environ.get("HERMES_LOCAL_TOKEN", "")

# Ollama settings (if backend=="ollama")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

# llama.cpp server (if backend=="llamacpp")
LLAMACPP_URL = os.environ.get("LLAMACPP_URL", "http://localhost:8080")

# System prompt — same intent, shorter to reduce local compute
LOCAL_SYSTEM_PROMPT = os.environ.get(
    "LOCAL_SYSTEM_PROMPT",
    "You are Hermes, a helpful voice assistant. Keep responses brief (2 sentences)."
)
CONVERSATION_HISTORY_LENGTH = int(os.environ.get("CONVERSATION_HISTORY_LENGTH", "5"))

# ── Local Speech ──────────────────────────────────────────────────────────────

# Whisper.cpp binary path (relative to project dir)
WHISPER_CPP_BIN = os.environ.get("WHISPER_CPP_BIN", "./bin/whisper-cli")
WHISPER_CPP_MODEL = os.environ.get("WHISPER_CPP_MODEL", "models/ggml-base.bin")

# Piper TTS binary path
PIPER_BIN = os.environ.get("PIPER_BIN", "./bin/piper")
PIPER_MODEL = os.environ.get("PIPER_MODEL", "models/en_US-amy-medium.onnx")

# Enable offline STT/TTS
ENABLE_OFFLINE_STT = os.environ.get("ENABLE_OFFLINE_STT", "true").lower() in ("true", "1", "yes")
ENABLE_OFFLINE_TTS = os.environ.get("ENABLE_OFFLINE_TTS", "true").lower() in ("true", "1", "yes")

# ── Audio ─────────────────────────────────────────────────────────────────────

AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE", "plughw:1,0")
AUDIO_OUTPUT_DEVICE = os.environ.get("AUDIO_OUTPUT_DEVICE", "default")
AUDIO_SAMPLE_RATE = int(os.environ.get("AUDIO_SAMPLE_RATE", "16000"))

# ── Display ────────────────────────────────────────────────────────────────────

LCD_BACKLIGHT = int(os.environ.get("LCD_BACKLIGHT", "70"))
UI_MAX_FPS = int(os.environ.get("UI_MAX_FPS", "4"))
RESPONSE_HOLD_TIMEOUT = int(os.environ.get("RESPONSE_HOLD_TIMEOUT", "30"))
SLEEP_TIMEOUT = int(os.environ.get("SLEEP_TIMEOUT", "60"))

PET_THEME = os.environ.get("PET_THEME", "hermes-messenger").lower()
PET_COLOR_PRIMARY = tuple(int(x) for x in os.environ.get("PET_COLOR_PRIMARY", "200,130,50").split(","))
PET_COLOR_ACCENT = tuple(int(x) for x in os.environ.get("PET_COLOR_ACCENT", "0,150,255").split(","))

# ── Logging ───────────────────────────────────────────────────────────────────

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.environ.get("LOG_FILE", "/tmp/hermes-petpi.log")


def print_config():
    print(f"LOCAL_BACKEND          = {LOCAL_BACKEND}")
    print(f"HERMES_LOCAL_URL       = {HERMES_LOCAL_URL}")
    print(f"OLLAMA_URL             = {OLLAMA_URL}")
    print(f"OLLAMA_MODEL           = {OLLAMA_MODEL}")
    print(f"ENABLE_OFFLINE_STT     = {ENABLE_OFFLINE_STT}")
    print(f"ENABLE_OFFLINE_TTS     = {ENABLE_OFFLINE_TTS}")
    print(f"WHISPER_CPP_BIN        = {WHISPER_CPP_BIN}")
    print(f"PIPER_BIN              = {PIPER_BIN}")
    print(f"PET_THEME              = {PET_THEME}")
