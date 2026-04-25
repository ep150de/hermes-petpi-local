"""Local text-to-speech using Piper TTS."""

import subprocess
import queue
import threading
import os
import tempfile
import wave
import struct
import time
import config_local as config

_SENTINEL = object()

# RMS mouth-shape thresholds for piper-generated PCM (16-bit)
_RMS_THRESHOLDS = [500, 2000, 6000]


class TTSPlayer:
    """Pre-fetch pipeline for piper-tts with RMS mouth-sync."""

    def __init__(self):
        self._submit_q: queue.Queue[str | object] = queue.Queue()
        self._play_q: queue.Queue[tuple[str, bytes, list[int]] | object] = queue.Queue(maxsize=2)
        self._cancel = threading.Event()
        self._done = threading.Event()

        self._full_text = ""
        self._mouth_timeline: list[int] = []
        self._playback_start = 0.0
        self._playback_duration = 0.0
        self.is_speaking = threading.Event()
        self._play_proc: subprocess.Popen | None = None

        self._fetcher = threading.Thread(target=self._fetch_loop, daemon=True)
        self._player = threading.Thread(target=self._play_loop, daemon=True)
        self._fetcher.start()
        self._player.start()

    @property
    def current_text(self) -> str:
        if not self.is_speaking.is_set() or self._playback_duration <= 0:
            return ""
        words = self._full_text.split()
        if not words:
            return ""
        elapsed = time.monotonic() - self._playback_start - 0.25
        if elapsed < 0:
            return ""
        progress = min(1.0, elapsed / self._playback_duration)
        idx = min(int(progress * len(words)), len(words) - 1)
        end = idx + 1
        start = max(0, end - 4)
        return " ".join(words[start:end])

    def get_mouth_shape(self) -> int:
        if not self.is_speaking.is_set() or not self._mouth_timeline:
            return -1
        elapsed = time.monotonic() - self._playback_start
        frame_idx = int(elapsed * 1000 / 80)
        if 0 <= frame_idx < len(self._mouth_timeline):
            return self._mouth_timeline[frame_idx]
        return -1

    def submit(self, text: str) -> None:
        t = (text or "").strip()
        if not t:
            return
        self._submit_q.put(t)

    def flush(self) -> None:
        self._done.clear()
        self._submit_q.put(_SENTINEL)
        self._done.wait(timeout=60)

    def cancel(self) -> None:
        self._cancel.set()
        if self._play_proc:
            try:
                self._play_proc.kill()
            except Exception:
                pass
        self._submit_q.put(_SENTINEL)

    # ── Fetcher ──────────────────────────────────────────────────────────────────

    def _fetch_loop(self):
        while not self._cancel.is_set():
            text = self._submit_q.get()
            if text is _SENTINEL:
                self._submit_q.put(_SENTINEL)
                break
            self._fetch_and_enqueue(text)

    def _fetch_and_enqueue(self, text: str):
        if not config.ENABLE_OFFLINE_TTS:
            return

        # Piper generates WAV to stdout
        try:
            cmd = [
                config.PIPER_BIN,
                "--model", config.PIPER_MODEL,
                "--output-raw",
            ]
            proc = subprocess.Popen(
                cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            wav_raw, stderr = proc.communicate(input=text.encode("utf-8"), timeout=15)
            if proc.returncode != 0:
                print(f"[tts] piper error: {stderr.decode()[:200]}")
                return

            # Convert raw PCM (24kHz s16le) to WAV + compute RMS timeline
            wav_bytes = self._raw_to_wav(wav_raw)
            timeline = self._compute_mouth_timeline(wav_raw)
            self._play_q.put((text, wav_bytes, timeline))
        except Exception as e:
            print(f"[tts] fetch error: {e}")

    def _raw_to_wav(self, raw_pcm: bytes, sample_rate: int = 24000) -> bytes:
        """Wrap 16-bit little-endian PCM in a WAV header."""
        import io, wave
        out = io.BytesIO()
        with wave.open(out, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(raw_pcm)
        return out.getvalue()

    def _compute_mouth_timeline(self, pcm_raw: bytes, window_ms: int = 80) -> list[int]:
        samples = struct.unpack(f"<{len(pcm_raw)//2}h", pcm_raw)
        rate = 24000
        spw = int(rate * window_ms / 1000)
        n = max(1, len(samples) // spw)
        timeline = []
        for i in range(n):
            start = i * spw
            end = min(start + spw, len(samples))
            window = samples[start:end]
            rms = (sum(s * s for s in window) / len(window)) ** 0.5 if window else 0
            if rms < _RMS_THRESHOLDS[0]:
                shape = 0
            elif rms < _RMS_THRESHOLDS[1]:
                shape = 1
            elif rms < _RMS_THRESHOLDS[2]:
                shape = 2
            else:
                shape = 3
            timeline.append(shape)
        return timeline

    # ── Player ───────────────────────────────────────────────────────────────────

    def _play_loop(self):
        while not self._cancel.is_set():
            item = self._play_q.get()
            if item is _SENTINEL:
                self._play_q.put(_SENTINEL)
                break

            text, wav_bytes, timeline = item
            self._full_text = text
            self._mouth_timeline = timeline

            try:
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(wav_bytes)
                    path = f.name
                self._play_proc = subprocess.Popen(
                    ["aplay", "-D", config.AUDIO_OUTPUT_DEVICE, "-r", "24000", "-f", "S16_LE", "-c", "1", path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                self._playback_start = time.monotonic()
                self._playback_duration = len(timeline) * 0.08
                self.is_speaking.set()
                self._play_proc.wait()
                self.is_speaking.clear()
                os.unlink(path)
                self._playback_duration = 0.0
            except Exception as e:
                print(f"[tts] playback error: {e}")
                self.is_speaking.clear()

        self._done.set()
