---
title:         Build-environment Gotchas — the Live Text
kind:          record
status:        live
opened:        2026-09-13
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       Every live gotcha in full. AGENTS.md carries the one-line symptom index; the story is here.
---

# Build-environment Gotchas — the Live Text

**These are the traps that can still bite you today, each with the story of
what failed.** [AGENTS.md](../AGENTS.md)'s gotchas section carries the same 36
entries as **one line each** — the symptom, and a link to the entry here. That
split is the whole point: a session pays for the index before it does anything,
and pays for the story only when a symptom matches.

**The story is the payload, not decoration.**
[environment-gotchas](../practices/environment-gotchas.md) says why: a fix with
no account of what failed is a fact you cannot judge, and the next session
undoes it the moment it looks wrong. So the entries below are unabridged —
moving them out of the always-loaded file changed the loading, never the text.

**Three files, and they are not the same thing.** This one holds what is
**live**. [record/GOTCHAS_ARCHIVE.md](GOTCHAS_ARCHIVE.md) holds what was
**shortened or retired**, with the verdict that put it there — read it when an
entry here points at it for the history. [AGENTS.md](../AGENTS.md) holds the
index a session actually loads.

**If you arrived from a symptom in the index:** the entry below is the whole of
it. Check any date in it against the tree before acting — several of these
describe mechanisms that have since been fixed, and say so.


## 1. <a id="g1"></a>pip install cmarkgfm, or tools/doc_lint.py's strikethrough check silently stops ...

**`pip install cmarkgfm`, or [tools/doc_lint.py](../tools/doc_lint.py)'s
strikethrough check silently stops running.** Without it the check does not
fail — it prints a one-line notice and scans for everything else, so a
document that renders an unintended `<del>` on GitHub passes the gate.
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) installs it,
but only when `CLAUDE_CODE_REMOTE=true`; a local shell has to do it.


## 2. <a id="g2"></a>A git helper that returns stdout and drops the exit code will hand you a confident ...

**A git helper that returns stdout and drops the exit code will hand you a
confident wrong answer — this is the most-repeated bug in the project.** Two
shapes, both live: `git rev-parse <missing-ref>` exits non-zero but *prints
the ref you asked for*, so `_git(...'rev-parse', ref) or <fallback>` never
falls back — it carries the string `origin/precedent-beta-v01` forward as a
hash, which reached continuous integration once as a 12-char truncation of a
ref name. And `git show <commit>:<path>` exits 128 with **empty stdout** for
two unrelated situations — the commit is not in this clone, or the path did
not exist at that commit — so a caller reading stdout alone answers an
unanswerable question. That one reported 69 lines of a vendored tree as LOST
on 2026-09-08, disprovable only by extracting both trees and diffing them by
hand. **Use `rev-parse --verify --quiet`, and consult the return code whenever
a command can fail for two different reasons.** Found in five separate tools
so far; the inventory is in the archive. Note the trigger for the first shape:
a *non-repo* prints nothing, so the plain form looks correct for years — it
only echoes on an unborn `HEAD` or a missing ref.

**A third shape, and it defeats the fix this entry recommends:
`rev-parse --verify --quiet` exits 0 and echoes back ANY well-formed 40-hex
string, present in the clone or not.** `--verify` checks that the argument
names a single revision — a full hash always does — never that the object
exists. Found 2026-09-08 by a negative-control fixture for
[tools/precedent_upstream_check.py](../tools/precedent_upstream_check.py): a
watermark pointing at 40 zeroes read as *present*, so the guard meant to say
"that commit is not in this shallow clone" never fired and the notice
announced a change it could not list. Ask the object database instead —
`git cat-file -e <sha>^{commit}`. `--verify` remains right for a *name*
(`origin/main`, `HEAD`), which is what the two shapes above are about.


## 3. <a id="g3"></a>A repository attached mid-session clones single-branch, so every branch you create ...

**A repository attached mid-session clones single-branch, so every branch you
create there reads as "unpushed" forever — including to a Stop hook that then
blocks the turn.** `add_repo` hands you a `git clone --depth 1` whose only
refspec is `+refs/heads/main:refs/remotes/origin/main`. The push genuinely
succeeds, but no `origin/<branch>` ref is ever written, so `git rev-list
origin/<branch>..HEAD` cannot resolve. **Pushing again — the honest-looking
remedy — changes nothing, because the push was never the problem.** A second
trap sits on top: `add_repo`'s clone URL is lowercased, so GitHub answers
`remote: This repository moved`, which reads like the cause and is not.
Confirm with `git ls-remote origin refs/heads/<branch>` — that talks to the
server and ignores local refs — then repair rather than re-push: `git config
--unset-all remote.origin.fetch`, `git config --add remote.origin.fetch
'+refs/heads/*:refs/remotes/origin/*'`, a bounded `git fetch --depth=50 origin
<branch>`, and `git branch --set-upstream-to=origin/<branch>`. The refspec
half self-applies at session start now — but only where the hook runs, which
is not an attached sibling (see below). The clone-URL capitalization half is
never automated: nothing local knows the canonical spelling, so that stays a
manual `git remote set-url`.


## 4. <a id="g4"></a>git clone with no --branch asks the SERVER which branch to check out, and the ...

**`git clone` with no `--branch` asks the SERVER which branch to check out,
and the answer is a setting on a web page that nothing in this repository can
see.** The remote's `HEAD` symref is whatever the repository's default branch
is set to, and git follows it silently. 2026-09-09: two practice-source
repositories had it pointed at a feature branch, so every session-start clone
landed on an older tree and a plain sync would have overwritten newer
committed text — exit 0, no warning. **The consuming repo had never been
stale; the clone had been pointed somewhere else**, and `git pull --ff-only`
follows whatever branch the checkout is on, so it stayed wrong every session
afterwards. **The lesson that outlived the fix: when a rule forbids asking a
question, check whether something else is asking it for you.** The guard
against this reads Python, so it never saw a `git clone` making the same
inference on our behalf — the class is open even though this instance is shut.
Pinned since 2026-09-10 in
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py); a
clone you run by hand is still yours to branch explicitly. Full incident:
entry 36.


## 5. <a id="g5"></a>A stale checkout is indistinguishable from missing work, and the guard cannot save ...

