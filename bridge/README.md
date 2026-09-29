# Chat Bridge — Telegram Access to a Repository, Content Only

**A Telegram bot that is a narrow front door to Claude Code working on a
repository.** You send a voice note or a message; Claude does the work in the
repository; you get back a few sentences, a link, and a **More** button for
the full answer.

**Status: a test build.** It runs inside a Claude Code cloud session
([cloud_start.sh](cloud_start.sh)) or on any always-on computer, and
uses long polling, so it needs no server of its own, domain or certificate. The thinking behind it, and what a
hosted version would add, is in
[spec/SPECULATIVE_TELEGRAM_ACCESS.md](../spec/SPECULATIVE_TELEGRAM_ACCESS.md).
**To set it up, follow [SETUP.md](SETUP.md).**

## The Rule It Exists to Keep

**Instructions that arrive through chat are limited to content, for
everyone, the repository's owner included.** Content is documents, notes,
decisions and lists: files with a content extension (`.md`, `.txt`, `.csv`
and so on) outside the repository's machinery. Machinery is everything
listed below, and it can never be changed from chat, whatever the message
says or whoever sends it. The owner has a normal session for that.

Machinery is read from the same places GitHub enforces from, so the bridge
and branch protection cannot disagree about a path:

1. a built-in floor: `.github/`, `.claude/`, `tools/`, `practices/`,
   `local/`, `templates/`, `precedent.json`, the AGENTS and CLAUDE instruction files, any
   `CODEOWNERS`, and any hidden file or folder;
2. `owned_paths` in the repository's `precedent.json`;
3. every pattern in the repository's `CODEOWNERS`, whoever owns it;
4. `extra_owned_paths` in the bridge's configuration.

A `CODEOWNERS` pattern the bridge can't read makes it refuse every write,
and it says so. To see how the bridge would treat a path:
`python3 bridge/run.py scope --repo notes docs/plan.md tools/x.py`.

## Three Locks, and Which One Holds

1. **The tool set.** Each turn runs `claude -p` with file tools only
   (`--tools`), the rest listed as disallowed, no Model Context Protocol (MCP) servers, and
   `--restricted` where the installed Claude Code has it. Restricted mode
   removes every command-running tool, keeps file tools inside the checkout,
   and ignores user and project settings files, so neither the owner's broad
   permissions nor a repository's hooks widen a chat turn.
2. **The guard** ([chatbridge/guard.py](chatbridge/guard.py)), a PreToolUse
   hook. It denies reads outside the checkout and writes to anything but
   content, and tells the model why, so it can tell the person.
3. **The bridge's own check after the turn.** The model has no shell and no
   git, so nothing is committed except by the bridge. It lists every changed
   path and commits only if **all** of them are content. Otherwise the
   changes are set aside with `git stash` (kept, never deleted), nothing is
   saved, and the reply opens with what was refused. **This is the boundary**:
   it doesn't depend on the model behaving or on a hook firing.

