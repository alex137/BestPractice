---
slug:        whats-new
title:       "\"What's new?\" keeps a running log of what changed in the project, and shows it"
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "A phrase in a MESSAGE -- no file path reaches it. The log's own mechanics are in tools/precedent_whats_new.py. Decided: 2026-09-30, when the practice landed."
occasion:    "a person asks \"What's new?\", or what has changed in the project lately"
gates:       []
index_clause: "write every missing day, quiet ones named; the reply opens with the link"
checked_by:  null
defines:     ["What's new"]
command:     {"What's new?": "Write an entry for every finished day that changed the project and has none yet, say which days were quiet and skipped, then show the log: its link first, the newest entries, what changed today so far, and ask what you want to know more about."}
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-30"
approved_by: "Morgan, 2026-09-30 -- the plan from a brainstorm session, the entry shape
  after two review rounds, then a critique he agreed with except four points:
  a running log of everything interesting rather than since a reader's last
  visit; entries chosen for what is most noteworthy, a content day included;
  approximate figures, with no mechanical figure check; and one phrase that
  writes what is missing and then shows it. \"Act!\" Amended 2026-10-01
  from his review of the first daily entry: open the reply with the log's
  link; write every missing day, not only yesterday; a quiet day gets no
  entry and the reply says so; a fixed opening line instead of a summary
  headline; a weekday and a slug in each heading; any change counts, a
  content day included; rewrite the past entries once. \"Act\""
strength:    decided
---
## Rule
**"What's new?" has two halves, in this order.**

**1. Bring the log up to date.** Run
`python3 tools/precedent_whats_new.py --days`. It lists **every finished
day since the log's last one, however many** -- not only yesterday. Say
first how many you are about to write (*"writing the 3 missing days
first"*), then write **one entry per day**, newest first, at the top of the
log. **A quiet day, with no activity at all, gets no entry**: put nothing in
the log for it, and tell the person which days were quiet and skipped. Run
`python3 tools/precedent_whats_new.py --mark <the latest day listed>`, quiet
or not, then `--check`. A day already covered is never written twice, so a
second "What's new?" the same day skips straight to half 2. Commit the log
like any other change.

**2. Show it.** **The reply opens with the log's link** (*"check here
daily"*), before anything else. Show the newest entries, then what changed
today so far (`--today`), which no entry covers yet. Then ask what they want
to know more about.

**The log is a running record of everything interesting the project did**,
not a digest since someone's last visit. **Any change counts, not only
code.** An entry picks **the day's most noteworthy changes**, whether code,
plumbing or content. A new guide or a new philosophy document can be the
day's news without a commit message saying so, and `--days` lists each
day's new documents for that reason. In a project whose day was mostly
content -- many pages written or revised -- the entry names the most
important of those, the same way.

**An entry's shape:**

- **The heading:** the weekday, the date, and a slug in backticks, as in
  *Wednesday 2026-09-30: `daily-log-and-safer-merges`*. The slug is a few
  lowercase words joined by hyphens naming the day's top highlight. It is
  not a link; the backticks mark it as a name, and keep
  [headline-capitalization](headline-capitalization.md) from capitalizing
  it.
- **The opening line, word for word:** *"Some top highlights from the
  day's activity, ask if you want to learn everything done."* Never a
  sentence summing up the bullets: in something this short it only says
  them twice.
- **About three bullets.** Each says the change plainly first, then the
  technical version in parentheses, with a real figure or a real technical
  name: *"The instructions every session reads first got much shorter (the
  opening of AGENTS.md went from about 3,460 tokens to about 980)."* Lead
  with what a reader would most want to know, not with command words.
**Approximate is fine** ("about 800 tokens per session"): the figure has to
be real, not exact ([no-invented-specifics](no-invented-specifics.md)).
**Never name who approved or signed off on anything.**
`python3 tools/precedent_whats_new.py --check` flags an entry that does,
and one whose heading or opening line is not in the shape above; an older
entry it flags is rewritten into the shape once.

## Detail
**Where the log lives.** `WHATS_NEW.md` at the root (the tool: [tools/precedent_whats_new.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_whats_new.py)), or wherever
`precedent.json`'s `whats_new_path` points. Its one piece of state is its
front matter, `checked_through: <date>`: the last day it covers. That also
answers whether today's run already happened, since "checked through
yesterday" means it did. The tool reads the later of this checkout's log
and `main`'s, so a session working from a checkout that is behind doesn't
write days `main` already has.

**What counts as a day.** A calendar day in the repository's timezone
(`fallback_timezone` in `precedent.json`), never the writer's own: the log
is shared, so a day has to end at the same moment whoever writes it. A day
counts when `main` changed during it. A day with no change is quiet: no
entry, said in the reply. So is a commit that touches only the log, or the log reaching `main`
would be news every day. The first run, with no log yet, covers the last
seven finished days.

**It runs newest first**, the one kind of dated list that does: a reader
opens a news log for the latest
([dated-list-runs-forward](dated-list-runs-forward.md) names this
exception).

**Fixing an entry is an ordinary edit.** The opening line is fixed in one
place, `HEADLINE` in the tool, and `--days` prints it.

## Why
A shared project changes between a member's conversations, and nothing
brings those changes into their old chats. A summary made up at each
session start was different every time and left nothing behind. A log
written once a day, in plain words with the real figure beside them, is
something a member can check daily, link to, and trust.

## Story
Designed 2026-09-30 in a brainstorm session, critiqued in another. The
entry shape went through two review rounds. The critique found that the
log would have logged its own commits, that a tiered repo's `main` holds
only Promote merges (so the listing reads the commits they brought), and
that a person's own timezone would move a shared day's edges. It replaced
the templates' "catch the member up at session start" paragraph, which
summarized afresh each time and kept nothing.

The first daily entry, on 2026-10-01, had a bold headline sentence that
summed up its own bullets, so a four-bullet entry said everything twice. It
became a fixed opening line, the heading gained a weekday and a slug, quiet
days became something the reply says rather than something silently
skipped, and the ten entries already written were rewritten into the shape.

## Install
Nothing to do: the tool ships with the engine, and the first "What's new?"
creates the log.