**A stale checkout is indistinguishable from missing work, and the guard
cannot save the sessions that most need it.** A session once came up 366
commits behind and concluded that files which had landed days earlier "did not
exist"; another had a local branch sharing **zero** commits with origin. `git
status` says "up to date with origin" in both cases, because it compares
against a remote-tracking ref nothing has refreshed.
[.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh) now
**repairs** rather than warns — on a clean tree that is strictly behind it
fast-forwards, which makes the harness re-read the instruction files — and
warns only for diverged, no-shared-history and dirty-tree states, because a
hook that discards work is worse than any stale checkout. **What no guard
covers, and why this stays here: it does not run for a repo attached
mid-session, or when the harness rooted the session one directory above the
repo.** So before concluding anything is missing or unfinished, run `git fetch
origin <branch>` and `git rev-list --count HEAD..origin/<branch>` yourself.
Three incidents and the guard's full design history are in the archive.


## 6. <a id="g6"></a>This repo is normally cloned --depth 1, and several tools degrade rather than fail ...

**This repo is normally cloned `--depth 1`, and several tools degrade rather
than fail on that.** [tools/behavioral_replay.py](../tools/behavioral_replay.py)
divided by the replayable-commit count and took the whole harness down with a
`ZeroDivisionError` on a one-commit clone — the exact environment a fresh
session starts in. It now reports `REPLAY_STATUS: DEGRADED` instead. On the
same clone `origin/main` does not exist, so doc_lint's
changed-vs-default-branch scope quietly becomes changed-vs-`HEAD`: it checks
your uncommitted files and nothing else. Fix both with a bounded `git fetch
--depth=500 origin <branch>`; some git policy hooks block `--unshallow`, and a
bounded fetch works either way.


## 7. <a id="g7"></a>git clone --depth 1 /some/path is ignored; git only honours --depth over a ...

**`git clone --depth 1 /some/path` is ignored; git only honours `--depth` over
a transport.** A phase-2 smoke test believed it was exercising a shallow clone
for an hour and was not — the bug it was written to catch was still there. Use
`file:///some/path` to force a genuinely shallow local clone. (Used again
2026-09-08 to build the fixture that proves the carry check refuses rather
than inventing lost content.)


## 8. <a id="g8"></a>A scope: 'tree' check in tools/precedent_check.py can silently report a false pass ...

**A `scope: 'tree'` check in `tools/precedent_check.py` can silently report a
false *pass* on an under-fetched local clone, not just degrade loudly like the
two entries above.** `parallel-artifact-ledger` walks `git log --no-merges --
<member-dir>` and fails on any commit whose hash isn't in
`templates/harness/LEDGER.md`. 2026-09-05: a local run reported `0 violated`,
but GitHub Actions' checkout of the same commit reported a real violation
twice — the local clone's history simply didn't reach back far enough for `git
log` to find the commit at all, so **an empty result read as "clean," not as
"couldn't check."** `git fetch --depth=1000 origin <branch>` (or deeper — this
check needs the *entire* history of the directories it walks) before trusting
a clean local run of any `scope: 'tree'` check.


**Second cause of the same false pass, 2026-09-14: running the deep check
BEFORE committing.** `parallel-artifact-ledger` walks `git log` for each member
directory and fails on a commit whose hash no `LEDGER.md` row references. An
uncommitted change has no hash, so the check has nothing to find and reports
`0 violated` — a pass it is structurally incapable of withholding. A session
ran all five gates clean against a dirty tree, committed, pushed, and CI failed
on the one violation the local run could not have seen. AGENTS.md already says
which moment each level gates — light check gates a commit, deep check gates a
**push** — and this is exactly what that distinction is for: a deep check run
before the commit exists is measuring a different tree from the one CI reads.
Run it between `git commit` and `git push`, never before both.

## 9. <a id="g9"></a>The leak gate's vocabulary layer fails open unless you also set the git config.

**The leak gate's vocabulary layer fails open unless you also set the git
config.** `export PRECEDENT_LEAK_BLOCKLIST=<a path OUTSIDE this repo>` is half
of it; without `git config precedent.requireVocabulary true` a shell that
starts without the variable prints `PARTIAL`, exits 0, and the push goes
through with only the structural rules applied. Every push here is publication
into a public repository, so the half-configured state is the dangerous one.
See `python3 tools/leak_gate.py --explain`. **Narrowed 2026-09-12**: with the
variable unset the gate now reads `leak-blocklist.txt` from the individual set
`~/.config/precedent/config.json` names, so the common case — a list sitting
where INSTALL.md section 8 puts it, in a shell nobody exported anything in —
runs the full layer instead of reporting `PARTIAL`. The trap that remains is
the one this entry is really about: a list somewhere ELSE, with neither the
variable nor the git config set, still fails open and still looks like a pass.


## 10. <a id="g10"></a>A bare python3 tools/leak_gate.py refuses when a private source RESOLVED and no ...

**A bare `python3 tools/leak_gate.py` refuses when a private source RESOLVED
and no blocklist is set — and allows, loudly, when the private sources could
not be attached at all.** The distinction is the whole rule and it was got
wrong once, in both directions, on 2026-09-08. First the gate reported PARTIAL
and **exit 0** for a session that could attach neither private source; it
pushed into a public repository with only the structural rules applied and
reported it afterwards. So the requirement was derived from `precedent.json`
DECLARING a private source. **That refused every session that could not attach
one** — a live, intermittent condition here — and within the hour it blocked a
real session out of pushing at all, whose commit then "dies with the
container": `repo-is-memory` losing outright, in exchange for no safety. **The
threat model was backwards.** Private vocabulary reaches a session by the
session READING the private sources' text. A session that could not attach
them never read a word and has nothing from them to leak; the one that DID
attach them is the one writing to a public tree with private text in context.
So **resolution, not declaration, requires the list**. Practically: if the
sources resolved, export `PRECEDENT_LEAK_BLOCKLIST` — you have the repository,
so you have the file. If they did not resolve, the push goes through and the
gate says out loud what it could not cover: a private term that reached the
session some other way, most plausibly the person's own messages. **Say that
in the reply.** A caller that only ever wants the structural half says so by
name with `--structural-only`; CI and `verify_harness.py` both pass it, and
both call themselves structural.


## 11. <a id="g11"></a>Setting git config precedent.requireVocabulary true to satisfy the leak gate makes ...

**Setting `git config precedent.requireVocabulary true` to satisfy the leak
gate makes `verify_harness.py` fail two of its own leak-gate checks.** The two
gates want opposite environments and neither says so, which is why it costs an
hour every time. Run them separately: `python3 tools/leak_gate.py` with
`PRECEDENT_LEAK_BLOCKLIST` exported, and `env -u PRECEDENT_LEAK_BLOCKLIST
python3 tools/verify_harness.py` with the git config unset. **Unset the config
when you are done** rather than leaving it on the clone — a later session
running the harness hits this again with no idea why.


