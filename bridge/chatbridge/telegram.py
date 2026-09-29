"""telegram.py -- the Telegram adapter: the only module that knows Telegram exists.

Everything else in chatbridge speaks in `Incoming` and `Outgoing` objects, so
a WhatsApp adapter (spec/SPECULATIVE_WHATSAPP_BRIDGE.md, phase 2) replaces
this file and nothing else.

It uses the Bot API over plain HTTPS with long polling (`getUpdates`), so the
bridge needs no public address, no domain and no certificate: anything with
an outbound internet connection can run it. Standard library only.

Telegram does NOT transcribe voice notes for bots. A bot receives the audio
file (Ogg/Opus) and has to transcribe it itself; the speech-to-text some
Telegram apps show is a feature of the app, not something the Bot API hands
over. That is why transcribe.py exists. (Checked against general knowledge of
the Bot API; core.telegram.org was unreachable from the environment that
wrote this, 2026-09-28.)
"""
from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field


@dataclass
class Incoming:
    """One thing a person did in their chat with the bot."""
    kind: str                      # "message" | "callback"
    user_id: int
    chat_id: int
    message_id: int = 0
    private: bool = True
    text: str = ""                 # typed text, or a caption
    voice_file_id: str = ""        # set for voice notes, audio files, video notes
    voice_seconds: int = 0
    voice_filename: str = ""       # what to call the audio for the transcriber
    forwarded: bool = False        # the person is showing someone else's words
    reply_to_message_id: int = 0   # the bot message this one answers, if any
    callback_id: str = ""
    callback_data: str = ""
    first_name: str = ""


@dataclass
class Outgoing:
    chat_id: int
    html: str
    buttons: list = field(default_factory=list)   # rows of (label, callback_data)
    reply_to: int = 0


class TelegramError(RuntimeError):
    pass


class Telegram:
    def __init__(self, token: str, base_url: str = "https://api.telegram.org",
                 timeout: int = 70):
        if not token:
            raise TelegramError("no bot token")
        self.token = token
        self.base = base_url.rstrip("/")
        self.timeout = timeout

    # -- raw calls ---------------------------------------------------------
    def call(self, method: str, **params):
        url = f"{self.base}/bot{self.token}/{method}"
        body = json.dumps({k: v for k, v in params.items() if v is not None}).encode()
        req = urllib.request.Request(url, data=body,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                data = json.loads(e.read().decode())
            except Exception:
                raise TelegramError(f"{method}: HTTP {e.code}") from None
        except urllib.error.URLError as e:
            raise TelegramError(f"{method}: {e.reason}") from None
        except (OSError, http.client.HTTPException, ValueError) as e:
            # A dropped long poll or a proxy's non-JSON page: urllib doesn't
            # wrap errors raised while reading the response.
            raise TelegramError(f"{method}: {type(e).__name__}: {e}") from None
        if not data.get("ok"):
            raise TelegramError(f"{method}: {data.get('description', data)}")
        return data.get("result")

    def download(self, file_id: str) -> bytes:
        info = self.call("getFile", file_id=file_id)
        url = f"{self.base}/file/bot{self.token}/{info['file_path']}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as r:
                return r.read()
        except (OSError, http.client.HTTPException) as e:
            raise TelegramError(f"download: {type(e).__name__}: {e}") from None

    # -- the adapter surface ---------------------------------------------
    def me(self) -> dict:
        return self.call("getMe")

    def poll(self, offset: int, wait: int = 50):
        """-> (next offset, [Incoming]). Updates this adapter does not
        understand still advance the offset, so they are not re-delivered."""
        ups = self.call("getUpdates", offset=offset, timeout=wait,
                        allowed_updates=["message", "callback_query"]) or []
        out = []
        for u in ups:
            offset = max(offset, u["update_id"] + 1)
            inc = parse_update(u)
            if inc is not None:
                out.append(inc)
        return offset, out

    def send(self, o: Outgoing) -> int:
        markup = None
        if o.buttons:
            markup = {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row]
                                          for row in o.buttons]}
        params = dict(chat_id=o.chat_id, text=o.html, parse_mode="HTML",
                      link_preview_options={"is_disabled": True},
                      reply_markup=markup)
        if o.reply_to:
            params["reply_parameters"] = {"message_id": o.reply_to,
                                          "allow_sending_without_reply": True}
        try:
            msg = self.call("sendMessage", **params)
        except TelegramError as e:
            # A formatting feature this client or server rejects must not
            # swallow the reply: fall back to plain text once.
            if "parse" not in str(e).lower() and "entit" not in str(e).lower():
                raise
            params.pop("parse_mode")
            params["text"] = strip_tags(o.html)
            msg = self.call("sendMessage", **params)
        return msg["message_id"]

    def send_plain(self, chat_id: int, text: str) -> int:
        msg = self.call("sendMessage", chat_id=chat_id, text=text,
                        link_preview_options={"is_disabled": True})
        return msg["message_id"]

    def typing(self, chat_id: int):
        try:
            self.call("sendChatAction", chat_id=chat_id, action="typing")
        except TelegramError:
            pass

    def ack(self, callback_id: str, text: str = ""):
        try:
            self.call("answerCallbackQuery", callback_query_id=callback_id,
                      text=text or None)
        except TelegramError:
            pass

    def set_commands(self, commands):
        self.call("setMyCommands",
                  commands=[{"command": c, "description": d} for c, d in commands])


def parse_update(u: dict):
    if "callback_query" in u:
        q = u["callback_query"]
        msg = q.get("message") or {}
        chat = msg.get("chat") or {}
        return Incoming(kind="callback", user_id=q["from"]["id"],
                        chat_id=chat.get("id", q["from"]["id"]),
                        message_id=msg.get("message_id", 0),
                        private=chat.get("type", "private") == "private",
                        callback_id=q["id"], callback_data=q.get("data", ""),
                        first_name=q["from"].get("first_name", ""))
    m = u.get("message")
    if not m or "from" not in m:
        return None
    voice = m.get("voice") or m.get("audio") or m.get("video_note")
    fname = ("voice.ogg" if m.get("voice") else "video.mp4" if m.get("video_note")
             else (m.get("audio") or {}).get("file_name") or "audio.mp3")
    reply = m.get("reply_to_message") or {}
    return Incoming(
        kind="message", user_id=m["from"]["id"], chat_id=m["chat"]["id"],
        message_id=m["message_id"], private=m["chat"].get("type") == "private",
        text=m.get("text") or m.get("caption") or "",
        voice_file_id=(voice or {}).get("file_id", ""),
        voice_seconds=(voice or {}).get("duration", 0),
        voice_filename=fname if voice else "",
        forwarded=bool(m.get("forward_origin") or m.get("forward_date")),
        reply_to_message_id=reply.get("message_id", 0),
        first_name=m["from"].get("first_name", ""))


def strip_tags(html: str) -> str:
    import re
    import html as h
    return h.unescape(re.sub(r"<[^>]+>", "", html))
