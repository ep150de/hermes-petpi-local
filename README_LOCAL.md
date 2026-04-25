# hermes-petpi — Local-Only Mode (no API keys)

A fully offline variant of hermes-petpi that uses local LLM inference, local speech recognition, and local text-to-speech — **zero external API calls**.

**Perfect for:** privacy-conscious users, air-gapped systems, or anyone who wants a completely self-contained voice assistant.

## Hardware

Same as hermes-petpi:
- Raspberry Pi Zero 2 W / Pi Zero W
- PiSugar WhisPlay board (1.54" LCD, button, speaker, mic)

## Software Stack (100% Local)

| Component | Tool | Install |
|-----------|------|---------|
| **LLM Backend** | Hermes Agent / Ollama / llama.cpp | [See below](#local-llm-backends) |
| **Speech-to-Text** | whisper.cpp | `./install-whisper.sh` |
| **Text-to-Speech** | piper-tts | `./install-piper.sh` |
| **Audio** | ALSA arecord/aplay | preinstalled |
| **Speech** | Local only | No internet required |

## Quick Start (Fully Offline)

### 1. Install Local LLM Backend

Choose one:

**Option A: Hermes Agent (local mode)**
```bash
# If you already run Hermes Agent locally
git clone https://github.com/hermes-agent/hermes-agent.git
cd hermes-agent
# Follow setup — ensure it listens on http://localhost:8000
```

**Option B: Ollama** (simpler)
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b  # or any model that fits Pi Zero (small ones!)
```

**Option C: llama.cpp server**
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make server
./server -m models/phi-2.Q4_K_M.gguf --port 8080
```

### 2. Build Local Speech Binaries

```bash
# From the hermes-petpi-local directory:
./install-deps.sh       # install system packages (portaudio19-dev, etc.)
./download-models.sh    # fetch whisper & piper model files (~300MB)
./build-whisper.sh      # compile whisper.cpp
./build-piper.sh        # compile piper
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env:
#   LOCAL_BACKEND="hermes" | "ollama" | "llamacpp"
#   Set LOCAL_URL accordingly
```

### 4. Run

```bash
python3 main_local.py
```

---

## Local LLM Backends

### Hermes Agent (local)

If you already run Hermes Agent locally, hermes-petpi-local connect via HTTP:

```bash
# .env
LOCAL_BACKEND=hermes
HERMES_LOCAL_URL=http://localhost:8000
```

No additional setup needed — the Hermes Agent handles streaming just like the cloud version.

### Ollama

Ollama runs a simple REST API and manages models for you.

```bash
# Install & pull a model:
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b   # ~2GB, may be tight on Pi Zero
ollama pull phi:mini      # smaller, ~1.5GB, decent quality

# .env
LOCAL_BACKEND=ollama
OLLAMA_MODEL=phi:mini
OLLAMA_URL=http://localhost:11434
```

The first run downloads the model; subsequent runs are instant.

Note: Pi Zero's 512 MB RAM limits model size. Use **Q4 quantized 1-3B parameter models** only. Consider offloading to a more powerful machine on your network.

### llama.cpp Server

Minimal server for GGUF models — most flexible and efficient.

```bash
# Build llama.cpp (on Pi or cross-compile)
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp && make server

# Download a small model (phi-2, TinyLlama)
wget https://huggingface.co/second-state/Phi-2-GGUF/resolve/main/phi-2.Q4_K_M.gguf

# Run server:
./server -m phi-2.Q4_K_M.gguf --port 8080 --ctx-size 1024

# .env
LOCAL_BACKEND=llamacpp
LLAMACPP_URL=http://localhost:8080
```

---

## Local Speech (Whisper.cpp + Piper)

### Why separate binaries?
- whisper.cpp: optimized C implementation, ~10MB binary, ~200MB model
- piper: neural TTS, fast inference, ~100MB model + binary

### Install scripts

```bash
# 1. System deps
sudo apt install -y portaudio19-dev libsndfile1-dev cmake build-essential

# 2. whisper.cpp
./install-whisper.sh   # clones, builds, and downloads base model (~300MB)

# 3. piper-tts
./install-piper.sh     # clones, builds, downloads en_US-amy-medium model (~200MB)
```

Both install into `./bin/` (committed to `.gitignore`).

### Model options

**Whisper:**
- `ggml-base.bin` (300 MB) — decent accuracy, fastest
- `ggml-small.bin` (500 MB) — better, slower
- `ggml-medium.bin` (2 GB) — high quality, very slow on Pi Zero

**Piper:**
- `en_US-amy-medium.onnx` (200 MB) — clear, natural
- `en_US-amy-low.onnx` (50 MB) — compact, robotic

Change paths in `.env` if you store models elsewhere.

---

## Configuration Reference

| Variable | Values | Description |
|---|---|---|
| `LOCAL_BACKEND` | `hermes` / `ollama` / `llamacpp` | LLM provider |
| `HERMES_LOCAL_URL` | `http://host:port` | Hermes Agent endpoint |
| `OLLAMA_URL` | `http://host:port` | Ollama API |
| `OLLAMA_MODEL` | model tag | e.g. `phi:mini` |
| `LLAMACPP_URL` | `http://host:port` | llama.cpp server |
| `ENABLE_OFFLINE_STT` | `true` / `false` | Use whisper.cpp? |
| `ENABLE_OFFLINE_TTS` | `true` / `false` | Use piper? |
| `PET_THEME` | `hermes-messenger` etc | Pet sprite |

All other settings (display, audio, pet) are shared with the online variant.

---

## Performance Notes

| Metric | Pi Zero 2 W | Pi 4 / Desktop |
|--------|-------------|----------------|
| Whisper transcribe | ~2-4 s (base model) | <1 s |
| TTS synthesis | ~0.5-1 s per sentence | <0.3 s |
| LLM first token | 3-10 s (small model) | 0.5-2 s |
| Total latency (press→reply) | 5-15 s typical | 2-5 s |

**Pi Zero limitations:**
- CPU-only inference — keep models small (≤3B params, Q4 quantized)
- 512 MB RAM shared — swap may be used
- Not suitable for large context (>1024 tokens)

**Recommendation:** Use Phi-2 or TinyLlama (2-3B) via llama.cpp server for best quality/speed tradeoff.

---

## Differences from Online Variant

| Feature | Online (hermes-petpi) | Local (hermes-petpi-local) |
|---------|---------------------|---------------------------|
| OpenAI Whisper API | ✅ Cloud | **❌ whisper.cpp binary** |
| OpenAI TTS API | ✅ Cloud | **❌ piper-tts binary** |
| LLM | Hermes Agent (cloud or local) | **Local-only** (Hermes/Ollama/llama.cpp) |
| Network required | ✅ Yes (for APIs) | **❌ Optional** (only if using remote LLM) |
| Model updates | Automatic (via API) | Manual (download GGUF/ONNX) |
| Privacy | Data leaves device | **All on-device** |
| Disk space | ~100 MB | ~1 GB (models) |
| First-time setup | 5 min | 30-60 min (compile + download) |

---

## Troubleshooting

### whisper.cpp: "illegal instruction"
Your model is compiled for a newer CPU. Re-compile with `CMAKE_ARGS="-DGGML_NATIVE=OFF"` or use a more compatible model.

### piper: audio garbled or too quiet
Adjust `amixer` gain or set `PIPER_AUDIO_GAIN` in config (future addition).

### LLM too slow / hangs
- Use a smaller model (phi-2 > TinyLlama > llama3.2:3b)
- Reduce `max_tokens` in `local_client.py`
- Consider running LLM on another machine (set `LOCAL_BACKEND=hermes` with remote Hermes URL)

### Out of memory
Pi Zero has 512 MB RAM. Swap is your friend:
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # set CONF_SWAPSIZE=2048 (2GB swap)
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

---

## Roadmap

- [ ] Bundle pre-compiled binaries for Pi Zero (no compile needed)
- [ ] Add Coqui TTS as alternative to piper
- [ ] Support whisper-faster (faster-whisper) for GPU-like speed
- [ ] Offline Hermes Agent Docker image
- [ ] Model downloader with checksum verification

---

## License

MIT — same as parent project.

## Acknowledgments

- [ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp) — offline Whisper
- [rhasspy/piper](https://github.com/rhasspy/piper) — neural TTS
- Local LLM community (Ollama, llama.cpp)

---

**Fully offline. Fully Hermes. Fully yours.**
