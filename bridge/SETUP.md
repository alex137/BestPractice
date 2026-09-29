# Setting Up the Chat Bridge — In a Claude Code Cloud Session

This runs the Telegram bridge **inside a Claude Code cloud session**, like the
ones you already use at claude.ai/code. Nothing is installed on your computer.
It's written for **you alone** on **one test repository**. Adding another
person is near the end, and running it on your own computer instead is the
last section. How it works and why is in [README.md](README.md).

**About half an hour the first time**, mostly steps 2 and 3. After that,
starting it again is one paste.

## What a Cloud Session Means for the Bot

- **The bot answers only while its session's machine is running.** A cloud
  session's machine is reclaimed after a while without activity, and the bot
  stops with it. How long an idle session keeps running isn't something I
  can tell you in advance; finding out is part of the test. Restarting is
  one paste (step 7).
- **Each new machine starts with an empty memory.** Claude's recollection of
  earlier messages and the full answers behind **More** are gone. **That's
  fine to lose for a test**: every change you made is already on GitHub, on
  your chat branch or landed.
- **Changes the bridge refused are set aside on that machine**, so they go
  when it goes. That's fine to lose: they're edits it wouldn't save, and
  the full answer (under More, while the machine lasts) says what they were.
- **Claude's turns run on the session's own Claude login**, so they count
  against your plan like any other session. No separate key.
- **Voice notes are transcribed in the same machine**, by an open-source
  Whisper model. The audio isn't sent to any other company, and you need no
  extra account. Claude itself can't listen to audio, so this is the
  nearest thing to handing it the recording: it runs right beside Claude.

## 1. Make a Test Repository

On GitHub, create a **private** repository, for example `chat-test`, with a
README file and nothing else. Write down its full name, `your-account/chat-test`.
Its main branch (usually `main`) is where "Go update" lands your changes.

**The test repository doesn't need BestPractice installed**, and for the
first test it's better without it. Any git repository works: the bridge
brings its own content-only line (a built-in list of machinery paths), and
adds whatever the repository's own `CODEOWNERS` or Precedent configuration
names. A repository that does have Precedent installed works too. Its
instructions then shape Claude's content work, but its hooks don't run in a
chat turn, and its commit checks may want things the bridge's commits don't
carry. Test on a plain one first.

## 2. Create the Bot

About 2 minutes, in Telegram on your phone:

1. Open a chat with **@BotFather** (check for the blue tick).
2. Send `/newbot`. Give it a display name, then a username ending in `bot`,
   for example `morgan_notes_bot`.
3. BotFather replies with a **token**, a long string with a colon in it.
   **Treat it like a password.** You'll paste it into the environment
   settings in step 3, **never into a chat with Claude**, where it would end
   up in a transcript.
4. Send `/setjoingroups`, pick your bot, and choose **Disable**, so nobody
   can add it to a group.

## 3. Make a Cloud Environment for the Bridge

**Use a separate environment for this, not the one your usual sessions
run in.** It holds the bot token and needs network access your other
sessions shouldn't have.

At claude.ai/code, open the cloud environment menu in a session's title
bar, create a new environment (name it `chat bridge`), and set:

**Network access.** Keep the default access level and add these to the
allowed domains:

- `api.telegram.org`: the bot talks to Telegram here;
- `huggingface.co`: the Whisper model downloads from here the first time
  on each machine.

If a start-up check later says another host was refused (the model's
download host may be a second one), add that too. The check names it
exactly.

**Environment variables.** Paste this into the environment variables box,
then replace the parts in capitals. The box takes one `NAME=value` per line.
The table below says what each one is for.

```text
CHATBRIDGE_TELEGRAM_TOKEN=PASTE-THE-TOKEN-FROM-BOTFATHER
CHATBRIDGE_REPO=YOUR-ACCOUNT/chat-test
CHATBRIDGE_HANDLE=morgan
CHATBRIDGE_NAME=Morgan
CHATBRIDGE_LANDING=main
CHATBRIDGE_LANGUAGE=en
CHATBRIDGE_WHISPER_MODEL=small
```

Paste into: the environment variables box of the `chat bridge` environment's
settings. Add `CHATBRIDGE_TELEGRAM_USER_ID=<your id>` as its own line after
step 6.

**Don't add `ANTHROPIC_API_KEY` to this environment** unless you mean to: if
it's set, Claude's chat turns bill to that API key instead of your plan.

| Variable | Set it to | Needed? |
|---|---|---|
| `CHATBRIDGE_TELEGRAM_TOKEN` | The token from BotFather | Yes |
| `CHATBRIDGE_REPO` | `your-account/chat-test` | Yes |
| `CHATBRIDGE_HANDLE` | A short name for you, like `morgan` | Recommended |
| `CHATBRIDGE_NAME` | Your first name, used in how Claude addresses you | Recommended |
| `CHATBRIDGE_LANDING` | The branch "Go update" lands on, if it isn't `main` | Only if different |
| `CHATBRIDGE_LANGUAGE` | `en`, so Whisper doesn't have to guess the language | Recommended |
| `CHATBRIDGE_TELEGRAM_USER_ID` | Your Telegram user id. The bot tells you it when you first connect (step 6); set it then to skip the invite on every restart | After step 6 |
| `CHATBRIDGE_WHISPER_MODEL` | `small` by default. `base` is faster and less accurate; `medium` is slower and more accurate | Optional |

**Setup script (optional, makes starts quicker).** This installs the
Whisper package when each machine starts, instead of on the first start
of the bridge:

