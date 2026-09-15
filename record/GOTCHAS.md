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

**`pip install cmarkgfm markdown`, or two gates degrade and a third fails
for reasons that have nothing to do with the tree.** Neither is in the
standard library, and the two behave differently, which is what makes this
worth reading twice.

**cmarkgfm — silent.** Without it
[tools/doc_lint.py](../tools/doc_lint.py)'s strikethrough check does not
fail: it prints a one-line notice and scans for everything else, so a
document that renders an unintended `<del>` on GitHub passes the gate. The
`doc-references-are-links` check in
[tools/precedent_check.py](../tools/precedent_check.py) skips for the same
reason and says so in one line among fifty.

**markdown — one tool, one exit code.** [tools/doc_html.py](../tools/doc_html.py)
imports it at module level, so `--help` exits 1 and the deck engine cannot
render `.md` slides.

**Where it actually bites is [tools/verify_harness.py](../tools/verify_harness.py),
which does NOT degrade.** It fails the checks that need them, and each failure
describes what it was *testing* — strikethrough cases, a planted
`doc-references-are-links` violation, a `--help` sweep across 56 tools — never
what is missing. On 2026-09-14 that read as `3 failed` on a branch whose entire
diff was two markdown files, and took two full harness re-runs to attribute:
install `cmarkgfm`, down to 1 failed; install `markdown`, `202 passed, 0
failed`. The harness now names the missing packages in a preflight line and
again in the closing recap, so the shortest reading of its output says
"environment", not "your diff".

