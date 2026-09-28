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
  "none"     Voice notes are refused with a sentence saying why.

Claude does not take audio input through the API (per its documentation,
read 2026-09-28), so transcription is always a separate step.
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