```sh
python3 -m venv ~/.cache/chatbridge-venv && ~/.cache/chatbridge-venv/bin/pip install --quiet faster-whisper
```

Paste into: the Setup script box of the `chat bridge` environment's
settings.

## 4. Start a Session in That Environment

Open a new session in the **`chat bridge`** environment, **rooted in
`alex137/BestPractice`**, with your test repository **attached** as well,
and paste:

```text
From the Telegram-access session (https://claude.ai/code/session_0174aVwbMQNw2xGPpHDpDGnD):
start the Telegram chat bridge for my test.

1. In BestPractice, fetch and check out the branch
   claude/telegram-access-brainstorm-7f10il -- the bridge lives there.
2. Make sure my test repository (the one CHATBRIDGE_REPO names) is attached
   to this session WITH PUSH ACCESS -- the bridge pushes its chat branch
   and lands changes there; attach it if not.
3. Run `bash bridge/cloud_start.sh` in the background and watch its output.
4. If it prints FIX lines, tell me in plain words what to change in this
   environment's settings, and stop.
5. Otherwise give me the invite link it prints (if it prints one), and tell
   me when the bridge says it is serving.
6. If the bridge process stops later, tell me why and restart it once.

This is a test run: change no code, and push nothing yourself -- the bridge
makes its own commits to my test repository.
DO NOT MERGE — STOP AT THE PULL REQUEST
```

Paste into: a new session in the `chat bridge` cloud environment, rooted in
`alex137/BestPractice`, with your test repository attached.

The first start takes a few minutes: it installs Whisper (unless the setup
script already did), downloads the model, and checks everything.

**Only one bridge per bot at a time.** Telegram hands each message to one
poller, so if an old session is still running the bridge when you start a
new one, both complain of a conflict. Stop the old one first: open it and
say *stop the bridge*.

## 5. If the Check Says FIX

The session tells you which line failed. The usual ones:

- **`network`**: a host was refused. Add it to the environment's allowed
  domains, then tell the session to run the start script again.
- **`Telegram bot token`**: the token variable is missing or mistyped.
- **`repo … reachable`**: the test repository isn't attached to the
  session, or `CHATBRIDGE_REPO` has a typo.

## 6. Connect Your Phone

**Open the invite link on your phone** and tap **Start**. The bot answers
"Connected" and tells you your Telegram user id. Put that id into
`CHATBRIDGE_TELEGRAM_USER_ID` in the environment settings, so later restarts
recognise you without a new invite. The invite link works once and expires in
a week.

## 7. Try It

1. **Send a voice note**: *"Add a section to the README called Ideas, with
   one line: try the Telegram bridge."* You get a few sentences back, a
   **See the change** link, and two buttons. What it heard is attached,
   folded away.
2. Tap **More** to read the full answer.
3. **Ask for something off limits**: *"Add a GitHub workflow file."* It
   refuses and says so in its first words. **The refusal applies to you
   too**, by design.
4. Say or type **Go update**, or tap **Land it**. Your changes land on the
   main branch. Until then they sit on the branch `chat/<your handle>`.
5. `/status` shows what hasn't landed yet. `/new` starts a fresh
   conversation.

**When the bot stops answering**, the session's machine has probably been
reclaimed. Open the `chat bridge` session again, or start a new one with the
same paste from step 4, and say *restart the bridge*.

**Worth noting as you go**: whether a few sentences were enough, whether you
tapped More, how long replies took, what Whisper misheard, and how long the
bot kept running between uses. That's what this test is for.

## Adding Another Person Later

**This test build isn't ready for other people yet.** Three things stand in
the way, and [the spec](../spec/SPECULATIVE_TELEGRAM_ACCESS.md#what-could-go-wrong-before-others-use-it)
has the full list:

- **Their turns would run on your Claude login.** A cloud session's login
  is yours, for your own use. For anyone else, the bridge should run on an
  Anthropic API key, billed per use, which also makes the cost visible.
- **Landing is a direct push**, which a protected branch rightly refuses. For
  now give other people `"can_land": false`: their changes wait on their chat
  branch, and you land them from the compare link `/status` gives. Landing
  through a pull request is the missing piece.
- **Branch protection is the lock GitHub enforces**, and every real
  repository needs it before anyone else uses the bridge on it: pull
  requests required, code-owner review on, no bypass. See
  [documentation/GITHUB_SETTINGS.md](../documentation/GITHUB_SETTINGS.md).

When those are dealt with: write a configuration file from
[config.example.json](config.example.json) with each person, their
repositories and `can_land`, run the bridge with it
(`python3 bridge/run.py run --config <file>`), and send each of them an
invite (`python3 bridge/run.py invite --config <file> --handle <theirs>`),
which works while the bridge is running. Suggest they turn
on Telegram's two-step verification, since whoever holds their Telegram
account can talk to the bot as them.

## Running It on Your Own Computer Instead

The same bridge runs on any always-on machine with Python 3.9+, Claude Code
logged in, and git able to push to the repository. Copy
[config.example.json](config.example.json) to
`~/.config/chatbridge/config.json`, fill it in, and put the bot token in the
`CHATBRIDGE_TELEGRAM_TOKEN` environment variable. Then:

```sh
python3 bridge/run.py check
python3 bridge/run.py invite --handle morgan
python3 bridge/run.py run
```

Paste into: a terminal on that machine, from the top of a BestPractice
checkout on the branch above.

For voice notes there, pick a transcription backend in the config: local
Whisper (`pip install faster-whisper`, then `"backend": "whisper-local"`), an
OpenAI-compatible service, or any local command
([README.md](README.md#transcription)).
