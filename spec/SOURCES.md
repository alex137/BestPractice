<!-- Last updated: 2026-08-31 (Buenos Aires) by a phase-3 build session -->

# The Three Sources (Phase 3)

What [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s
"[Source — Who a Practice Belongs To](../PRACTICE_ENGINE_PLAN.md#source--who-a-practice-belongs-to)"
and
"[Precedence, and the One Case Where the Individual Does Not Win](../PRACTICE_ENGINE_PLAN.md#precedence-and-the-one-case-where-the-individual-does-not-win)"
build to in this repo, and — as importantly — what phase 3 could **not** build
from here and why. Read the plan sections first; this is the implementation
note.

## What exists

| Plan's requirement | Built as | Status |
|---|---|---|
| Levels are repositories, not directories | [tools/precedent_resolve.py](../tools/precedent_resolve.py) resolves N source *directories*, each a checkout of a separate repo | Built. Nothing about a level is a field; it comes from which source a file was loaded from. |
| A consumer repo declares universal + team | [precedent.json](../precedent.json), tracked, at the repo root | Built. Precedent carries one for itself: it runs on the universal set it publishes. |
| A person declares their own individual set | `~/.config/precedent/config.json`, or `PRECEDENT_USER_CONFIG` | Built. A shared repo naming an individual source is refused **by name**, with the privacy reason in the message. |
| Precedence: individual > team > universal | Sources walked lowest-first; later replaces earlier | Built and tested. |
| `overrides:` names a lower slug | Same walk, with the named slug as a second target | Built and tested. |
| `severity: blocking` at team/universal cannot be overridden | Refused, and the refusal is *reported* | Built and tested. |
| Degrade gracefully when the individual set is missing | Resolves on what it has, says on stderr what is **not in force** | Built and tested. `--strict` makes it fatal where a caller wants that. |
| A retired practice is resolvable but not in force | `status:` filtered at resolve time | Built and tested. |
| The frozen example set | [examples/practice-set/](../examples/practice-set) | Built — invented content, see below. |
| The leak gate's vocabulary layer | [tools/leak_gate.py](../tools/leak_gate.py), blocklist from `PRECEDENT_LEAK_BLOCKLIST`, template at [templates/leak-blocklist.txt.template](../templates/leak-blocklist.txt.template) | Built and switched on. |
| The private sets **populated** from RepoPersonalPreferences' 46 rules | — | **Not done. See below.** |

Twenty-one stated cases in [tools/verify_harness.py](../tools/verify_harness.py)
(`check_source_precedence`) build a throwaway consumer repo with all three
sources and assert each rule above. Every one was verified by breaking the
resolver and watching the matching case fail — inverted precedence, ignored
`severity`, ignored `overrides:`, a retired practice let through, a shared
repo allowed to name an individual set, a missing source made fatal, and a
missing source degraded *silently*.

**The fixture is built in a temporary directory and never committed.** A
committed fixture holding a team- or individual-shaped tree inside Precedent
is the shortcut the plan forbids, and the leak gate refuses it by path. A
check whose setup requires switching off another check is a check that ends
up switching it off.

## What phase 3 did not do, and why it could not be done from here

**The two private sets exist but are still empty.** The plan's phase-3 item 1
is to populate `precedent-individual` and `precedent-team-maintainers` from
RepoPersonalPreferences' 46 rules — default everything to team, promote to
universal individually, move the person-specific handful to individual, and
retire `morgan-scope` and `bestpractice-wins` because the structure now says
what they said.

None of that happened, and none of it could have. Two independent reasons,
both worth writing down so the next session does not rediscover them:

- **A platform restriction.** Those repositories belong to a different owner
  than this one, and a session cannot hold both with write access at once.
  The session that populates them is a session opened against *them*, not
  against Precedent.
- **The plan forbids it anyway.** *"Nothing from an individual or team set may
  be staged on this branch at any point, even transiently"*
  ([Risks](../PRACTICE_ENGINE_PLAN.md#risks)). Every push here is publication
  into a public repository owned by someone else. Doing the split "from here"
  would mean holding private content in this working tree, which is the
  exposure the whole arrangement exists to prevent.

So phase 3 built the **receiving half**: everything in Precedent that the
private sets plug into. Populating them is work for a session opened against
those repositories, and it now has a resolver, a precedence contract, a
tested example, and a blocklist template to work against, rather than a blank
page.

**What that leaves unproven.** The precedence contract is tested against
fixture practices, not against RepoPersonalPreferences' real 46. A real
migration will find allocation questions — which rules are genuinely generic,
which are one person's — that no fixture can raise. The mechanism is tested;
the *migration* is not started.

## The example set is invented, deliberately

[examples/practice-set/](../examples/practice-set) is three practices, a
user-level config, and a README. The plan describes it as *"a one-time frozen
copy of Morgan's private practices, illustrative only, never updated from the
live individual set"*, and it is frozen and illustrative — but it is not a
copy of anything.

That is not a shortcut standing in for the real thing. **A scrubbed copy of a
real private set, published, is the disclosure the separation exists to
prevent** — scrubbing catches the words someone thought of, and a private set
is private because of the associations in it, which is exactly what a
word-list cannot see. An invented example teaches the same mechanics and
discloses nothing, so it is the better artifact and not merely the available
one.

It earns its keep by being *checked*: the harness parses all three files
against the catalogue's own parser, requires the five body sections, and
resolves the set as somebody's individual source — including asserting that
its one `overrides:` still lands on a universal practice that exists. An
example that has silently stopped matching the format is worse than no
example, because it is the first thing anyone copies.

## The leak gate's vocabulary layer, as switched on

The structural layer has gated every push since phase 2. Phase 3 adds the
half that catches private *words*, and the arrangement is the one
`scrub-gate` already uses: the blocklist lives in the private set and scans
the public tree from there, because a list of secret terms committed to a
public repo publishes the terms it guards.

```
cp templates/leak-blocklist.txt.template <your individual set>/leak-blocklist.txt
export PRECEDENT_LEAK_BLOCKLIST=<your individual set>/leak-blocklist.txt
git config precedent.requireVocabulary true
```

The third line is the one that is easy to skip and should not be. Without it
the layer **fails open**: a shell that starts without the variable prints
`PARTIAL` and exits 0, so the push goes through with only the structural
rules applied. With it, an unrun vocabulary layer is fatal.

**Three ways the gate passed on a leak, found by testing it rather than
reading it**, and fixed in the same commit that switched the layer on:

| The miss | Why it passed |
|---|---|
| A term committed in one commit and removed in a later one, in the same push | `--range` used the **net** `git diff A..B`, in which the file does not appear at all. The blob is published regardless. |
| A term in a **staged blob**, cleaned up in the working tree afterwards | Having listed the names from git, the gate then read the file **off disk**. |
| A term in a **commit message** | Never scanned. Messages are published verbatim, and a message is where a session narrates what it was working on. |

The gate now walks a range commit by commit, reads blobs out of git, and
scans messages. `check_leak_gate_fires` in the harness states fifteen cases
against a throwaway repository and asserts the exit status, because the
pre-existing check ran the gate on *this tree* and reported what it said —
which passes just as happily when the gate has stopped looking. That is why
nothing caught these.

**The automated checks that run on the server still run the structural layer
only**, permanently: they have no access to a private list. They are the
unbypassable backstop, because a `git push --no-verify` cannot skip them; the
[pre-push hook](../templates/hooks/pre-push) is the complete check, because it
is the only half that can load the words.
