"""shaper.py -- turn a full answer into a phone-sized reply.

The model is asked for a <telegram>...</telegram> summary. The bridge does not
trust it to be short: it strips markdown, cuts at a sentence boundary under
`max_chars`, and falls back to the full answer's opening when the tag is
missing. The full answer is never lost -- it is saved, and the reply carries
a "More" button that sends it.
"""
from __future__ import annotations

import html
import re

_TAG = re.compile(r"<telegram>(.*?)</telegram>", re.S | re.I)


def summary(full: str, max_chars: int = 450) -> str:
    m = _TAG.findall(full or "")
    text = m[-1] if m else _TAG.sub("", full or "")
    text = _plain(text)
    return clip(text, max_chars) if text else "Done."


def without_tag(full: str) -> str:
    return _TAG.sub("", full or "").strip()


def _plain(md: str) -> str:
    t = re.sub(r"```.*?```", " ", md, flags=re.S)
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", t)
    t = t.replace("**", "").replace("__", "").replace("`", "")
    return re.sub(r"\s+", " ", t).strip()


def clip(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", cut)]
    if ends and ends[-1] > max_chars // 3:
        return cut[:ends[-1]].strip()
    return cut.rsplit(" ", 1)[0].rstrip(",;:") + "…"


def render(*, text, repo_tag=None, links=(), heard=None) -> str:
    """-> Telegram HTML. `links` is a list of (label, url)."""
    parts = []
    if repo_tag:
        parts.append(f"<i>[{html.escape(repo_tag, quote=False)}]</i>")
    parts.append(html.escape(text, quote=False))
    ls = [f'<a href="{html.escape(u, quote=True)}">{html.escape(l, quote=False)}</a>'
          for l, u in links if u]
    if ls:
        parts.append(" · ".join(ls))
    out = "\n".join(parts)
    if heard:
        out += "\n<blockquote expandable>Heard: " + html.escape(clip(heard, 900), quote=False) + "</blockquote>"
    return out


def chunks(text: str, size: int = 3900):
    """Split a long answer for Telegram's per-message limit, on line breaks."""
    out, cur = [], ""
    for line in (text or "").splitlines(keepends=True):
        while len(line) > size:
            if cur:
                out.append(cur)
                cur = ""
            out.append(line[:size])
            line = line[size:]
        if len(cur) + len(line) > size:
            out.append(cur)
            cur = ""
        cur += line
    if cur.strip():
        out.append(cur)
    return out or ["(empty)"]
