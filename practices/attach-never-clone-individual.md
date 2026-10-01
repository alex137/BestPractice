---
slug:        attach-never-clone-individual
title:       Attach the individual source, never make a second clone of it
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "No locus, and deliberately `**`. The mistake is a session running `git clone` into the wrong directory right after the repo-attach tool answers, outside every repo's tree; no file in this one is edited when it happens, so a narrower glob would never fire. The occasion index is the channel. Decided: 2026-09-25, when the practice was written."
occasion:    "attaching a practice source"
gates:       []
index_clause: "attach the individual one, never a second clone; shared sets sit beside the repo"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-25"
approved_by: "Morgan, 2026-09-25, in a handoff relayed from a consumer repo's
  vendors-update session -- \"move this instruction into a practice ...
  since practices do reach every repo through sync\" (strength: decided, his
  own pick among the two routes the handoff named)"
---
## Rule
**Attach the individual source; never make a second clone of it.** Call the
repo-attach tool (`add_repo` in Claude Code on the web) for
`precedent-individual` as the session-start step says: it is what grants
this session access, push included. Its reply (as of 2026-09) says to clone the repo to
`/home/user/<name>`, the directory the project lives in, while the source
bootstrap clones it to `~/precedent-individual`. **The bootstrap keeps one
working tree and makes both paths lead to it.** If it cloned first, it has
left a link at the attach path, so the reply's clone command stops with
"destination path already exists": that is the set, already there, and that
path is fine to register, open and edit in. If the session cloned first, the
next bootstrap run (the resolver's self-heal, or `python3
tools/precedent_session_check.py --apply`) reuses that clone, points
`~/.config/precedent/config.json`'s `individual.path` at it, and links
`~/precedent-individual` to it. **Either path is the same tree; a clone
anywhere else is a second copy nothing loads.** If two separate trees are
already on disk, the bootstrap and the session check report both and touch
neither: carry any work out of one into the other, remove the emptied one,
and re-run the bootstrap, which links its path instead of cloning again.

**A shared set is the other way round:** its clone lives at the path the
repo's `precedent.json` resolves (`../<name>`, beside the repo). If that path
already holds a working clone — `git -C <path> rev-parse HEAD` succeeds —
use it. If not, clone it there, and do so even when the attach tool attached
nothing, which is what it does for a public set.

## Why
A second clone of the individual set is one nothing loads. An edit
committed and pushed from it looks landed while every session keeps reading
the other copy, and the hook keeps pulling that other copy forward while the
hand clone stays where it was. Nothing errors. A practice written that
morning is simply not in force.

## Story
Measured in a consumer repo on 2026-09-25. A session called the attach tool
for `precedent-individual`, followed its reply, and cloned the set to
`/home/user/precedent-individual`. The hook had already cloned it to
`~/precedent-individual`, and the user config pointed there. Within the hour
the two had diverged: the hook's copy had moved forward to a newer commit
and the hand clone was still on the one it was cloned at.
[`tools/precedent_session_check.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_session_check.py)'s
"each practice source is cloned exactly once on this disk" row caught it,
but only afterwards.

The instruction that sent the session to the attach tool came from this
repo's own install templates
([templates/AGENTS.md.loader.template](https://github.com/alex137/BestPractice/blob/staging/templates/AGENTS.md.loader.template)
and [templates/AGENTS.md.template](https://github.com/alex137/BestPractice/blob/staging/templates/AGENTS.md.template)).
Both said to attach the individual repo and neither said where its clone
lives, so the tool's own suggestion filled the gap. Fixing the templates
alone would not have reached one installed repo: a refresh regenerates only
the loader block, and the hand-written prose a template installs is frozen
from the day it was installed. **That is why this is a practice.** Its line
in the occasion index is part of the loader block, so every refresh carries
it into every installed repo's instructions file.

The obvious home was the individual set's own `claude-web-bootstrap`, and it
is the wrong one: a practice in the individual set is read only once the
individual set has resolved, and the moment this rule is needed is exactly
the moment it may not have. It is universal for the same reason.

The other route considered was a refresh-time diff of each installed
template section against the current template. It was not taken: every
install fills the template's placeholders and many edit the prose around
them, so the diff is mostly noise, and it would be a new mechanism to build
and maintain where the practice route already exists and already reaches
every repo.

**2026-09-28: telling sessions to ignore the reply did not hold.** Two
consumer sessions reported the same "cloned exactly once" row failing every
turn, one with both copies at one commit and one with the two diverged. The
rule then said to ignore the half of the attach reply that says where to
clone; the reply is the more recent and more specific instruction a session
has in front of it, and it won. Telling sessions to skip the attach
altogether was ruled out, because the attach is what grants push access. So
the fix moved into the engine, the same answer
[`_clone_elsewhere_on_disk`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_source_bootstrap.py)
already gave the shared sets: one working tree, with every other path a
symlink to it. Whichever route clones first keeps its tree, and the other
path becomes a link. Two trees that already exist are reported and never
merged or removed by the bootstrap (practice `repair-cannot-discard-work`),
since in the diverged report the hand clone could have held commits nobody
had pushed.

## Install
Nothing to install beyond the engine. The templates' own attach bullet
points here, and the line reaches an installed repo with its next refresh;
the linking lives in the vendored
[`tools/precedent_source_bootstrap.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_source_bootstrap.py),
so it reaches a consumer with its next engine refresh and needs no change to
the consumer's own bootstrap hook. It finds the attach path as the parent
of `$PRECEDENT_PROJECT_DIR`, else of `$CLAUDE_PROJECT_DIR`; a harness that
sets neither gets the old single-path behaviour. It only looks there for a
hosted repository URL, and only reuses a clone whose origin names the same
repository.

**Checked by the harness, and caught after the fact.**
[`tools/verify_harness.py`](https://github.com/alex137/BestPractice/blob/staging/tools/verify_harness.py)
pins both orders (attach first, bootstrap first) and the diverged pair.
[precedent_session_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_session_check.py)'s "cloned exactly once" row still fails on
two working trees for one source and names both; a symlink counts as one
tree.
