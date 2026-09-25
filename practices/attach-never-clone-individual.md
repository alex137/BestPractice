---
slug:        attach-never-clone-individual
title:       Attach the individual set, never clone it by hand
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "attaching a practice source to a session with the repo-attach tool, or that tool's reply says to clone what it attached"
gates:       []
index_clause: "attach the individual set, never hand-clone it -- work where the user config points; a shared set clones to its precedent.json path"
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
**Attach the individual set; never clone it by hand.** When the repo-attach
tool (`add_repo` in Claude Code on the web) grants this session read access
to `precedent-individual`, its reply says to clone the repo to
`/home/user/<name>`. **Ignore that part.** The session-start hook, or the
resolver's self-heal on the next resolve, clones the individual set to the
path `~/.config/precedent/config.json`'s `individual.path` names — normally
`~/precedent-individual` — and that is the only copy anything reads. **To
edit the individual set, work in that directory.** If the config is missing,
run `python3 tools/precedent_session_check.py --apply`, which re-runs the
bootstrap into the right place; a hand clone is not a substitute.

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

## Install
Nothing to install. The templates' own attach bullet points here, and the
line reaches an installed repo with its next refresh.

**Not mechanically checked before the fact.** The mistake is a session
running `git clone` into the wrong directory, which leaves nothing in any
tree for a check to read until the clone exists. After the fact it is
caught: [precedent_session_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_session_check.py)'s "cloned exactly once" row fails on
two working trees for one source and names which one the config reads.
