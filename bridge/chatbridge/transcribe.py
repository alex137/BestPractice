"""transcribe.py -- voice note to text. Telegram hands a bot the audio, not words.

Three backends, picked in the configuration's "transcription" block:

  "openai"   Any OpenAI-compatible /audio/transcriptions endpoint: OpenAI
             itself, or another provider exposing the same interface at a
             different base_url. Needs an API key in an environment variable.
             Accepts Telegram's Ogg/Opus voice notes as they arrive.
  "command"  Any local program that prints the transcript on stdout, given
             the audio file's path -- a local Whisper build, for instance.
             Nothing leaves the machine. argv is a list with "{input}" where
             the path goes.
  "whisper-local"
             An open-source Whisper model run by faster-whisper on the
             machine the bridge runs on. No key, no third party: in a cloud
             session the audio stays in the container Claude works in.
  "none"     Voice notes are refused with a sentence saying why.

Claude cannot listen to audio: the API takes no audio input (per its
documentation, read 2026-09-28), and Claude Code's file tools read text,
images and PDFs, not sound. So transcription is always a separate step;
"whisper-local" is the nearest thing to handing the audio to Claude, since
it runs beside it.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
import uuid


class TranscriptionError(RuntimeError):
    pass


class NoTranscriber:
    available = False

    def transcribe(self, audio: bytes, filename: str = "voice.ogg") -> str:
        raise TranscriptionError(
            "voice notes aren't set up on this bridge yet (no transcription backend)")


class OpenAICompatible:
    available = True

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1",
                 model: str = "whisper-1", language: str | None = None,
                 prompt: str | None = None, timeout: int = 120):
        if not api_key:
            raise TranscriptionError("transcription API key is not set")
        self.key, self.base, self.model = api_key, base_url.rstrip("/"), model
        self.language, self.prompt, self.timeout = language, prompt, timeout

    def transcribe(self, audio: bytes, filename: str = "voice.ogg") -> str:
        fields = {"model": self.model, "response_format": "json"}
        if self.language:
            fields["language"] = self.language
        if self.prompt:
            fields["prompt"] = self.prompt
        body, ctype = _multipart(fields, "file", filename, audio)
        req = urllib.request.Request(f"{self.base}/audio/transcriptions", data=body,
                                     headers={"Content-Type": ctype,
                                              "Authorization": f"Bearer {self.key}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise TranscriptionError(f"transcription failed: HTTP {e.code} "
                                     f"{e.read()[:200]!r}") from None
        except urllib.error.URLError as e:
            raise TranscriptionError(f"transcription failed: {e.reason}") from None
        return (data.get("text") or "").strip()


class Command:
    available = True

    def __init__(self, argv, timeout: int = 300):
        if not argv or not any("{input}" in a for a in argv):
            raise TranscriptionError('"command" needs an argv list containing "{input}"')
        self.argv, self.timeout = list(argv), timeout

    def transcribe(self, audio: bytes, filename: str = "voice.ogg") -> str:
        suffix = os.path.splitext(filename)[1] or ".ogg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio)
            path = f.name
        try:
            argv = [a.replace("{input}", path) for a in self.argv]
            r = subprocess.run(argv, capture_output=True, text=True, timeout=self.timeout)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise TranscriptionError(f"transcription command failed: {e}") from None
        finally:
            os.unlink(path)
        if r.returncode != 0:
            raise TranscriptionError(f"transcription command exited {r.returncode}: "
                                     f"{r.stderr.strip()[:200]}")
        return r.stdout.strip()


class WhisperLocal:
    """An open-source Whisper model run on this machine by faster-whisper.
    The audio never leaves the machine the bridge runs on -- in a cloud
    session, the same container Claude works in. The model downloads from
    Hugging Face on first use, so that host has to be reachable once."""
    available = True

    def __init__(self, model="small", language=None, compute_type="int8",
                 download_root=None):
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            raise TranscriptionError(
                "the whisper-local backend needs faster-whisper: "
                "pip install faster-whisper") from None
        self.model_name, self.language = model, language
        self.compute_type, self.download_root = compute_type, download_root
        self._model = None

    def load(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            try:
                self._model = WhisperModel(self.model_name, device="cpu",
                                           compute_type=self.compute_type,
                                           download_root=self.download_root)
            except Exception as e:
                raise TranscriptionError(
                    f"couldn't load the Whisper model '{self.model_name}' ({e}). "
                    "If this is a download failure, allow huggingface.co -- and any "
                    "host `check` lists as refused -- in the network settings") from None
        return self._model

    def transcribe(self, audio: bytes, filename: str = "voice.ogg") -> str:
        model = self.load()
        suffix = os.path.splitext(filename)[1] or ".ogg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio)
            path = f.name
        try:
            segments, _info = model.transcribe(path, language=self.language,
                                               vad_filter=True)
            return " ".join(s.text.strip() for s in segments).strip()
        except Exception as e:
            raise TranscriptionError(f"transcription failed: {e}") from None
        finally:
            os.unlink(path)


def from_config(cfg: dict):
    backend = (cfg or {}).get("backend", "none")
    if backend == "none":
        return NoTranscriber()
    if backend == "openai":
        return OpenAICompatible(
            api_key=os.environ.get(cfg.get("api_key_env", "OPENAI_API_KEY"), ""),
            base_url=cfg.get("base_url", "https://api.openai.com/v1"),
            model=cfg.get("model", "whisper-1"), language=cfg.get("language"),
            prompt=cfg.get("prompt"))
    if backend == "command":
        return Command(cfg.get("argv"), timeout=cfg.get("timeout_seconds", 300))
    if backend == "whisper-local":
        return WhisperLocal(model=cfg.get("model", "small"), language=cfg.get("language"),
                            compute_type=cfg.get("compute_type", "int8"),
                            download_root=cfg.get("download_root"))
    raise TranscriptionError(f"unknown transcription backend {backend!r}")


def _multipart(fields: dict, file_field: str, filename: str, data: bytes):
    boundary = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\""
                f"\r\n\r\n{v}\r\n").encode()
    out += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
            f"filename=\"{filename}\"\r\nContent-Type: application/octet-stream"
            f"\r\n\r\n").encode()
    out += data + f"\r\n--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"