## 12. <a id="g12"></a>On a shallow clone, git merge-base between two different branches can exit 1 ("no ...

**On a shallow clone, `git merge-base` between two *different* branches can
exit 1 ("no common ancestor") even when the branches genuinely share history —
and that false negative reads exactly like a destructive force-push.** On
2026-09-06 a session nearly asked the user to confirm a branch rewrite that
had never happened. `git merge-base <A> origin/main` and `git merge-base <B>
origin/main` each resolved fine meanwhile: the shallow fetch simply didn't
reach the real common ancestor of `<A>` and `<B>`. Exit 1 is not evidence of a
rewritten branch — fetch deeper and recheck before concluding anything about
two branches' relationship.


## 13. <a id="g13"></a>git log --format=%P silently reports no parents at all for a commit sitting at a ...

**`git log --format=%P` silently reports no parents at all for a commit
sitting at a shallow clone's boundary, even when it really has two.** A
`checked_by` script that told merge commits from ordinary ones worked
perfectly against a full clone, then misclassified the exact boundary commit
the moment it ran against a fresh `--depth 1` clone of the same repo —
reproduced directly, not suspected. Git's pretty-printers respect the shallow
graft; the commit object's own header still records both parents. `git
cat-file -p <sha>` reads that header and is unaffected — count lines starting
with `parent ` instead of parsing `%P`.


## 14. <a id="g14"></a>A consuming repo's own mechanical check against materialized ...

**A consuming repo's own mechanical check against materialized
`tools/checks/`/`practices/` output cannot resolve sources live and trust
every one it lists.** A repo-local source's check script belongs under that
source's own declared `path` (`local/tools/checks/`), never directly in the
consuming repo's `tools/checks/` — that is `precedent_materialize.py`'s
**output** directory, deleted and rewritten on every sync, so a hand-added
file there survives until the next one. A dependent repo shipped exactly this
check resolving sources live; it passed locally, then failed its own CI on
`main`, flagging every script sourced from its team and individual sources.
**A team source is a sibling clone outside the repo and an individual source
resolves via a private user-level config — neither exists in a bare CI
checkout, so "this source didn't resolve here" is not evidence of an orphan.**
Attribute by the committed `MANIFEST.json`'s own `checks` list instead: a file
with no entry there is the real signature of a hand-dropped orphan; a recorded
file whose source is unreachable is skipped, never failed.


## 15. <a id="g15"></a>A repo attached mid-session never runs its own SessionStart hook, so every ...

**A repo attached mid-session never runs its own SessionStart hook, so every
environment guarantee that hook provides is silently absent while you work in
it.** SessionStart hooks fire for the session's *primary* repo only. A sibling
attached with `add_repo` is just a directory on disk: its hook is never
executed, no matter that it is committed, executable and correct. 2026-09-06:
`verify_harness.py` reported a broken `doc_html.py` twice over, and both were
the same missing module the hook installs on line 13. **The failure reads like
a broken tool and is an unrun hook**, so the reflex to go debug the tool is
wasted. `pip install cmarkgfm markdown` by hand once per session you work in
an attached sibling — the harness went from `1 failed` to `0 failed` with no
code change. Treat every entry here that says "the session-start hook does
this" as **not** done when you arrived as a sibling. **One guarantee has an
environment-level route out of this since 2026-09-11, and only one**: the
freshness guard reads `PRECEDENT_FRESHNESS_ALSO` (`;`-separated `<path>=<base
branch>`), so a session can have attached repositories checked even though
their own hooks never fire — an environment variable follows a session into
every repository it touches, the same reasoning as `PRECEDENT_COMMIT_*` for
identity. **Write the path as `~/name`, never spelled out.** An individual
practice source lives at `$HOME/precedent-individual` and `$HOME` is `/root`
on some containers and `/home/user` on others, so an absolute path written on
one names nothing on the next — and a dead entry is skipped rather than
blocked on, deliberately, so the variable goes on reading as coverage while
covering nothing. This environment's own entry did exactly that from the day
it was set until 2026-09-11, naming `/home/user/precedent-individual` while
the clone sat at `/root/precedent-individual`. The guard expands `~`, `$HOME`
and `$CLAUDE_PROJECT_DIR` now, so one value is correct everywhere, and
`python3 tools/precedent_session_check.py` has a row that names any entry
still resolving to nothing and prints the value to set instead. Nothing else
in this entry is covered: the `pip install`, the path-trigger channel and the
rest still need doing by hand.


## 16. <a id="g16"></a>A merge conflict in .claude/hooks/freshness-guard.sh locks the session out of every ...

**A merge conflict in `.claude/hooks/freshness-guard.sh` locks the session out
of every tool that could repair it, and `git` being exempt does not help.**
2026-09-11: merging `origin/precedent-beta-v01` into a branch that had also
touched the guard left conflict markers in the live PreToolUse hook. Bash
aborts on the parse error before reaching either the git exemption or the
once-per-session sentinel, and exits 2 — which is exactly how a PreToolUse
hook refuses a call. The matcher is `Edit|Write|NotebookEdit|Bash`, so **Edit,
Write and Bash were all refused at once**, and the guard's own fail-open path
does not cover this: it is written for "cannot read the payload", not for
"will not parse". **The way out is a tool the matcher does not name.**
`Monitor` runs a shell command under a different tool name, so it is not
matched: `Monitor(command: "cd <repo> && git checkout --ours
.claude/hooks/freshness-guard.sh")` restored a parseable file and every tool
came back. A subagent is NOT a way out — it inherits the same project hooks.
**Prefer avoiding it**: when a merge is going to touch the guard, expect this
and resolve that file first. Nothing detects it in advance, because the hook
is fine right up until the merge writes the markers.


## 17. <a id="g17"></a>The session's PRIMARY repo does not run its SessionStart hooks either, when the ...

**The session's PRIMARY repo does not run its SessionStart hooks either, when
the harness rooted the session one directory ABOVE it — and this project's own
required layout is what causes that.** Four Precedent repos side by side under
`/home/user` is what a team source needs, since it resolves as a sibling
clone; the harness then sets the session root to that parent, every hook path
written as `$CLAUDE_PROJECT_DIR/.claude/hooks/…` resolves to nothing, and **a
hook whose path does not exist is not an error anybody sees.** On 2026-09-08
that silently cost the commit identity, the global backstop, the freshness
guard, the `pip install`, the path-trigger channel — and
`.precedent/SESSION_PRACTICES.md`, the only route by which private team and
individual practices reach a session at all. **Do not diagnose this from
`env`** — `CLAUDE_PROJECT_DIR` is usually not set in a tool shell, so reading
it proves nothing either way. Test the effects:
[tools/precedent_session_check.py](../tools/precedent_session_check.py) checks
each guarantee by what it left behind, and `--apply` runs the three hooks by
hand. It cannot itself be a hook, for the obvious reason.


## 18. <a id="g18"></a>Your commits are authored by the bot because the harness sets that identity in ...

**Your commits are authored by the bot because the harness sets that identity
in git's GLOBAL config AND in every clone's LOCAL config — so a global-only
fix is silently overridden.** Measured 2026-09-11: `user.name=Claude`,
`user.email=noreply@anthropic.com` in `--global` and in both clones'
`--local`, and no backstop installed to refuse any of it. The cause is the
entry above — a session rooted one directory up, so `commit-identity.sh` never
ran — but the SYMPTOM reads as a git-config problem, and the config it reads
as is one somebody already set on purpose. **The cost is that a wrong-author
commit cannot be repaired after it merges** without rewriting `main`, which is
why `fab8d42` and two entries in the individual set's
`grandfathered_commit_shas` are permanent. **The remedy is one line, and it is
not `git config`:** ``` bash .claude/hooks/commit-identity.sh ``` It sets the
local identity, the GLOBAL one (so a clone attached later inherits a person),
repoints `/etc/localtime`, and installs the global `core.hooksPath` backstop
that refuses a bot-authored commit everywhere.
**`PRECEDENT_COMMIT_NAME`/`_EMAIL`/`_TZ` in the environment is what keeps it
fixed**, and two things that used to undo it are closed at that cause: a
harness run repointing the container's own `/etc/localtime`, and the hook's
fallback rung writing a timezone (TZ) value, `TZ=America/New_York`, into
untracked `.claude/settings.local.json`, where the harness reads it before
hooks run.
Both are archived in full as entry 33. Verified 2026-09-11 in a scrubbed HOME
with no private source, no credential and the bot identity preloaded: the hook
resolved at rung 1 and set the person and the declared offset, never reaching
the fallback. **Where those variables are absent it still bites**, so verify
by effect, never by reading the config you just wrote: `env -u GIT_AUTHOR_NAME
-u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT` must name the person and
the declared offset. **The trap that wastes the time is still live.** The
harness's own Stop hook flags commits whose committer is not
`noreply@anthropic.com` and asks you to `--amend --reset-author` onto exactly
the bot account the individual set's own `commit-author` practice refuses and
its own mechanical check fails on. Neither file is in this repository, which
is why neither is linked here. Following it recreates the violation this
repository spent a day fixing. **The repository's gate wins over generic
harness guidance**; say so and leave the commit alone.


## 19. <a id="g19"></a>The absence of .claude/hooks/ is NOT evidence that a repo's hooks are missing — ...

**The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are
missing — resolve the paths its settings.json actually declares.** A set can
wire its hooks to a tracked `bootstrap/` directory on purpose, and from a
directory listing that looks identical to a set whose hooks were never
installed. 2026-09-09: a session called four working hooks silently dead on
exactly that reading. **Both halves are mechanical now** — `python3
tools/precedent_check.py --only declared-hooks-exist` resolves every declared
`$CLAUDE_PROJECT_DIR` hook path and fails on one that is missing or not
executable, and
[tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py) does
the same per attached source. Full story:
[record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) entry 37.


## 20. <a id="g20"></a>A source set's hooks drift after installation and nothing has ever refreshed them — ...

**A source set's hooks drift after installation and nothing has ever refreshed
them — there was an install path and no repair path.** Measured 2026-09-09
across five real private sets: one carries a `freshness-guard.sh` three
thousand bytes shorter than canonical, supporting only `session-start` and
`pre-write` with no user-prompt mode (its settings.json wires no
`UserPromptSubmit` to match, so it is self-consistent, just older), and
`commit-identity.sh` is one version behind in **all five**, which is what
uniform drift looks like when canonical moved on after installation.
[tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
installs both hooks when a set is created and nothing revisits them; its
settings.json is also written only `if not settings.exists()`, so
bootstrapping INTO a directory that already has one — which is what a
migration is — yields hooks without wiring, or wiring without hooks. `python3
tools/precedent_refresh_sources.py --apply` now restores a
declared-but-missing hook, **independently of engine staleness**, since the
two go stale independently. Bringing a drifted-but-present hook up to
canonical is still a person's call, and [TODO.md's `source-hook-drift`
item](../TODO.md#source-hook-drift) holds it.


## 21. <a id="g21"></a>A refusal that names a remedy which cannot work is the moment to ask what the guard ...

**A refusal that names a remedy which cannot work is the moment to ask what
the guard actually measured, not to disable it.** The freshness guard used to
refuse the first write of every newly created branch and name `git fetch
origin <branch>` — impossible against a ref that does not exist — so the only
way forward a session found was `git config precedent.freshness.override
true`, which switches freshness checking off for that checkout permanently,
including the stale-base check that catches the single most expensive failure
class in this file. Fixed 2026-09-11 in both copies here: `git ls-remote
--exit-code --heads origin <branch>` separates "origin has no such branch"
from "origin could not be reached", and only the branch-absent case is waved
through, with the base-branch check still running on it. **An unreachable
origin still blocks, deliberately.** The override is still on offer in every
block message, which is why the shape above outlived the fix. Entries 30 and
35.


## 22. <a id="g22"></a>Something can move this checkout off your working branch mid-session, and the cause ...

**Something can move this checkout off your working branch mid-session, and
the cause is NOT known — treat a silently-vanished edit as this before you
re-derive it.** 2026-09-08, three minutes after a commit, the reflog recorded
`checkout: moving from claude/deep-review-… to precedent-beta-v01` followed by
a fast-forward pull. Nobody asked for either. The commit survived on the
abandoned branch, but twenty minutes of edits landed on the wrong one, and
**the only symptom was a function that had silently stopped existing** — which
reads exactly like a bad edit and is really a branch switch. `git status` was
clean throughout, as it always is for a checkout. **Three suspects are ruled
out by replay rather than reasoning**: `precedent_vendor_engine.py seed`,
`precedent_refresh_sources.py --apply` and `checkin.py fresh` were each run
against a throwaway clone on a feature branch and none moved `HEAD`. It is
also **not** the `checkin.py update` incident returning — that one is fixed
and verified (archived entry 4). Whatever does it is outside this repo's
tools; do not assume it is fixed. **Detection is the whole remedy available**:
[tools/precedent_session_check.py](../tools/precedent_session_check.py) stamps
the branch on its first run and compares on every later one. When it fires the
work is **not lost** — `git reflog` lists the commit, `git checkout` returns
to it, `git cherry-pick` recovers anything committed after.


## 23. <a id="g23"></a>A verify_harness.py fixture that builds an "absent credential" scenario inherits ...

**A `verify_harness.py` fixture that builds an "absent credential" scenario
inherits the container's real one, and so asserts the opposite of what it
ran.** Three separate variables have done it — `PRECEDENT_GIT_TOKEN`,
`PRECEDENT_SOURCE_BASE_URL` and `PRECEDENT_FRESHNESS_ALSO` — and the diagnosis
fails in the expensive direction each time: the failure reads as *missing*
access you in fact have, or as a guard blocking on a repository the fixture
never created. **Separate the two by re-running with the variables unset** —
failures that *disappear* were inheritance, not absence. All three are
scrubbed at the head of [tools/verify_harness.py](../tools/verify_harness.py)
now, and `check_fixtures_own_the_credential_environment` plants them and
asserts they come back gone, so this bites only a NEW variable nobody has
scrubbed yet. **The generalization is the part worth keeping: an ABSENCE is
state too** — a fixture constructing "nothing is available" owns that absence
and must clear the environment, not merely decline to set anything
([fixture-owns-its-state](../practices/fixture-owns-its-state.md)). Full story,
all three instances, in [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md)
entry 32.


## 24. <a id="g24"></a>A harness run that overlaps a write to the tree fails on a change belonging to no ...

**A harness run that overlaps a write to the tree fails on a change belonging
to no commit, and the count alone cannot tell you that.** `verify_harness.py`
reads the tree as it goes, over a hundred-odd checks and several minutes. On
2026-09-07 a run came back `1 failed` because a negative-control test had
briefly planted a failing check into `verify_harness.py` **while the run was
still in progress**. The failure was real, reproducible, and belonged to no
commit; two earlier runs and four later ones on the identical tree were clean.
`1 failed` renders identically whether it is self-inflicted, a real flake, or
a real bug. Run the harness to completion before editing anything it reads,
including its own controls, and never run two at once. The run recaps every
failure by name before the summary, so `tail -5` tells these apart.


## 25. <a id="g25"></a>Pointing a fixture's HOME at an empty directory does not keep it empty: ...

**Pointing a fixture's `HOME` at an empty directory does not keep it empty:
`precedent_resolve.load_config()` CLONES the individual source into it.** The
self-heal re-runs `.claude/hooks/precedent-individual-bootstrap.sh` whenever
the individual source looks unusable, so any tool that resolves sources -- the
leak gate among them -- writes `.config/` and a whole `precedent-individual/`
clone into whatever `HOME` you handed it, then reports that the source
RESOLVED. 2026-09-08: a fixture built to reproduce "no private source could be
attached" turned itself into "a private source resolved" mid-run, and the
gate's refusal was read as a bug in the gate for an hour. **The tell is the
fixture home having contents you did not put there** -- `ls -a` it after the
run, not before. To hold the unresolved state, unset `CLAUDE_CODE_REMOTE` as
well: the self-heal is deliberately narrow and fires only in a hosted session.
Same shape as [fixture-owns-its-state](../practices/fixture-owns-its-state.md),
one level further out -- the fixture owned its `HOME` and still did not own
what the code under test would do to it.


## 26. <a id="g26"></a>The individual source resolves to a clone you are probably not editing, and it can ...

**The individual source resolves to a clone you are probably not editing, and
it can be many commits stale.** `~/.config/precedent/config.json` names an
absolute path, and **everything that resolves the individual source at runtime
reads that one** — not the sibling clone you have been editing. It has cost
several confusions: a harness fixture failing because it read that clone's
freshness, a SessionStart hook installing one of two commit hooks because the
script it executed was the stale copy, and on 2026-09-08 a materialize that
would have written pre-fix test files back into a consumer repo. **Check it
before concluding a tool is broken:** ``` python3 -c "import
json,pathlib;print(json.load(open(pathlib.Path('~/.config/precedent/config.json').expanduser()))['individual']['path'])"
git -C <that path> fetch && git -C <that path> rev-list --count
HEAD..origin/main ``` **The rule that resolves it:** the config-named clone is
pulled `--ff-only` at every session start, so it can only ever be BEHIND — an
attached sibling clone beside the repo you are working in is what a session
actually edits, and is the better evidence of what the source says. **A fix
that lives outside the repository cannot be recorded inside it as a state**,
only as a thing to check: `~/.config/precedent/config.json` is per-container,
so a session that repointed it fixed nothing for the next container. Do not
read any recorded path here as current — run the command.


## 27. <a id="g27"></a>A sibling clone that was current when you took it can rot while you work, and a ...

**A sibling clone that was current when you took it can rot while you work,
and a "these copies do not match" failure will blame the code rather than your
clone.** 2026-09-07: `verify_harness.py` reported three copies of
`commit-identity.sh` disagreeing. The check was correct that they differed and
wrong about what that meant — the attached clone was 2 commits behind, and one
`git -C <clone> pull --ff-only` made all three agree with no change to any
file here. **The direction of the mistake is what makes this worth a rule**:
the failure reads as "this repo's file is wrong", and the obvious remedy —
copy the clone's older version over the newer one — silently reverts
somebody's just-landed work. Confirm which side is stale first: `git -C
<clone> fetch && git -C <clone> rev-list --count HEAD..origin/<branch>`. Same
reasoning for a check younger than your branch: rule out "never been green
here" by running it against the untouched tip before fixing it.

**Second instance, 2026-09-11, where the stale clone was the LEAK GATE's
blocklist** — and it put a wrong finding in a pull request. The gate
reported 30 undeclared-repo hits; a session read them as a real defect,
wrote "red on the base branch too" into its gate block, and filed a TODO
item for a fix already merged. Its clone of the private set predated a
repository rename by hours, so it lacked the allowlist line those 30
references needed. **A correct gate, correct output, stale input —
indistinguishable from a real failure by construction.** The gate says so
itself now: on failure it names the blocklist's clone and how far behind
it is. It never claims a clone is current (an unfetched remote-tracking
ref cannot prove that) and never fetches, since a gate that reaches the
network to grade itself can hang on a push. **When a gate whose input
lives in another repository fails, ask how old the input is before
believing the finding.**


## 28. <a id="g28"></a>A scratch COPY of this repo, taken to prototype a change without touching the ...

**A scratch COPY of this repo, taken to prototype a change without touching
the working tree, goes stale the moment the freshness guard fast-forwards the
real checkout under you — and copying the prototyped files back reverts every
commit that arrived in between, silently.** 2026-09-11: a session copied the
tree to the scratchpad, prototyped a fix to `precedent_check.py` there,
measured it, and copied the two changed files back. In between, the guard had
done exactly what it is built to do and moved the checkout forward three
merges. `git diff` against the copy had read clean when the copy was taken,
which is the whole trap: it rots from the OTHER side, so nothing about the
copy looks different afterwards. The revert took out another session's
refinement of an unrelated check's description, and **only
[tools/doc_sync.py](../tools/doc_sync.py) caught it** — `spec/ENFORCEMENT.md`'s
generated block regenerated to text OLDER than the committed block, which is a
shape no other gate here looks for. The wholesale-copy-back is the mistake; a
prototype copy is still the right way to measure. **Re-apply the edits to the
CURRENT file** — the same patch script, run against `HEAD`'s version, with
each `old` string asserted to occur exactly once so a moved file fails loudly
instead of half-applying — **then read `git diff` before committing and
confirm every hunk is one you meant.** A hunk you did not write is the revert.


## 29. <a id="g29"></a>HEAD == origin/<branch> and a clean tree is NOT evidence that your work landed — it ...

**`HEAD == origin/<branch>` and a clean tree is NOT evidence that your work
landed — it is the exact reading you get when your commit has been thrown
away.** 2026-09-07: a session committed on local `precedent-beta-v01`, then
ran `git checkout -B precedent-beta-v01 origin/precedent-beta-v01`, which
**silently discarded the commit it had just made**. Its verification printed
`HEAD=a7e503c beta=a7e503c dirty=0` and read as success: every ref matched,
nothing was uncommitted, and the change was in neither the tree nor the
remote. A concurrent session's push made the hashes advance, which made the
output look *more* convincing. **Commit on the working branch, never on the
branch you are about to reset** — `git checkout -B` is a reset. And **verify
the CONTENT, not the refs**: `git show origin/<branch>:<file> | grep <a phrase
from your change>`, grepping for a phrase distinctive to your own edit rather
than a common one. Recovery: the commit is unreferenced, not gone — `git
reflog` lists it and `git cherry-pick` restores it.


## 30. <a id="g30"></a>The commit backstop is GLOBAL (core.hooksPath), so it reaches throwaway fixture ...

**The commit backstop is GLOBAL (`core.hooksPath`), so it reaches throwaway
fixture repositories too — and refused them.** A repo attached mid-session
inherits the container's *global* identity (measured:
`noreply@anthropic.com`), so a per-checkout fix cannot cover it even in
principle. The cost landed immediately: `verify_harness.py` builds dozens of
temporary repos and commits in them without `TZ`, and the backstop refused the
first one, taking the whole run down in a mechanism unrelated to what was
being tested. **A fixture commit is not a person's commit** — the harness sets
`PRECEDENT_ALLOW_ANY_AUTHOR=1` for every subprocess it spawns. Any other tool
that creates scratch repositories needs the same, and the symptom will not
look like an identity problem. `core.hooksPath` also makes git look THERE AND
NOWHERE ELSE, so the global hooks chain to each repository's own
`.git/hooks/<name>` first — without that, every repo's own gates vanish
silently. Resolve that path with `rev-parse --absolute-git-dir`, never
`rev-parse --git-path hooks`: the latter *respects* `core.hooksPath` and so
names the global directory.


## 31. <a id="g31"></a>"no individual source resolved" is not noise — it means every personal and team ...

**"no individual source resolved" is not noise — it means every personal and
team practice is silently absent, and the session will confidently apply the
wrong rules.** 2026-09-07: a session ran most of a working day here with none
of the account owner's personal practices loaded. `tools/precedent_resolve.py`
printed the reason on *every single run*, and the session read past it every
time as startup chatter — because the checks it prefixes all reported `0
violated`, and the line sits directly above the summary a session is reading
the output *for*. The cost is invisible while it happens: the practices that
did not load included `audience-register`, the owner's standing rule about how
replies are written, so **every reply that session was pitched by guesswork
while a rule saying exactly what to do sat unread**. The session's own
diagnosis each time was "I keep forgetting" — a misdiagnosis, since the rule
was never in front of it. **Stop and fix it before doing anything
rule-dependent:** `add_repo` for the private sources, then re-run `python3
tools/precedent_resolve.py --repo .` and confirm the count names `individual`
and `team`, not universal alone.


## 32. <a id="g32"></a>The private practice sets reach a session through the environment credential, not ...

**The private practice sets reach a session through the environment
credential, not through `add_repo`: set `PRECEDENT_GIT_TOKEN` and
`PRECEDENT_SOURCE_BASE_URL` ([PER_MACHINE_SETUP.md](../PER_MACHINE_SETUP.md)) and the SessionStart
hook clones them before the first turn, where no ordering rule can reach it.**
Verified end to end 2026-09-10 on a brand-new container and again 2026-09-11:
all four sources on disk before the first turn. **That "before the first
turn" guarantee did NOT hold on 2026-09-14, and it is the failure to plan
for.** In a resumed session the four clones landed *during the second turn*
-- reflog `clone: from .../precedent-team-writing` timestamped mid-session --
so the whole first turn ran with every team and individual practice silently
absent, on the universal set alone. Nothing announced it except the
unresolved-source notes, which read identically to the steady-state failure
this entry is about. **So treat the credential route as reliable but not
instantaneous**: on turn one, check the session-start source line rather than
assuming, and where something reports a source missing, look again before
concluding anything -- a race and a real absence print the same text
(practice: [diagnosis-is-measured](../practices/diagnosis-is-measured.md)).
The cost when that is skipped was paid the same day: a session read the
missing sources, relayed this entry's own two candidate causes -- refused
credential, retired repository -- as a diagnosis, and recommended deleting
three live source declarations. Both causes were wrong; the clone had simply
not run yet.
[tools/precedent_resolve.py](../tools/precedent_resolve.py) prints `MISSING` when
no credential is set and `SET` when one is set and a clone still failed; the
session check and the session-start source report print the same line.
**`add_repo` is the fallback, and what is measured about it does not add up.**
Three 2026-09-07 measurements had it refusing a cross-owner add in BOTH
directions — including as a session's very first tool call, so "call it before
anything else" is not a remedy — while two other sessions held repositories
from both owners at once and pushed to all of them. Nobody has an explanation
that fits both, so call it, read what it says, and proceed from that; never
from a remembered result. The full contradictory sequence is entry 34, and the
cost of skipping it is the entry above: a session with `individual` and `team`
unresolved applies the wrong rules all day and cannot tell. **If `env | grep
-c PRECEDENT` says 0, that is not proof the runner drops variables** — an
account can hold two environments with the SAME NAME and the selector cannot
tell them apart, which is what it was three times. The setting-up half of this
now lives where someone setting the variables reads it,
[PER_MACHINE_SETUP.md](../PER_MACHINE_SETUP.md)'s environment table; the three-day sequence is
[record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md) entry 29.


## 33. <a id="g33"></a>add_repo on a PUBLIC repository attaches nothing and never reaches the cross-owner ...

**`add_repo` on a PUBLIC repository attaches nothing and never reaches the
cross-owner check, so testing that wall with `access: "read"` measures nothing
at all.** Asked on 2026-09-09 for read access to `alex137/bestpractice` from a
session rooted in a private practice-set repository owned by someone else, it
answered `"status":"read_available"` and *"Nothing was attached to the
session"*: the session's git proxy already serves anonymous clones of public
GitHub repositories, so the request short-circuits before any authorization
runs. **Read as a success, that says the cross-tier refusal above has been
lifted. It has not been** — the tool's own reply names `access: "push"` as the
path that runs the full repository-access checks, and warns in the same breath
that cross-owner attachments may still be refused. **The useful half is what
it hands you anyway**: a session rooted anywhere, under any owner, can
`GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1` this public repository with
nothing attached — which is how a session working in a private source set
reads the upstream tree. Allow ≈10 minutes and do not interrupt the clone.
What that checkout cannot do: push, reach the GitHub tools (its web
application programming interface, and the Model Context Protocol server that
fronts it), or fetch Git Large File Storage objects.


## 34. <a id="g34"></a>A session you spawn can lose its Model Context Protocol (MCP) tools mid-run, and it ...

**A session you spawn can lose its Model Context Protocol (MCP) tools mid-run,
and it cannot report back to you either — so a spawned session must take the
measurement it was spawned for in its OPENING turn.** 2026-09-09: a
measurement session created with `create_session` called `add_repo`
successfully as its first tool call, and when sent a follow-up minutes later
answered that the tool was gone — *"the MCP server that provided it was
removed from the configuration mid-session"* — with a `ToolSearch` for it
returning nothing. Nobody reconfigured anything. The follow-up measurement was
simply lost. The second half was wrong until 2026-09-13: `ListAgents` does not
reach a cloud session, so `SendMessage` fails — but **that is peer messaging,
not every route.** `create_trigger` with `persistent_session_id` fires into a
named session; one did that to correct this entry. It needs the spawner's
session id, so the seeded prompt must name it
([seeded-prompt-names-its-origin](../practices/seeded-prompt-names-its-origin.md)).
Still write the measurement into the prompt: the tools can vanish mid-run,
which is this entry's actual subject.

## 35. <a id="g35"></a>A private repo name reaches a public tree by nobody having predicted it, so repo ...

**A private repo name reaches a public tree by nobody having predicted it, so
repo references are an ALLOWLIST, not a blocklist.** Declare an owner
private-by-default in the private blocklist file (`# visibility-audit:
private-owner <account> -- reason`) and every `owner/name` mention is refused
unless an `allow` line gives a reason. The blocklist approach failed in both
directions on 2026-09-07: it missed a private repository nobody had listed,
and blocked two names that had become public. **The set of names you may
mention is small and known; the set of repos you might create is unbounded.**
**The case that matters and is easy to miss is the URL form** — the lookbehind
keeping `a/acct/x` from matching also rejects `github.com/acct/x`, because the
character before the owner is `/` there too. A stated test case caught that;
reading it did not. **And a blocklist entry catches the name somebody typed,
never the SHORT form of it.** A private repo leaks through what is named AFTER
it — a practice source, a branch, a directory, a tag, a check — long after the
repo's own name is gone, under the short name people actually type. The fix is
truncating each pattern to a distinctive stem, verified at zero hits against
this tree; the measurement behind each cut is in the archive.
[tools/very_deep_check.py](../tools/very_deep_check.py) does the other half on
request, asking the GitHub API whether each referenced repo is actually
private; the push gate cannot, because it must work offline and in CI.


## 36. <a id="g36"></a>A background sleep is not a wait, and using one as a wait makes you invent elapsed ...

**A background `sleep` is not a wait, and using one as a wait makes you invent
elapsed time.** 2026-09-11: a session polling a continuous integration job ran
`sleep` four times as a BACKGROUND task, then queried the API immediately each
time — a background task returns a task id at once and pauses nothing. It
believed roughly thirteen minutes had passed. Real elapsed time between its
polls was near zero, so every poll returned the same `in_progress`, which it
read as a hung job. **The second half is the expensive one.** It then reported
the job as hanging "after 18 minutes" — a figure it got by comparing the job's
`started_at` against a present moment it had never measured. It had not run
`date` once. The job had in fact finished in 5 seconds, failing normally on a
pre-existing violation, 26 seconds BEFORE the session merged over it; the last
poll it acted on returned stale data. The invented figure went into a merge
commit on `precedent-beta-v01`, where it cannot be corrected in place —
published history — so the correction lives as a comment on the pull request
instead. **Read the clock before claiming any duration.** `date -u` costs
nothing, and a timestamp compared against an imagined now is not a measurement
— it is [no-invented-specifics](../practices/no-invented-specifics.md) failing in
the one place the invention looks like arithmetic. Note also that the harness
DOES notify when a background task completes; those notifications arrived,
just after the merge. The mechanism was there and went unused. **The symptom
impersonates a real failure**, which is why this is worth a gotcha rather than
a shrug: a stale `in_progress` and a genuinely hung job render identically,
and "it's been N minutes" is exactly the sentence that makes a session stop
waiting.

## 37. <a id="g37"></a>A shallow clone makes a merely-behind checkout read as diverged, so the guard ...

**A shallow clone counts every commit back to its graft point as LOCAL, so a
checkout that is only BEHIND reads as diverged — and the freshness guard then
refuses to update it, which is worse than either.** 2026-09-13: a session came
up on a checkout from the previous morning, 172 commits behind
`origin/precedent-beta-v01`. The guard's session-start pass fetched, computed
`behind=172` and `ahead=132`, concluded the two copies had gone their separate
ways, and warned instead of fast-forwarding — correct behaviour for a genuine
divergence, and there was none: after a deeper fetch, `merge-base` resolved to
`HEAD` itself and the local-only count was **zero**.

**What it cost is the part worth keeping.** The session wrote a whole reply
against a day-old tree — including rules that had been superseded that
morning — and the tell was not a git error but a defect the person had already
reported fixed: the fix (a `UserPromptSubmit` reply gate, landed at 14:12 that
day) simply did not exist in the files the session had. **A stale checkout
does not announce itself as staleness; it announces itself as your own work
being wrong.** The session only found out because an unrelated command tripped
the pre-write guard, which reported the same phantom divergence.

**Both of the obvious readings are wrong.** "Origin has moved and I should
re-push" is wrong — nothing local existed. "The guard is broken and should be
overridden" is wrong, and `git config precedent.freshness.override true`
switches off the stale-base check as well, which catches the most expensive
failure class in this file.

**Reproduce it in four commands**, which is how the fix was verified: clone
`--depth 1` over `file://` (a local path ignores `--depth`, gotcha
[g7](#g7)), add commits upstream, then `git fetch --depth=1 origin <branch>`.
The fetched tip lands as a **disjoint graft** with no path back to `HEAD`, so
`rev-list --count origin/<branch>..HEAD` counts everything the shallow clone
can see and calls it local. A plain `git fetch` on an already-shallow
repository can produce the same disjoint state, which is why the guard's own
fetch was not enough.

**Fixed 2026-09-13** in both copies of
[.claude/hooks/freshness-guard.sh](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/.claude/hooks/freshness-guard.sh):
when the counts say diverged and the clone is shallow, `_deepen_if_shallow`
fetches `--deepen=500` (falling back to `--unshallow`, which some git policy
hooks refuse) and both counts are recomputed before anything is believed. The
same recount runs in the pre-write mode. Verified against a fixture that
reproduces the phantom: the old copy prints `has diverged ... NOT updating`
and leaves `HEAD` behind; the patched copy deepens, recounts 3 rather than 1,
and fast-forwards.

**The same commit added the quantity a person can actually judge.** Every
message reporting a checkout as behind now carries how much OLDER it is than
the remote tip — computed from the two tips' commit times, never from the
container's clock — and past a declared limit (`stale_checkout_hours` in
[precedent.json](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/precedent.json),
24) it is labelled `STALE` rather than merely behind. Morgan's reasoning for
wanting the time and not the count, 2026-09-13: over a missed hour *"chances
are not much changed"*, over a few days *"chances are a lot did, thus
increasing the risk of problems."*

**It fired again on 2026-09-14, and the cause is not unknown: the fix could
not run, because the fix was not in the tree that was running.** A session
opened here and the guard refused its first tool call with
`'precedent-beta-v01' has diverged (132 local, 162 remote)`. A bounded
`git fetch --depth=500` recounted it as **0 local and 212 behind**, and the
branch fast-forwarded cleanly — the same phantom this entry is about, on a
checkout that already had `_deepen_if_shallow` committed upstream.

**The obvious reading is that the fix fired and failed, and that reading is
wrong.** A second session checked the file afterwards, found
`_deepen_if_shallow` present, ran its fetch command by hand, got exit 0, and
concluded the guard had refused with a working fix installed — cause unknown.
That is true of the file and false of the run: by the time it looked, the
fast-forward had already replaced the file. `git show <the checked-out
commit>:.claude/hooks/freshness-guard.sh` settles it — **zero occurrences of
`_deepen_if_shallow`** in the copy that actually executed. The commit carrying
the fix is an ancestor of the current tip and **not** of the commit that was
checked out; it was one of the 212 the session did not have.

**The generalization is the part to keep: this hook runs from the working
tree, so it cannot repair a checkout too stale to contain it.** Every fix to
the freshness guard is delivered by the mechanism the fix is about, and the
case it most needs to handle — a badly stale checkout — is exactly the case
where the pre-fix copy is the one executing. **A session's own first fetch is
the only thing that closes that loop**, which is why the four commands under
"Reproduce it" stay worth running by hand when the counts look like a
divergence. Do not read "the fix is installed" as "the fix ran": ask what the
file looked like at the commit that was checked out, not at the one you are
standing on now.

**Measured the same day: all four private practice sets still carry a pre-fix
guard**, so a session rooted in any of them meets the original trap at full
force. Their vendored engines were refreshed to current that day and did
**not** bring the hook with them — the engine and the hooks go stale
independently ([g20](#g20)), and only the engine has a repair path.

## 38. <a id="g38"></a>A Routine that fires a FRESH session gets none of the session-management tools, so a scheduled job that reads the fleet cannot run there

**Measured 2026-09-14**, twice, in opposite directions on the same afternoon.

A scheduled Routine was created to sweep the fleet — list every session, keep
the ones blocked on the person, notify. `create_trigger` returned a warning
that reads like boilerplate: *"this trigger stores no MCP connectors, so the
sessions it fires will run without connector (`mcp__<server>__*`) tools."* The
Routine was fired once as a test. It completed in 32 seconds and exited 0, and
its recorded run status was `SUCCEEDED`. **The run succeeded at doing
nothing**: the fired session reported that `list_sessions` was not available to
it, which is the one tool the whole job rests on.

**Neither the warning nor the run status tells you this.** A Routine whose
session cannot do its work still fires, still finishes, still records success —
the failure is inside the turn, and `last_run` cannot see in there. Left alone
it would have reported quietly for as long as nobody opened a run.

**The remedy the warning names does not apply.** `connectors` resolves against
the person's connected claude.ai connectors — measured on this account: Gmail,
Google Calendar, Google Drive, and nothing else. The session-management server
is the harness's own, not a connector, so there is no name to pass and nothing
for the `connectors` argument to carry.

**What works is a STANDING session.** A session created with `create_session`
*does* get the tools — confirmed by creating one and watching it parse a saved
`list_sessions` result mid-sweep. So the shape is a standing session doing the
work, and a Routine bound to it with `persistent_session_id` waking it on the
schedule.

**That costs the Routine's own notifications**, which the server offers only to
a Routine that starts a fresh session on each firing. The way back is that the
standing session can send one itself: `PushNotification` with
`status: "proactive"` is available inside a session and reaches the person's
phone. So the notification moves from the Routine into the prompt.

**The generalization worth keeping: a scheduled job's capabilities are not the
capabilities of the session that scheduled it.** Test the fired session's
tools, in its opening turn, before building anything on top of it — and read
what the test run actually *said*, never its exit code.
