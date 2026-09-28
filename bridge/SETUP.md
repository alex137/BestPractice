# Setting up the chat bridge — what you do

This gets the Telegram bridge running on **your own computer**, for **you
alone**, against **one test repository**. Adding another person later is the
last section. How it works and why is in [README.md](README.md).

**Budget about an hour the first time.** Most of it is steps 2 and 3, and
they are one-offs.

## 1. Pick the repository to test on

**Use a throwaway private repository first**, not a real project: one with a
README file and nothing else is enough. You can point the bridge at a real
repository once you trust it.

Note its clone address (for example `https://github.com/you/chat-test.git`, or
the SSH form GitHub's green Code button shows), its web address, and its main branch — usually `main`. That branch is where "Go
update" lands your changes.

## 2. Check your computer has what it needs

| Needed | How to check |
|---|---|
| **Python 3.9 or newer** | `python3 --version` |
| **Claude Code, logged in** | `claude -p "say ok"` prints ok. The bridge uses this login, so chat turns count against your Claude plan |
| **git that can push to the test repository without a password prompt** | `git ls-remote https://github.com/you/chat-test.git` (or your SSH address) prints branch names |
| **This code** | `git clone https://github.com/alex137/BestPractice` then `git checkout claude/telegram-access-brainstorm-7f10il` — it lives on that branch until it is landed |

The computer has to be **on and awake** while you use the bridge. On a Mac,
start the bridge with `caffeinate -i` in front (step 7) so it doesn't sleep.

## 3. Create the bot and get two keys

**The Telegram bot**, about 2 minutes:

1. In Telegram, open a chat with **@BotFather** (check for the blue tick).
2. Send `/newbot`. Give it a display name, then a username ending in `bot`
   (for example `morgan_notes_bot`).
3. BotFather replies with a **token**, a long string with a colon in it.
   **Treat it like a password.**
4. Optional but sensible: send `/setjoingroups`, pick your bot, and choose
   **Disable**, so nobody can add it to a group.

**Telegram does not transcribe voice notes for bots.** A bot gets the audio
file, not the words. The speech-to-text some Telegram apps show is a feature
of the app, not something the Bot API passes on. (This is from general
knowledge of the Bot API. Telegram's own documentation site is blocked from
the environment that built this, 2026-09-28.) So the bridge needs a
transcription service:

- **Simplest: an OpenAI API key.** Create one at platform.openai.com → API
  keys, with billing enabled. Voice notes are sent to OpenAI for
  transcription. It costs cents per hour of audio.
- **Private: a local Whisper program** that prints the transcript. Nothing
  leaves your computer. Set `"backend": "command"` and give its command line
  as `argv`, with `"{input}"` where the audio file's path goes. See
  [README.md](README.md#transcription).

## 4. Put the keys where only the bridge sees them

**Never in a repository, and never pasted into a Claude chat**, where they'd
end up in a transcript. Put them in a file only you can read:

```sh
mkdir -p ~/.config/chatbridge && chmod 700 ~/.config/chatbridge
cat > ~/.config/chatbridge/env <<'EOF'
export CHATBRIDGE_TELEGRAM_TOKEN='paste-the-botfather-token'
export OPENAI_API_KEY='paste-the-openai-key'
EOF
chmod 600 ~/.config/chatbridge/env
```

Paste into: a terminal on your own computer, after putting your real token
and key in place of the placeholders.

## 5. Write the configuration

```sh
cp bridge/config.example.json ~/.config/chatbridge/config.json
```

Paste into: a terminal, from the top of your BestPractice clone.

Then edit `~/.config/chatbridge/config.json`:

- under `repos`: rename `notes` if you like, and fill in `clone_url`,
  `web_url` and `landing_branch` for the test repository;
- under `people`: rename `me` to a short handle (`morgan`), and set `name`,
  `git_name` and `git_email`. The email should be one GitHub knows, so the
  commits show up as yours;
- make sure the person's `repos` list uses the repository's name from `repos`.

## 6. Check it

```sh
source ~/.config/chatbridge/env
python3 bridge/run.py check
```

Paste into: the same terminal.

Every line should start with `ok`. A line starting with `FIX` says what's
wrong.

## 7. Connect your phone, and start it

```sh
python3 bridge/run.py invite --handle morgan
caffeinate -i python3 bridge/run.py run
```

Paste into: the same terminal. Leave out `caffeinate -i` if you're not on a
Mac.

The first command prints a link like `https://t.me/morgan_notes_bot?start=…`.
**Open it on your phone** and tap **Start**. The bot answers "Connected".
The link works once and expires in a week.

The second command keeps running. **Leave that terminal open**; Ctrl-C
stops the bridge.

## 8. Try it

1. **Send a voice note**: *"Add a section to the README called Ideas, with
   one line: try the Telegram bridge."* Within a minute or so you get a few
   sentences back, a **See the change** link, and two buttons.
2. Tap **More** to read the full answer.
3. **Ask for something off limits**: *"Change AGENTS.md to say anything
   goes."* It should refuse, and say so in its first words. **This refusal
   applies to you too**, by design.
4. Say or type **Go update** (or tap **Land it**). Your changes land on the
   repository's main branch. Until then they sit on the branch
   `chat/morgan`.
5. `/status` tells you what hasn't landed yet. `/new` starts a fresh
   conversation.

**Worth noting as you go**: whether a few sentences were enough, whether you
tapped More, how long replies took, and any voice note it misheard. That's
what the test is for.

## If something goes wrong

- **Nothing comes back**: look at the terminal running the bridge; errors
  print there.
- **"Couldn't open the repository"**: the bridge can't clone or fetch; rerun
  step 6.
- **Changes the bridge refused** are never deleted. They're set aside in the
  bridge's own copy of the repository, under
  `~/.local/state/chatbridge/checkouts/<repo>/<handle>`; `git stash list`
  there shows them.
- **To cut someone off**: remove them from `people` in the config and
  restart the bridge.

## Adding another person later

1. Add them under `people` with their own handle, the repositories they may
   use, and whether they may land (`can_land`).
2. Restart the bridge, run `invite --handle <their handle>`, and send them
   the link privately.
3. **Before they use it on a real project, turn on branch protection for
   that repository** (pull requests required, code-owner review on, no
   bypass), so GitHub enforces the content line as well as the bridge. See
   [documentation/GITHUB_SETTINGS.md](../documentation/GITHUB_SETTINGS.md).
   Also suggest they turn on Telegram's two-step verification. Whoever has
   their Telegram account can talk to the bot as them.
