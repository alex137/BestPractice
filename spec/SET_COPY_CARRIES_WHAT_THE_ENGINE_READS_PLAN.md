# A copied-in set carries every file the engine reads from it

**Status:** proposed, 2026-11-01. Written for review before it is built.
Asked for by Morgan, 2026-11-01: "Write up your plan for this root fix.
Make sure it includes mechanisms to keep this list up to date and check
it."

## The situation

A repository can take a shared practice set in two ways. It can read the
set **live**, from a clone of the set's repository beside it. Or it can keep
a **copy** of the set inside itself, under `process/<name>/`, which Update
Vendors refreshes (spec/VENDORED_SHARED_SETS.md). With a copy, the engine
treats the copy's folder as the set: every tool that reads a file "from the
source's own folder" reads it from the copy.

Some engine tools do exactly that. They read a per-set file from the set's
folder:

| File | Read by | What it carries |
|---|---|---|
| `reply_check.json` | `tools/precedent_reply_check.py` (`CONFIG_NAME`), and `tools/precedent_check.py` | the set's reply-gate requirements, enforced when a session ends a turn |
| `close_detect.json` | `tools/precedent_close_detect.py` (`CONFIG_NAME`) | the set's close-detection rules |
| `our_language.json` | `tools/precedent_vocabulary.py` (`src['path'] / 'our_language.json'`) | the set's own words for the vocabulary list |

So when a copy leaves one of these files out, that part of the set silently
stops applying in the repository holding the copy. Nothing says so.

## What happened

1. On 2026-11-01, a voice repository's Update Vendors refreshed its copy of
   the ladder set. The copy held `practices/`, `precedent-source.json` and
   `tools/`, and no `reply_check.json`.
2. Measured in that repository, with the person's individual set on: its
   sessions got **none** of the ladder set's reply-gate requirements. The
   reply gate listed the ladder's practices as reminders, and enforced
   nothing of the ladder's. After the fix below it enforces them (3 in a
   given reply; the file holds 6, some fire only at certain moments).
3. PR #1487 fixed that one file. It added a hand-kept tuple to
   `tools/checkin.py`:
   `SOURCE_CONFIGS = ('reply_check.json', 'close_detect.json')`. Its comment
   says it mirrors `precedent_reply_check.CONFIG_NAME` and
   `precedent_close_detect.CONFIG_NAME`, by hand.
4. Writing this plan, the third reader turned up. `precedent_vocabulary.py`
   reads `our_language.json` from each source's folder, and the voice
   repository's ladder copy does not have it today. The ladder set's own
   words never reach that repository's vocabulary list. **The hand-kept
   tuple was incomplete the day it was written.** That is the evidence for
   everything below.

## Why it happened: two copiers, one complete and one not

`tools/checkin.py` copies two kinds of things.

