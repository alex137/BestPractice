---
title:         Shared Openings and the Providers' Prompt Caches
kind:          proposal
status:        drafted
opened:        2026-11-22
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Can Precedent make sessions start faster and cheaper by giving many people the same opening text? Every large provider keeps its cache inside one customer's account, so nobody can host an opening for others; what is left is keeping Precedent's own text identical and first, which it mostly is already. The prize is at most about 6,700 to 11,500 ordinary input tokens per session start here. Pick: a small feature of Precedent and one measurement, not a product."
---
# Shared Openings and the Providers' Prompt Caches

*Abstract.* Every session in a repository that uses Precedent begins by
loading the same text. A model provider's prompt cache serves a repeated
opening at a fraction of the price, and sooner, when the opening is the
same from its first word. This note asks whether Precedent could host
openings that many people share, so that each of their sessions starts
warm. It reads the four large providers' own documentation, looks at what a
session's opening really contains under each assistant program this
repository supports, and counts what could be saved from this repository's
own load-budget figures. The idea is judged on one question: does anybody
besides the provider get to decide who shares a cache? The answer is no,
and that settles most of it.

## Contents

- [What the Answer Is](#what-the-answer-is)
- [How the Providers Cache](#how-the-providers-cache)
- [What a Session's Opening Looks Like to the Cache](#what-a-sessions-opening-looks-like-to-the-cache)
- [What Precedent Could Do, Smallest First](#what-precedent-could-do-smallest-first)
- [Product, Feature or Neither](#product-feature-or-neither)
- [What Is Not Known](#what-is-not-known)

**Where the numbers come from.** Every provider figure is quoted from the
provider's own page, read on 2026-11-22, and the passages relied on are
stored under [shared-openings-sources/](shared-openings-sources/), one file
per page with its address. Every token count for this repository is
computed by [shared_openings_figures.py](shared_openings_figures.py) from
the files themselves and from
[tools/session_load_budgets.json](../tools/session_load_budgets.json),
counted the rough way the load budget counts (words times 1.3). Two figures
are single measurements of the session that wrote this note and are
labelled so. Nothing here is an estimate.

## What the Answer Is

- **Nobody can host a shared opening.** Anthropic, OpenAI and Google each
  say in writing that a cache is never shared across customers' accounts.
  xAI does not say either way. A cache lives inside the provider, keyed to
  the customer who paid to fill it.
- **So "hosting shared openings" reduces to "publish the text in a form
  that hits each customer's own cache".** Precedent already publishes that
  text: it is the tracked instructions file, the same for everyone on the
  same commit.
- **Under Claude Code the cache is narrower still.** Anthropic's own page
  says it is "effectively scoped to one machine and directory". Two people
  in the same repository do not share it, and neither do two checkouts.
- **The prize is small.** A warm opening saves at most about 6,700 to
  11,500 ordinary input tokens once per session start here, and at most
  about 11,500 to 19,750 for a repository at the 10,000-token ceiling.
  Inside a session the assistant program already caches every turn.
- **Pick:** a small feature of Precedent, namely keep its own text
  byte-for-byte stable and keep what changes last, plus one measurement
  before building anything. Not a product.

## How the Providers Cache

All four cache a **prefix**: the request from its first token up to some
point. A later request reuses the stored work only as far as it is
identical. One changed character near the top loses everything after it.

| | Anthropic | OpenAI | Google | xAI |
|---|---|---|---|---|
| **Who shares a cache** | One organization, and on Anthropic's own API one workspace inside it. Never across organizations. | One organization and one processing region. Never across. | Vertex: one project, never across. Gemini API: not documented. | Not documented. |
| **How long it lives** | 5 minutes, or 1 hour at a higher write price. Each read restarts the clock. | Newest models: at least 30 minutes, or 12 hours at a higher write price. Older models: about 5 to 10 minutes idle, up to an hour; or up to 24 hours. | Automatic: no later than 24 hours on Vertex, "most entries are evicted earlier"; not stated for the Gemini API. A created cache: 1 hour unless set, no upper limit. | No lifetime stated. "Cache entries can be evicted at any time." |
| **What a write costs** | 1.25 times ordinary input for 5 minutes, 2 times for 1 hour. | Newest models: 1.25 times for 30 minutes, 2.5 times for 12 hours. Older models: no extra charge. | Automatic: no extra charge today. A created cache: storage by the hour. | No charge mentioned. |
| **What a read costs** | 0.1 times ordinary input; 0.05 and 0.025 times on the newest models. | 0.1 times on most newest models, 0.05 times on some; older models vary by model. | Vertex: 90% off. Gemini API: "a reduced rate", per model on the price page. | Per model on the price page; the listed models work out between 15% and 25% of input. |
| **Keep it alive or pin it** | No pin. A read refreshes it; a request that asks for no output can warm it. | No pin. A read refreshes it; a warm-up request exists on the newest models. | A created cache: yes, its lifetime can be extended without limit. Automatic: no. | No. A header keeps requests on the same server, which makes a hit likelier, not certain. |

The words behind each cell:

**Anthropic.** "Different organizations never share caches, even if they
use identical prompts." "On the Claude API, Claude Platform on AWS, and
Microsoft Foundry, caches are also isolated between workspaces." "Cache
hits require 100 percent identical prompt segments." "By default, the cache
has a 5-minute lifetime. The cache is refreshed for no additional cost each
time the cached content is used." "Cache write tokens with a 5-minute TTL
are 1.25 times the base input tokens price ... 1-hour TTL are 2 times ...
Cache read tokens are 0.1 times the base input tokens price." "There's no
way to manually clear the cache." Warming: "Set `max_tokens: 0` in your
request ... For the default 5-minute cache, send a new pre-warm request at
least every 5 minutes to keep the cache warm."
([prompt caching page](shared-openings-sources/anthropic-api-prompt-caching.txt),
[pricing](shared-openings-sources/anthropic-api-pricing.txt))

**OpenAI.** "Caches are not shared across organizations and cannot be
reused across regional processing boundaries." "Cache reuse requires the
entire rendered prefix to match." "Keys influence routing; they do not pin
requests to a machine or guarantee a cache hit." On the newest models,
"cache writes cost 1.25× the standard, uncached input-token rate for the
default 30-minute lifetime", and reads "cost 0.1× the ordinary input rate
on most of these models". "Cache entries are not stored indefinitely."
OpenAI's own advice is this note's subject in one line: "Put stable
developer instructions and shared reference material first. If developer
instructions or shared material contain timestamps, user-specific content,
or other dynamic content, place those at the end".
([prompt caching guide](shared-openings-sources/openai-prompt-caching-guide.txt),
[pricing](shared-openings-sources/openai-api-pricing.txt))

**Google.** "Google Cloud uses your project number to isolate cached data,
and cached content is never shared across projects." "A cached prefix
expires no later than 24 hours after it's created, and most entries are
evicted earlier." "Implicit caching provides a 90% discount on cached
tokens compared to standard input tokens." For a cache the customer
creates: "If not set, the TTL defaults to 1 hour" and "There are no minimum
or maximum bounds on the TTL." Google's pages now say a created cache is
"not supported for Gemini 4 models", which get the automatic kind only.
([Vertex overview](shared-openings-sources/google-vertex-context-cache-overview.txt),
[Gemini API caching](shared-openings-sources/google-gemini-api-caching.txt),
[Gemini API pricing](shared-openings-sources/google-gemini-api-pricing.txt))

**xAI.** "When consecutive requests share the same starting messages, the
xAI API automatically caches them." "Cache entries can be evicted at any
time due to server load or restarts." "Since cache entries are stored
per-server", a conversation header "routes requests with the same
conversation ID to the same server".
([overview](shared-openings-sources/xai-prompt-caching-overview.txt),
[questions page](shared-openings-sources/xai-best-practices-faq.txt),
[cache hits page](shared-openings-sources/xai-maximizing-cache-hits.txt),
[pricing](shared-openings-sources/xai-pricing.txt))

**Time saved.** No provider gives a current figure. Anthropic: "You
generally see improved time-to-first-token for long documents." OpenAI:
"Reduce the time spent processing input before the response starts." xAI's
own worked example found that at a few thousand tokens "Time to first token
barely changed." Precedent's opening is a few thousand tokens.

## What a Session's Opening Looks Like to the Cache

A request is built in layers, and the assistant program owns the first
ones. Precedent's text never comes first.

**Claude Code.** Anthropic documents the order and what varies:

- **First, the program's own tool list and system prompt.** They are the
  same for everyone on the same version and settings, with one exception:
  "The system prompt embeds your auto memory paths", which are named for
  the repository's place on disk, "so it differs across users, machines,
  and checkouts."
- **Then the conversation, which opens with facts about the machine:**
  "an announcement of the working directory, platform, shell, and OS
  version", and on a person's own computer a snapshot of the repository:
  "Sequential sessions share the prefix only when the git status snapshot
  taken at startup matches". Cloud sessions "never include the snapshot".
- **Then Precedent's text.** "CLAUDE.md content is delivered as a user
  message after the system prompt, not as part of the system prompt
  itself." This repository's [CLAUDE.md](../CLAUDE.md) pulls in [AGENTS.md](../AGENTS.md), so the
  resident rules and the occasion index arrive here.
- **Then what session start prints**, "added to Claude's context at the
  start of the conversation, before the first prompt". That is where
  Precedent's per-person session practices arrive.
- **Then, on every turn, what the turn's own check prints**, put in "at
  the point where the hook fired".

Anthropic's summary: "In Claude Code, the cache is effectively scoped to
one machine and directory ... Two sessions in different directories
therefore build different prefixes and miss each other's cache."
([Claude Code caching page](shared-openings-sources/anthropic-claude-code-prompt-caching.txt),
[memory page](shared-openings-sources/anthropic-claude-code-memory.txt),
[hooks page](shared-openings-sources/anthropic-claude-code-hooks.txt))

**One documented way around the machine limit, for people who build their
own program on Anthropic's agent kit.** A setting moves the per-machine
part out of the system prompt, "leaving only the static preset and your
`append` text in the system prompt so identical configurations share a
cache entry across users and machines". Still inside one organization.
([agent kit page](shared-openings-sources/anthropic-claude-code-sdk-system-prompts.txt))

**Codex.** The current Codex pages say which instruction files are read
and in what order (the person's own, then the repository's from its root
down, 32 KiB in all by default), and do not say where they sit in the
request. An OpenAI engineering post from January 2026 does: after the
system message, the tools and two developer messages, as a user message,
with the description of the working directory and shell after it. Whether
the program still does that is not documented.
([instruction files page](shared-openings-sources/openai-codex-agents-md.txt),
[engineering post](shared-openings-sources/openai-unrolling-codex-agent-loop.txt))

**Gemini CLI.** Its context files "are concatenated ... and provided as
part of the system prompt", the person's own file first, then the
repository's. Its token caching works with a paid key and not with a
personal Google sign-in.
([configuration page](shared-openings-sources/google-gemini-cli-configuration.txt),
[token caching page](shared-openings-sources/google-gemini-cli-token-caching.txt))

**What Precedent's own text does to a match, here.** Computed by the
script:

| Part | Tokens (rough) | Changes when |
|---|---|---|
| [AGENTS.md](../AGENTS.md), hand-written lines before the practice block | 885 | somebody commits a change to them |
| [AGENTS.md](../AGENTS.md), resident rules | 856 | a practice changes; **its heading carries generated counts**, so any added practice changes it |
| [AGENTS.md](../AGENTS.md), occasion index and standing instruction | 2,678 | a practice with an index line changes |
| [AGENTS.md](../AGENTS.md), hand-written lines after the practice block | 1,358 | somebody commits a change to them |
| [CLAUDE.md](../CLAUDE.md) | 55 | almost never |
| **Tracked files: the same for everyone on the same commit** | **5,832** | |
| Session practices file, written at session start | 880 | per person, and per session when a practice set did not load |
| **Whole opening Precedent adds** | **6,712** | |
| Ceiling a repository may reach | 10,000 | |

Three findings about the changing parts:

1. **The tracked text holds no date and no machine path.** It changes
   only with a commit. That is the good news: for everyone on the same
   commit it is already identical, and it already comes before the
   per-person part.
2. **The session practices file is not stable when something fails.**
   Measured in this session: it was 478 tokens while one practice set was
   missing, opened with a line carrying the time it was written to the
   minute and a path on this machine, and was 880 once the set loaded.
   Session start's own status lines carried times to the second.
3. **The per-turn text outweighs the opening within a few turns.** The
   text this repository's check prints at the start of each turn measured
   2,177 tokens on one turn of this session. It is added at the end, so it
   breaks no match, but it is new text every turn; three turns of it is
   about the size of the whole opening.

## What Precedent Could Do, Smallest First

What a warm opening can save, per session start, in ordinary input tokens
(computed; "nothing warm" pays the write price, "already warm" pays the
read price):

| Case | Tracked files (5,832) | At the ceiling (10,000) |
|---|---|---|
| Nothing warm, 5-minute write | 7,290 | 12,500 |
| Nothing warm, 1-hour write | 11,664 | 20,000 |
| Already warm, read at 0.1 | 583 | 1,000 |
| Already warm, read at 0.025 | 146 | 250 |
| **The most a warm opening can save** | **6,707 to 11,518** | **11,500 to 19,750** |

That is the whole prize, once per session start, and only when another
session with the identical beginning ran inside the cache's lifetime, in
the same account, and under Claude Code on the same machine and folder.

1. **Keep what changes last and out of the stable text.** Session start
   prints the session practices first and its status lines after; no time
   of day, and no "kept from an earlier run" line, sits above stable text.
   Saves at most the session file's share, 880 tokens' worth per start, in
   the sessions where something failed. Cheap, and it is OpenAI's and
   xAI's own written advice.
2. **Take the generated counts out of the resident block's heading.** The
   heading changes whenever any practice is added anywhere, and everything
   after it, 4,947 of the 5,832 tokens, stops matching for sessions
   on either side of that commit. Small saving; smaller change.
3. **Make the stable part identical for every user of the same practice
   set.** It already is, at the same commit. What stops two people sharing
   it is the provider's account boundary and Claude Code's per-machine
   beginning, neither of which Precedent can move.
4. **The same for people sharing one private repository.** The tracked
   block in a private project already carries the team's rules, identical
   for all of them. They share a cache only if they are in one
   organization at the provider, and, under Claude Code, not even then
   across machines. On a team that builds its own program on the agent
   kit, the documented setting above does give a shared beginning; that is
   a how-to page, not a mechanism.
5. **A per-repository opening that also carries the repository's
   orientation** (the map, the where-things-are page). It adds tokens to
   every session, against the 10,000 ceiling, to save a file read that is
   itself cached for the rest of the session once made. It would pay only
   if most sessions read those files anyway. That is a question for a
   measurement, and the load budget's history argues the other way.
6. **A hosted service.** It cannot hold anyone's cache. What it could
   add: a published, byte-exact opening per practice-set version, which
   the git repository already is; and a timer that keeps a customer's
   cache warm, which has to run with the customer's own key inside the
   customer's own account, costs a read of the whole beginning each time,
   and saves nothing unless a session starts before the cache would have
   lapsed. That is a scheduled job the customer runs, not a service.

## Product, Feature or Neither

**A small feature of Precedent, and not a product.**

- **The thing a product would sell does not exist.** The providers keep
  each cache inside one customer's account. There is no shared opening to
  host.
- **The saving is too small to carry a product.** A few thousand tokens,
  once per session start, when the timing happens to be right. The
  per-turn text and the assistant program's own beginning are both larger
  and both outside what a shared opening touches.
- **What is worth having is nearly free:** items 1 and 2 above, and a line
  in the catalogue saying that always-loaded text stays stable and puts
  what changes last. That is hygiene inside the engine.
- **The larger lever found on the way is the per-turn text**, 2,177 tokens
  a turn in this session. Trimming what is printed every turn saves more
  than any arrangement of the opening. It belongs to the load budget, and
  is filed with the open item.

Should there be a Precedent thread to explore it? One short one: run the
measurement below, do items 1 and 2 if it shows a miss, and stop.
The open item is
[todo-2026-11-22-shared-openings](../todo/todo-2026-11-22-shared-openings-keep-the-opening-stable-and-measure-it.md).

## What Is Not Known

- **Whether the opening is being read from cache at all today.** Every
  request's reply says how many tokens were read from cache. Two sessions
  started back to back in the same checkout, with the first reply's count
  compared against the 5,832 above, would say. Not done here.
- **Whether two cloud sessions of one repository share a beginning.** Each
  runs in a new machine; Anthropic's pages say cloud sessions leave out
  the repository snapshot and do not say whether the rest matches.
- **Whether today's date sits in the request, and where.** Not documented
  for Claude Code or Codex.
- **How cached reads count against a subscription's limits.** Anthropic
  documents only that cached re-reads "still" draw usage "at the cached
  token rate"; OpenAI only that Codex credit billing "has no separate
  cache-write charge".
- **Who shares a cache at xAI and on Google's Gemini API.** Neither says.
- **Where Codex puts the instruction file today**, as above.
- **The per-turn figure in a healthy session of another repository.** The
  2,177 is one turn of one session here.