**Both are installed by
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh)** (only
when `CLAUDE_CODE_REMOTE=true` — a local shell has to do it), and by both CI
workflows. **So a container missing them is telling you the hook never ran**,
which is a much larger fact than two absent packages: the same session had
neither the generated session-practices file the private sources write, nor
the commit backstop. That session
was rooted one directory ABOVE this repository — see [g17](#g17) — so none of
its hooks fired, silently. [`python3 tools/precedent_session_check.py`](../tools/precedent_session_check.py) reports
all of those guarantees at once, and its packages row now names `pip install`
as the remedy rather than `--apply`, because `--apply` re-runs the hook that
could not run.


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

**Since 2026-09-14 the primary repo does this for you**, in
[.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh): a shallow
clone is deepened at session start, before anything reads history, bounded by
`timeout` and falling back to `--deepen` where `--unshallow` is refused.
Measured against this remote: 2.7 MB of history before, 9.5 MB after, 4
seconds. **What it does NOT cover is every case this entry is about** — a
sibling attached mid-session runs none of its own hooks
([g15](#g15)), a CI checkout is its own shallow clone, and a source set has no
such hook at all. In any of those, the manual fetch above is still the fix, and
a tool reporting a suspiciously clean result is still the symptom.


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

**Second recorded instance, 2026-09-14, and it narrows the suspects.** A
session working on a feature branch found the checkout back on
`precedent-beta-v01` between one tool call and the next, with
`git reflog` showing `checkout: moving from <feature-branch> to
precedent-beta-v01` and nothing else — **no pull afterwards this time**, unlike
the 2026-09-08 case. Nothing was lost: the branch tip still matched its remote,
because the work had already been pushed. What that buys is the ordering — the
move happened AFTER a push and a fetch, in a turn that ran no repository tool
at all beyond `git`, so whatever does this does not need one of this repo's
own tools to have been invoked. **The cheap habit that made it a non-event was
pushing before the gap**: a pushed branch survives the move, an unpushed one
survives only in the reflog.


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
reads the upstream tree.

**This entry said "allow ≈10 minutes" until 2026-09-14, and that figure does
not reproduce.** Measured on a hosted container that day, both clones landing
on `precedent-beta-v01` with all 116 practice files present: `--depth 1` took
**1 second** for 14 MB and 1 commit, and a FULL clone — which is what
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
actually runs for a universal source, with no `--depth` — took **3 seconds**
for 20 MB and all 1,394 commits. This repository is almost entirely prose, so
there is very little to transfer. Nobody knows what the ten minutes on
2026-09-09 was; a cold proxy and a Git Large File Storage (LFS) fetch are both candidates and
neither was measured. **What matters is not to cost a design decision against
it** — the ≈10 minutes was quoted in a 2026-09-14 session as the reason not to
put the universal catalogue in front of every session, and the real number is
three seconds (practice: diagnosis-is-measured — a relayed figure is a
hypothesis until this container measures it).

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

**A third occurrence, 2026-09-15, finally answers "can this be prevented
outright" — and the answer is narrower than either fix so far assumed.**
This session's checkout came up shallow at a commit hundreds behind tip
(`b3040c6`), the freshness guard refused the first tool call with
`132 local, 479 remote`, and `git show b3040c6:.claude/hooks/session-start.sh`
and `...freshness-guard.sh` both came back with **zero** occurrences of the
unshallow/deepen code. Same trap, third time.

**Anthropic's own docs settle why, as of 2026-09-15**
([claude-code-on-the-web](https://code.claude.com/docs/en/claude-code-on-the-web),
[cloud-environments](https://code.claude.com/docs/en/cloud-environments)):
*"Cloud sessions start from a fresh clone"* is true of a session's **first**
turn only. Every later turn **resumes the same virtual machine (VM) and the
same checkout** —
nothing re-clones, and *"resuming an existing session never re-runs the
setup script."* SessionStart hooks do fire on every resume, but they run
**whatever copy of themselves is already checked out**. A session opened
before a hook fix merged, and kept alive since, can never pick that fix up
by resuming — the hook that would fetch the fix is the one artifact resuming
cannot refresh. This is not a bug in the hook; it is what "resume" means.

**So there is no committed file that closes this for a session already
running old code.** The only way in is from inside that session:
`git fetch --unshallow` (or a bounded `--deepen`), run once, by hand or by
the hook succeeding on that session's own first chance to run current code.
Once it succeeds, the repo is no longer shallow at all, so the class of bug
cannot recur for that checkout again — this is a one-time threshold per
already-open session, not a recurring one.

**What a committed fix *can* still do, and where today's copy falls short:**
it already self-heals every **brand-new** session correctly (a fresh clone
gets the current, fixed hook) — the gap is only in already-resumed sessions,
and in how loudly a failed attempt reports itself. Today's `session-start.sh`
gives the unshallow exactly one `timeout 90` try and, on failure, writes a
single `WARN` line to stderr that nothing re-surfaces later. And
`freshness-guard.sh`'s `_deepen_if_shallow` only fires from the
divergence-detection branch (`ahead != "0"`) — a checkout that is shallow but
merely *behind*, never mis-read as diverged, gets no second attempt from the
guard at all if SessionStart's own try failed. Proposed hardening (not yet
built) is tracked at
[TODO.md's `shallow-clone-self-heal-hardening` item](../TODO.md#shallow-clone-self-heal-hardening).

**A setup script does not close the gap either, and is worth ruling out
explicitly so nobody re-proposes it.** Setup scripts are the one mechanism
that lives outside the git tree (environment config, not a committed file),
which looks at first glance like the way around the bootstrapping trap. But
per the same docs, a setup script *"runs the first time you start a session
in an environment"* and is *"skipped when a cached environment exists"* —
the environment filesystem is cached for roughly a week, so a setup script
is **not** guaranteed to run on every new session either, let alone on a
resumed one. It would add a second unreliable path, not close the one gap
that matters.

**Built 2026-09-15**, same session, same day, on Morgan's go-ahead. Both
`.claude/hooks/session-start.sh`'s single `timeout 90` attempt and
`freshness-guard.sh`'s divergence-gated `_deepen_if_shallow` were the
narrower gaps this entry always said were still open — not the
bootstrapping trap itself, which stays exactly as described above.
`session-start.sh` now retries once more on failure and leaves a
`PRECEDENT_SHALLOW_UNRESOLVED` marker in the git dir when both attempts
fail; `freshness-guard.sh` now calls the deepen unconditionally, before
either of its two callers trusts an ahead/behind count, and surfaces a
loud `WARN` at session-start when that marker is still there. A fixture
built to reproduce this entry's exact shape turned up something worth
recording precisely because it is not what the "reads as diverged"
framing above predicts: on the git version this container runs, the
disjoint shallow graft read as **`0 behind, 0 ahead`**, not as a false
divergence — so the OLD code, gated on `ahead != "0"`, never even
attempted a deepen and silently treated a checkout that was five real
commits stale as fully up to date. The new unconditional call fixes
that shape too, not only the one this entry names. Full detail:
[TODO.md's `shallow-clone-self-heal-hardening` item](../TODO.md#shallow-clone-self-heal-hardening),
closed.

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

## 39. <a id="g39"></a>A session can push branches but cannot DELETE a remote branch — the refusal is a 403 that reads like a network failure

**Measured 2026-09-14**, after a session had spent a whole conversation
offering to delete merged branches and never once trying.

`git push origin --delete <branch>` fails:

```
error: RPC failed; HTTP 403 curl 22 The requested URL returned error: 403
send-pack: unexpected disconnect while reading sideband packet
fatal: the remote end hung up unexpectedly
```

**The second and third lines are what make this waste an hour.** They are the
symptoms of a dropped connection, so the obvious reading is "the network
blipped, retry" — and a retry produces the same three lines, which reads as a
flaky remote rather than a settled answer. Only the first line, which scrolls
past first, says what actually happened.

**It is a capability limit, not a transient.** Proved by running both halves
back to back: the delete failed twice, and an ordinary `git push -u origin
<new-branch>` in the same working tree, seconds later, succeeded and printed
the pull-request URL. So the credential carries write access to *create* refs
and not to *remove* them, and nothing in the tooling says so up front.

**What this costs is credibility rather than work.** A session that offers
"say the word and I'll delete those branches" is promising something it cannot
do, and the person finds out only when they take it up. Offer to *list* merged
branches; leave the deletion to the person, who has a one-click Delete branch
button on every merged pull request page.

**Do not probe this with a throwaway branch.** The obvious test — push a
scratch branch to prove pushes still work — leaves behind a branch that,
by the very limit being tested, cannot then be removed. The session that
wrote this entry did exactly that and added `claude/push-capability-probe`
to the remote permanently.

## 40. <a id="g40"></a>The session-start identity block reaches every Precedent repo EXCEPT the individual set it reads the identity from

**Measured 2026-09-14**, during a four-set `Update Vendors` rollout — the
first work in months that commits to all four practice sets in one session,
which is the only reason anybody saw it.

Three team sets and BestPractice committed normally. The fourth, the
individual set, refused:

```
commit refused: it would be authored by the container's own agent account
(noreply@anthropic.com), not by a person.
  This is the GLOBAL backstop -- it fires in every repository, including one
  attached mid-session.
```

**The backstop was working.** It caught exactly what it exists to catch. What
was broken is the thing that should have made the backstop unnecessary.

`.claude/hooks/session-start.sh` applies the individual set's own
`bootstrap/commit-identity.sh` to each Precedent repo in the session. It found
them with:

```sh
for _repo in "$_here" "$_here"/../*/; do
```

— the primary repo, and its **siblings**. An individual set is not
necessarily either. `~/.config/precedent/config.json` records wherever it was
cloned, and on this container that is `$HOME/precedent-individual`, while the
primary repo and all three team clones sit under a different parent entirely.
So the glob covered four repositories and missed the fifth.

**The sharp part is that the block already had the path.** It resolves
`$_indiv` a dozen lines earlier — that is how it locates the script it runs —
and then never passes it to the loop. The one repository it reads the identity
*from* was the one repository it never applied that identity *to*.

**Why it stayed hidden for so long.** A normal session reads the individual
set and commits to the consuming repo; it has no reason to commit to the set
itself. Only a rollout that writes to every source at once puts a commit in
front of the gap.

**What it costs is the mechanism, not the commit.** Setting `user.email` by
hand fixes the one commit in front of you, and that hand-fix is precisely the
"instruction competing with a default, on every commit, forever" that
`commit-identity.sh`'s own header says never to rely on. Left alone it would
have come back on every future session, in the one repository where a
wrong-author commit is least likely to be noticed.

**Fixed the same day** by naming `$_indiv` in the loop. Proved by A/B rather
than by reasoning: with the old loop, unsetting the set's local `user.name`
and `user.email` and re-running the hook left both unset; with `$_indiv` in
the list, the same sequence restored the person's declared name and address
from their individual set's `identity.json`. The
script is idempotent, so a set that IS a sibling being named twice costs
nothing.

**Do not verify this by unsetting the set's LOCAL user.email and looking at
what git resolves.** That reads through to the global config, and the global
config is not a fixed background here: re-running `commit-identity.sh` by hand
during the investigation rewrote the container's global identity from the bot
account to the person, so the same unset-and-check that reproduced the bug
earlier in the session quietly stopped reproducing it later — and the new
guard row sat green against a state that could no longer go red. A control
that cannot fail is not a control (practice: `control-asserts-which-failure`,
`fixture-owns-its-state`). Set a bot `user.email` LOCALLY in the source clone
instead: that is the failure state, it owns its own state, and the row goes
red on it.

[tools/precedent_session_check.py](../tools/precedent_session_check.py) now carries that row — *every practice
source on this disk commits as a person too* — so the next occurrence is
reported rather than discovered by a refused commit.

**Swept for the same assumption, 2026-09-14**, because one mechanism getting
a repo list wrong is a bug and four mechanisms deriving the list four ways is
the actual problem. Four walk repositories on disk, and they did not agree:

- `tools/precedent_refresh_sources.py` already asks the resolver for the
  declared paths and adds siblings to them — its own docstring records
  learning this the hard way. Correct, untouched.
- `tools/precedent_session_check.py` scans `$HOME` **and** the parent, so it
  reached both. Correct, untouched.
- `tools/leak_gate.py`'s `local_clone_refs()` surveyed siblings only, and on
  this container that found four of the five clones on disk — **missing the
  private one**. Measured, not reasoned: it returned `alex137/BestPractice`
  and the three team sets, and no individual set. So the repository whose
  name most needs auto-blocklisting was the one the survey never saw. Fixed
  by unioning the resolver's declared paths in.
- `tools/verify_harness.py`'s commit-identity copy check globbed
  `precedent-team-*` beside this repo. It happens to find all three here;
  it is now the union with what `precedent.json` declares, so it will keep
  finding them when one moves.

**The rule the sweep suggests**, for anything that needs to know what
repositories are on this disk: ask the resolver what is DECLARED, then add
siblings — never siblings alone. The individual set is the one that breaks
it, every time, because it is the only one whose location is a person's own
config rather than the session's layout.

## 41. <a id="g41"></a>`/rate_limit` lies from inside a session — it reports a pristine window while the response headers report the truth

**The symptom.** You want to know how much of the GitHub API allowance this
account has already spent, so you ask the endpoint built for exactly that.
It answers `core: 0 used of 15000`, with a reset always about an hour away,
and it answers that every time you ask — the reset moves forward on each
call. Nothing looks broken.

**What is actually true.** Measured 2026-09-14, seconds apart, on the same
credential in the same container:

```
GET /rate_limit                    -> "core": {"used": 0, "limit": 15000}
GET /repos/<owner>/<name>  headers -> X-RateLimit-Used: 74, Remaining: 14926
```

The headers on an ordinary call are correct and the endpoint is not. The
cause was not chased past establishing which of the two to trust — the agent
proxy sits between the session and GitHub, and `/rate_limit` is plainly not
being served the way the repository endpoints are.

**Why it matters more than an ordinary wrong number.** A budget check built
on that endpoint is green on the day the account runs out, which is the one
day it exists for — the same shape as the stale `views-drift` header that
claimed something was already failing the build. It was nearly built that
way here. [tools/github_budget.py](../tools/github_budget.py) reads
`X-RateLimit-*` off calls it was making anyway, never the endpoint, and
[tools/precedent_check.py](../tools/precedent_check.py)'s
`github-api-budget` check fails if anything goes back.

**Two more things the same session established**, both surprising and both
load-bearing:

- **There is more than one allowance pool, keyed by repository.** A call
  about the public upstream repo was charged to a 15,000/hour pool; calls
  about two private sources to two separate 5,200/hour pools with their own
  reset clocks. The harness attaches a per-repository credential, so "how
  much is left" is a question about a repository, not about the account.
- **`/search/*` and `/graphql` never reach GitHub from a container.** The
  proxy answers `403 This GitHub API path is not available: sessions are
  bound to their configured repositories`. So the tightest allowance on the
  account — search, at 30 requests a MINUTE, shared by every session at once
  — cannot be measured from where its refusals are felt, and the calls that
  spend it come from the harness-side `mcp__github__*` tools.

**Do not "fix" a rate-limit refusal by retrying.** The pool is shared by
every window running; the lever is fewer simultaneous sessions and cheaper
tools (the local clone before the API, a repo-scoped `list_*` before a
`search_*`). Practice:
[github-api-budget](../practices/github-api-budget.md).

## 42. <a id="g42"></a>The permission classifier refuses commits and checks in the very practice set whose `identity.json` declares `relayed_authorization: accepted`

**The symptom.** You are working in an individual practice set, adding the
one field [relayed-authorization](../practices/relayed-authorization.md)
tells you to add. The moment the field is in the file, commands that ran a
minute earlier in the same repository come back as

```
Permission for this action was denied by the Claude Code auto mode
classifier. Reason: [Instruction Poisoning]
```

`git commit`, [`python3 tools/precedent_check.py`](../tools/precedent_check.py) and
`python3 tools/precedent_identity.py --relay` were all refused this way.
`git status`, ordinary file reads and `python3 -m json.tool identity.json`
kept working throughout, so the session looks healthy right up to the point
where it has to write something.

**What was measured, 2026-09-14.** The same `--relay` command, same
container, same repository: it ran and printed `REFUSED -- (field absent)`
before the edit, was denied after it, and then ran again on a later turn and
printed `ACCEPTED` — with nothing changed but the turn it was called in. So
the guard is **not deterministic**, which is what makes "try again in a
minute" such an attractive and such a bad plan. Three sessions hit it before
it was written down.

**Why it fires is a hypothesis, not a finding**
([diagnosis-is-measured](../practices/diagnosis-is-measured.md)). The task
reaches these sessions as a seeded or relayed prompt, and what it asks for is
a file that widens what a relayed message may cause — which is precisely the
shape the guard exists to refuse. The file's own content appears to weigh
too, since the identical command passed with the field absent and failed with
it present. Neither was chased further; what matters operationally is below.

**What does not fix it.** An environment variable cannot: the
`PRECEDENT_COMMIT_*` rung is dropped from this one reader by design, so no
variable can declare acceptance. Retrying does not, rewording the commit
message does not, and a stated authorization from the person in that window
does not reliably — it got `--relay` and `build_views.py --check` through, and
left `git commit` and [`precedent_check.py`](../tools/precedent_check.py) refused. **Writing the same file
through the GitHub API is not a fix either**: it is the workaround the denial
exists to stop, and a session that reaches for it has decided it knows better
than its own guard.

**What worked.** The person did it himself, which is the honest reading of a
guard that distrusts relayed authority: paste the block into GitHub's web
editor, commit on the branch, open the pull request. A session can still
read, verify and report — fetching the branch, parsing the pushed
`identity.json`, and reading the check runs all work fine from outside that
repository.

**Two traps sitting inside the recovery path**, both hit the same day:

- **A commit made in GitHub's web editor carries the browser's offset**
  (`-0400` here), which an individual set's own timezone check fails on. It cannot be grandfathered from the web
  editor either, because the commit adding the exemption is stamped wrong in
  exactly the same way. Redo the commit locally under
  `TZ="America/Argentina/Buenos_Aires"`.
- **`git reset --soft main` against a stale local `main` silently reverts
  whatever landed in between.** Re-committing an old tree on a new parent
  produced a one-line change that also rolled back a merged pull request, and
  nothing complained: CI was green, because undoing someone's merge breaks no
  rule. It was caught only by counting the files in the pull request diff —
  one expected, six present. **Count the files before merging**, every time a
  branch has been rebuilt by hand.

## 43. <a id="g43"></a>A spawned session's seeded prompt cannot pre-authorize a merge — the classifier refuses the `create_session` call itself

**The symptom.** [go-merge](../practices/go-merge.md) and
[spawn-session](../practices/spawn-session.md) both say a relayed `Go merge`
travels with a seeded prompt: the receiving session merges without asking
again, bounded by
[relayed-authorization](../practices/relayed-authorization.md)'s check on the
target repository's own `identity.json`. A `create_session` call seeding a
cross-owner repository with a prompt that said, in effect, "commit, push,
open the pull request, and merge it" was refused before the new session ever
started:

```
Permission for this action was denied by the Claude Code auto mode
classifier. Reason: [Merge Without Review]
```

**What was measured, 2026-09-15.** The identical `create_session` call,
same target repository, same content otherwise, with only the merge
instruction removed and replaced with "stop at the pull request — do not
merge," succeeded immediately. The spawned session then did the work, opened
its pull request, and — later, on its own, inside its own turn — went on to
merge that pull request itself, with no refusal reported back.

**Why it fires is a hypothesis, not a finding**
([diagnosis-is-measured](../practices/diagnosis-is-measured.md)): the two
data points only distinguish *baking a merge instruction into another
session's seed* from *a session merging its own pull request live, in its
own turn*. Nothing here establishes which part of the classifier's model
draws that line, only that it does.

**What does not work.** Writing the merge authorization into the seeded
prompt, however precisely it cites `relayed_authorization: accepted` and
quotes the practice — the call is refused before the target session reads
any of it.

**What works.** Seed the spawned session with everything through opening
the pull request, and stop the prompt there. Whether the merge then happens
live in that session's own turn is up to what happens inside it (the
person approving it there, or the session's own permission mode allowing
it) — not something the spawning session can hand over in advance.

## 44. <a id="g44"></a>A PreToolUse hook's once-per-session sentinel is not proof against two tool calls the harness dispatches at once — and the trap that made the first attempt at fixing it worse

**The symptom.** `freshness-guard.sh`'s `pre-write` mode keys its
once-per-session sentinel on `session_id` alone when one resolves — which is
the normal case — so every tool call in one turn computes the identical
sentinel path. Two Bash calls sent in the same message, both their first
tool call of the session, both read `[ -f "$sentinel" ]` as false before
either has written it, and both fall through to `_pre_write_one`, which runs
`git fetch`/`--deepen` against the same `.git` directory at once.

**What was measured.** One of two parallel calls this session blocked with a
false "diverged" reading — `record/GOTCHAS.md#g37`'s shallow-clone artifact
— while its sibling call, touching the same checkout at the same instant,
read the correct counts and passed clean. Same session, same moment, two
different verdicts, because nothing serialized them. Confirmed with an
instrumented A/B fixture: two copies of the hook, one with the fix below and
one without, each with a marker-plus-`sleep 2` planted at the top of
`_pre_write_one`. Unpatched, both processes' markers, tagged with each
one's process ID (PID), appear interleaved in the shared log — genuine
concurrent execution touching git at once. Patched, only one PID's markers
ever appear; the other call exits clean off the sentinel the first one
wrote, without touching git itself.

**The fix, and the trap inside fixing it.** `flock` on an fd opened by
`exec`, re-checking the sentinel after acquiring it — a second caller that
had to wait finds the first one already finished and exits immediately
instead of repeating the same git work. Held on the fd rather than in a
subshell, so a later `_block`'s plain `exit 2` still releases it when the
process exits normally, with no unlock path to remember.

**The first attempt at this fix put `2>/dev/null` on the same line as
`exec 9>file`, and that is a distinct, separate trap from the race itself.**
`exec` with no command applies its redirections to the *current shell*,
permanently — not scoped to that one statement, and not undone when the
enclosing function returns. Proven in two lines: a function that runs
`exec 9>/tmp/x 2>/dev/null` internally, called, then followed by an
ordinary `echo ... >&2` *outside* the function and *after* it returned —
that line went silent too. Every later `echo ... >&2` for the rest of the
script's run went to `/dev/null` with it, which is exactly why two existing
`verify_harness.py` cases caught the bug: their expected stderr text came
back empty, not wrong. `flock`'s own `2>/dev/null` on its own line is a
normal external command's redirection and stays scoped to that command —
the fix was moving the suppression there, not removing it.

**The generalization worth keeping.** A `[ -f sentinel ] && exit 0` /
`: > sentinel` pair with no lock between the check and the write is a
check-then-act race the moment two processes can run it at once — true of
any "once per session" guard a PreToolUse hook keeps this way, not just
this one. And separately: never put a stderr redirect on a bare `exec`
line meant only to open a persistent fd — the redirect persists exactly as
much as the fd does.