- **The universal copy** (BestPractice into a consumer's `process/upstream/`)
  works from `VENDORING_RULES`: a ruleset that decides **every** tracked
  file, ship or stay, with a reason. A precedent_check check,
  `vendoring-decided` (tools/precedent_check.py), refuses any tracked file
  no rule decides (Morgan, 2026-09-30: "make sure that *every new file* is
  evaluated to see if it should be vendored in or not"). `reply_check.json`
  got its rule there on 2026-09-30.
- **The shared-set copy** (a set into `process/<name>/`) works from an
  allowlist built up piece by piece in `_select_source`:
  - `practices/` and `precedent-source.json`;
  - the files the set's rules name (`_files_rules_name`);
  - the sets it `carries`;
  - its `exports`;
  - and now `SOURCE_CONFIGS`.

  `VENDORING_RULES` explicitly does not apply to it (the `_in_copy`
  docstring says so). Nothing decides the rest of a set's files. And
  nothing ties the list to what the engine actually reads.

So when an engine tool started reading a new file from each source's
folder, the universal copier was told and the shared-set copier was not.
No check compares the copied set against the engine's readers. It is the
same shape as the 2026-10-19 incident that `_files_rules_name` answered:
"the copy's rules are in force with their checks gone".

## The options, and what attacking each found

**A. Keep adding names to `SOURCE_CONFIGS` by hand.** Today's state. It has
already failed: `our_language.json` was missing the day the tuple was
written. A list kept beside the readers, not by them, drifts. Rejected as
the fix; kept only as the bridge until B lands.

**B. One registry of per-set files, owned by the engine and read by every
reader.** A single table, `SET_FILES`, in a module every reader already
imports (`tools/precedent_resolve.py`, which owns source resolution). Each
entry: the file name, the tool that reads it, and why a copy must carry it.
Each reader takes its name from the registry instead of its own string
(`CONFIG_NAME = precedent_resolve.set_file('reply_check')`). `checkin.py`
copies every registered file the set has.

- *Attack: a new reader writes `src['path'] / 'new.json'` and never touches
  the registry.* Nothing in B alone catches that. Answered by C.
- *Attack: the registry lists a file a set does not have.* Harmless: the
  copier copies what exists. A set without `close_detect.json` loses nothing.
- *Attack: a files-only (`exports_only`) copy.* Its rules are deliberately
  not in force, so registered files stay out, as today. Unchanged, and
  tested.

**C. A check that finds every read from a source's folder, and refuses an
unregistered one.** A precedent_check check, `set-file-registered`, run in
BestPractice. It scans `tools/*.py` for a file path built on a source's
folder: `src['path']`, `s['path']`, `source['path']`, `entry['path']`, a
`_declared_path(...)` result, or a `root` handed in as a source root,
joined with a string literal or a `CONFIG_NAME`-style constant. Every file
name found must be registered in `SET_FILES`. One that isn't is a finding
that names the file, the line, and the registry to add it to.

- *Attack: a static scan misses a dynamic read* (a name built at run time, a
  helper three calls away). Answered two ways. First, readers go through
  one helper, `precedent_resolve.read_set_file(src, key)`, which refuses an
  unregistered key at run time. The scan then also flags any raw
  `['path']) /` join outside that helper, so the only sanctioned route is
  the checked one. Second, D catches what slips past at the consumer.
- *Attack: false positives on joins that are not per-set files*
  (`src['path'] / 'practices'`). The scan registers the known folder reads
  too (`practices/`, `tools/checks/`), each marked folder; a finding names
  the line, so a real false positive is one allow line with a reason, the
  repository's usual pattern.

**D. Update Vendors verifies the copy is complete, every time.** After
`checkin.py` copies a set, compare the copy with the source clone. Every
registered file the source has must be in the copy, byte for byte. A
missing or different one makes the update LEFT FOR YOU, not DONE, naming
the file and what it carries. The same comparison runs as a consumer-side
check, `set-copy-complete`, in the consumer's own precedent_check. So a copy
made by an older engine, or edited by hand, shows up at the next check, not
only at the next update.

- *Attack: the consumer has no source clone in a fresh container.* The
  check then compares against the copy's own manifest record of what was
  copied (the manifest gains a `set_files` list at copy time), and says it
  could not compare against the source. A could-not-verify, never a pass.

**E. Every top-level file in a set is decided, ship or stay.** The set-side
twin of `vendoring-decided`. A set's `precedent-source.json` already lists
`code`, `exports` and `carries`. The new check, `set-file-decided`, runs in
a practice set and refuses a top-level file that is none of these:
- registered in `SET_FILES`;
- `practices/` or `precedent-source.json`;
- named by a rule;
- listed under a new `stays` key, with a reason (`approvers.json`: this
  repository's own reviewers; `precedent.json`: this repository's own
  install).

This is what catches a set author adding a new kind of file that a copy
ought to carry.

- *Attack: churn for set authors.* Today each set has about four top-level
  files beyond its practices (ladder: `approvers.json`,
  `our_language.json`, `precedent.json`, `reply_check.json`), and each is
  decided once. The check names the file and the two ways to decide it.

**Rejected: copy the set's whole repository.** It brings the set's own
`precedent.json`, `approvers.json`, `AGENTS.md`, its engine copy under
`tools/`, and any copies the set itself holds. The last is exactly the
nesting the next section forbids.

## The second fix: a copy never carries a copy

Morgan, 2026-11-01: "when [a voice repository] itself is vendored in elsewhere, I
want to make sure that the ladder set and BestPractice vendored in there are
NOT vendored in again within the vendored in [voice repository]".

**What holds today, checked.**
- A voice repository's set is its `voice-set/` folder (`set_root`), so its
  own `process/` copies sit outside what a copy takes.
- `_refuse_set_holding_copies` refuses a set whose `practices/` holds rules
  an install copied in from other sources. So pointing a copy at a voice
  repository's root, which holds such copies, is refused.
- A real downstream copy (a private planning repository's `content/voice-pack/`) holds a
  README, the unified prompt and the essentials, and nothing else.

**The gap.** Nothing stops a set from listing, among its `exports`, `code`
or `carries`, a folder that is itself another set's copy, like
`process/precedent-shared-ladder/`. The copy would then bring a nested,
frozen second copy of that set, at the carrier's level.

**The fix.** In `_select_source`, before copying, refuse any `exports`,
`code` or `carries` entry that:
- is, or is inside, a path the carrier's own `precedent.json` declares as a
  source (a vendored copy); or
- holds a `manifest*.json`, a `MANIFEST.json` recording installed copies, or
  a `tools/ENGINE_MANIFEST.json`.

`carries` stays allowed only for an entry that names a set the carrier
writes itself: it has its own `precedent-source.json` and is not one of the
carrier's declared sources. The refusal names the entry and says why.
Nothing is copied.

## Keeping the list up to date, and checking it

| Mechanism | Runs in | Catches |
|---|---|---|
| `SET_FILES` registry, read by every reader (B) | BestPractice engine | two lists drifting apart: there is one |
| `set-file-registered` check (C) | BestPractice, every push check | a new reader of a per-set file that skipped the registry |
| `read_set_file` refuses an unregistered key (C) | everywhere, at run time | a dynamic read the scan missed |
| copy-completeness at Update Vendors (D) | each consumer's update | a copy missing or differing from a registered file: not DONE |
| `set-copy-complete` check (D) | each consumer's precedent_check | an old or hand-edited copy, between updates |
| `set-file-decided` check (E) | each practice set's own check | a new top-level file in a set nobody decided |
| nested-copy refusal | every Update Vendors that copies a set | a copy that would carry another set's copy |

Each check gets harness cases that fail on today's code and pass after:
- a reader added with an unregistered name;
- a copy missing `our_language.json`;
- an undecided top-level file in a set;
- an export that points into the carrier's `process/<set>/`;
- a files-only copy that still takes nothing beyond its exports.

## What this ships, and how it reaches other repositories

Everything here is engine code (`tools/checkin.py`,
`tools/precedent_resolve.py`, the readers, `tools/precedent_check.py`)
plus a `stays` key that practice sets declare in their own
`precedent-source.json`. It reaches every repository by Update Vendors, as
usual. The first update after it lands fills each existing copy with the
files it lacks: today, `our_language.json` in every full copy of the
ladder set. Each practice set (the ladder and writing sets) needs one
commit declaring its `stays` files, or `set-file-decided` refuses at its
next check. Those two commits go in the same sitting as the engine change.

## The first Update Vendors after this lands, in every repository

Morgan, 2026-11-01: "make sure your plan includes a vendor updates plan so
when people update their vendors for the first time it does this
smoothly".

**The rule for the transition:** a new check never turns a repository red
that has not yet had the chance to take the fix. A repository is judged by
the new rules only once an Update Vendors with the new engine has run in
it. Until then, a finding is an advisory that says which command fixes it.

**What the first update does, by kind of repository:**

| Repository | What the first update does | What the person sees |
|---|---|---|
| A consumer holding a full copy of a set (a voice repository and its ladder and writing copies) | Copies each registered file the set has and the copy lacks. Records the list it copied in the copy's manifest (`set_files`), so later checks compare against it. | One line per filled file, in the update's summary: "copy of precedent-shared-ladder: added our_language.json, the set's own words now reach this repository's vocabulary". No question, nothing LEFT FOR YOU. Then DONE. |
| A consumer holding only a files-only copy | Nothing changes. Registered files stay out by design. | Nothing. |
| A consumer reading its sets live (a sibling clone) | Nothing to copy. The readers now take their names from the registry. | Nothing. |
| A practice set (ladder, writing, individual) | Its engine refresh brings `set-file-decided`. The engine already knows the files every set repository has for itself (`precedent.json`, `approvers.json`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `MAP.md`, `GLOSSARY.md`), so those need no `stays` line. Only a file the engine does not know needs a decision. | Only a file nobody can decide automatically, listed under LEFT FOR YOU with the two lines to choose from: ship it (register it) or keep it home (`stays`, with a reason). Today that list should be empty for the ladder and writing sets; the build checks it before landing. |
| BestPractice itself | Not a consumer; the new checks run in its own push check from the commit that adds them. | The usual. |

**Advisory until the first update, a finding after.** `set-copy-complete`
reads the copy's manifest:
- No `set_files` record means the copy was made by an engine from before
  this change. The check then gives an advisory: "this copy predates the
  set-files registry; the next Update Vendors fills it", and never a
  violation. So a consumer's `main` does not go red the day BestPractice's
  `main` moves.
- Once a `set_files` record exists, a missing or differing registered file
  is a real finding.

**An existing nested copy is reported, never a stop.** The refusal of
nested copies blocks a new one. If an existing copy already holds one, the
first update lists it under LEFT FOR YOU instead of failing: the path, the
set it duplicates, and the `precedent_decommission.py` line that removes
it. Then it carries on. None is known today; the build's rehearsal
confirms that on the repositories at hand.

**The order the updates run in.**
1. BestPractice lands and passes GitHub's test.
2. The practice sets update next: individual, ladder, writing. Any `stays`
   decision they need is made in that sitting.
3. Then the consumers, sets before the repositories that copy them. Update
   All Vendors already orders this from the declared repository links
   (commit 8c50ec609, "updates run in source order").

A consumer updated before its sets have updated still finishes DONE: it
copies what the set holds today, and the next update tops it up.

**The announcement.** The update's summary carries one line the first time
a repository takes this engine. It says that copies of shared sets now
carry every file the engine reads from them, and lists what was added. The
change is also announced the way Update Vendors changes are announced
(`check_update_vendors_change_is_announced` in the harness).

**A rehearsal before landing.** The build runs the new Update Vendors on
scratch copies of the repositories at hand: a voice repository with full
copies of the ladder and writing sets, a project, and the ladder and
writing sets themselves. It confirms:
- each reports DONE;
- the filled files are the expected ones (`our_language.json` in the voice
  repository's ladder copy);
- no new check turns any of them red;
- a second update right after reports nothing new.

The rehearsal's output goes in the pull request.

## Open questions for review

1. Is `precedent_resolve.py` the right home for `SET_FILES`, or should it be
   its own small module, so the readers import nothing heavier than a
   table? (needs: decision -- the reviewing session, then Morgan if it is a close call)
2. Should `set-copy-complete` compare bytes, or only presence? Bytes catches
   a hand edit; presence avoids a finding while an update is mid-flight. (needs: decision -- the reviewing session, then Morgan if it is a close call)
3. Is refusing an undecided top-level set file too strict for a set author
   working on a branch? An alternative is an advisory finding on a branch
   and a refusal only at the Produce. (needs: decision -- the reviewing session, then Morgan if it is a close call)