For anyone but the owner on a real project, add a fourth: branch protection
with code-owner review, so GitHub refuses machinery changes too
([SETUP.md](SETUP.md#adding-another-person-later)).

## What Happens to a Message

1. **Only private chats, only invited people.** Anyone else gets one line
   saying the bot is private. Group chats are ignored.
2. **Batching.** Messages that arrive within a few seconds of each other
   (`batch_seconds`) become one turn.
3. **Voice notes are transcribed.** Telegram hands a bot the audio, not the
   words. What was heard is attached to the reply as a collapsed quote.
4. **Forwarded messages are material, not instructions.** They reach the
   model marked `FORWARDED`.
5. **Which repository.** The one the replied-to message came from, else the
   person's current one (`/repos` to switch). People with more than one
   repository see its name at the top of each reply.
6. **The turn.** The bridge refreshes its own checkout (one per person per
   repository, on the branch `chat/<handle>`), then runs one Claude Code
   turn. The conversation resumes across messages; `/new` starts fresh.
7. **The check** described above, then commit and push of `chat/<handle>`.
8. **The reply**: at most a few sentences (`max_sentences`, cut hard at
   `max_chars`), a link to the change, and the buttons **More** and **Land
   it**. The model is asked for a `<telegram>` summary alongside its full
   answer, and the bridge enforces the length. If something failed or was
   refused, the reply's first words say so, and the model's own summary is
   dropped, since it may describe work the bridge then refused.
9. **Landing.** Saying or typing *Go update* (also *approved*, *land it*),
   `/land`, or the button merges the latest landing branch into
   `chat/<handle>`, checks every file is content, pushes to the landing
   branch without forcing, and confirms GitHub shows it.

## Commands

| Command | Does |
|---|---|
| `/repos` | Shows the current repository; buttons to switch |
| `/land` | Lands your changes, same as saying *Go update* |
| `/status` | How many changes haven't landed, with a compare link |
| `/new` | Starts a fresh conversation in this repository |
| `/help` | One paragraph on what the bot does |

## Transcription

Set in the configuration's `transcription` block:

- `"backend": "whisper-local"`: an open-source Whisper model run by
  `faster-whisper` on the bridge's own machine; this is the cloud setup's
  default. No key and no third party, and the audio stays where Claude is
  working. `model` is `small` by default (`base` is faster, `medium` more
  accurate), and `language` saves it guessing. The model downloads from
  Hugging Face the first time on each machine.
- `"backend": "openai"`: any OpenAI-compatible `/audio/transcriptions`
  endpoint (`base_url`, `model`, key in the environment variable named by
  `api_key_env`). Takes Telegram's Ogg voice notes as they come.
- `"backend": "command"`: a local program that prints the transcript, for
  example `"argv": ["/usr/local/bin/transcribe-ogg", "{input}"]`. If your
  Whisper build only reads Waveform Audio File Format (WAV) files, wrap it in a small script that converts with
  `ffmpeg` first.
- `"backend": "none"`: voice notes are refused with a sentence saying why.

**Claude can't listen to audio.** Its API takes no audio input, and Claude
Code's file tools read text, images and PDFs, not sound. So transcription is
always a separate step, and running it beside Claude is the nearest thing to
handing Claude the recording.

## Where Things Live

| What | Where |
|---|---|
| Configuration | `~/.config/chatbridge/config.json` (template: [config.example.json](config.example.json)) |
| Bot token, transcription key | Environment variables, never a file in a repository |
| Who is bound to what, invites, session identifiers | `~/.local/state/chatbridge/state.json` |
| Full answers (the More button) | `~/.local/state/chatbridge/answers/` |
| The bridge's checkouts | `~/.local/state/chatbridge/checkouts/<repo>/<handle>` |

**Telegram identifiers never enter a repository**; commits carry the
person's handle only.

## Known Limits of This Build

- **It runs only while its machine does.** In a cloud session that's until
  the session's machine is reclaimed, and each new machine starts with empty
  state: new invite (unless `telegram_user_id` is configured), fresh
  conversation, and no earlier More answers. Changes are on GitHub and
  survive. A hosted, always-on version is phase 2 of the spec.
- **The full answer lives on the bridge's machine**, behind the More button,
  not on GitHub. Links to changes point at GitHub, and on a private
  repository they only open for someone logged in with access.
- **Collapsed quotes** (`<blockquote expandable>`) are a newer Telegram
  formatting feature. If Telegram rejects a message's formatting, the bridge
  resends it as plain text.
- **No WhatsApp yet.** [chatbridge/telegram.py](chatbridge/telegram.py) is
  the only module that knows about Telegram, so a WhatsApp adapter replaces
  that one file.
- **The reply rules of a normal Precedent session** (The Boildown, the
  archive line) don't apply to a phone-sized reply. Restricted mode doesn't
  load the repository's hooks, so nothing demands them. If the bridge
  graduates, a practice should say how reply shape follows the surface.

## Tests

```sh
python3 -m unittest discover -s bridge/tests
```

Not for pasting: this is the command a contributor runs from the top of the
checkout.

The suite runs the whole loop against a fake Telegram server, a fake
`claude` and a local git origin: invites, a content change, a refused
machinery change from the owner, a voice note, a forwarded message, the More
button, and landing. It uses no network and no model.
