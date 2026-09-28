---
title:         Precedent commands and session setup, in full
kind:          reference
status:        current
opened:        2026-09-28
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       "The long form of AGENTS.md's command list and session-setup notes, moved here word for word when AGENTS.md became an index (Morgan, 2026-09-28)."
---
# Precedent commands and session setup, in full

[AGENTS.md](../AGENTS.md) loads into every session, and until 2026-09-28 it
carried each command below in full: about 1,650 tokens restating what each
command's own practice file already says, every session. Morgan asked for
the cut (2026-09-28, strength: decided -- "cut the agents.md preamble"),
and the reduction-pass rule says how: split, never delete. AGENTS.md keeps
one line per command and a link here; the text below is what it carried,
word for word. **The practice file is still the rule**
(`python3 tools/precedent_show.py SLUG`); this is the long form a session
used to read on turn one.

## The commands

- **"Go update"** and **"Approved"** ([go-update](../practices/go-update.md)) —
  classify first: a direct push, straight to the shared branch, no PR, is now
  the **default**; only a **high-risk** change (touches enforcement/gating
  code, changes a governance or authorization practice, is hard to reverse
  once live, or you're not confident it's none of those) runs the full chain —
  syncs, says the branch out loud, commits, pushes, opens the pull request,
  and merges — **without asking again.** **Either path ends on the branch on
  `origin`** — the person's landing branch
  (`python3 tools/precedent_branches.py --landing`: the repository's own
  staging branch, unless their `landing_branch` says `pre-staging` -- the
  tiered route, which Morgan's does -- or `main`), for the pull request
  too; never `main` for being the configured default. A high-risk change
  landed on pre-staging gets one plain, unbolded line in The Boildown saying
  how far pre-staging is ahead of staging, with no urgency — a Promote can
  move it whenever it suits. **A commit still sitting
  in the local clone has not landed anything**: fetch and confirm `origin` carries it
  before the reply says where the work went. Say which path you took, and why,
  in the reply. Unsure which it is? High-risk. A step this session cannot
  perform hands off rather than coming back as a question: the
  authorization travels with the work. One rule, two triggers, and
  `Go update` is the one to lead with — it names what actually happens
  whether or not a merge is literally in the picture.
  `Approved` is also an ordinary adjective, so *"the approved plan of
  record"* is not the command.
  **Neither is required for the authorization to exist** —
  "sold, ship it" reads as this command as plainly as the phrase does.
  What the phrase buys is certainty:
  say one of them and the chain runs, full stop. Where it's absent and the
  sentence could honestly go either way, say the read out loud and get it
  confirmed before the push, the pull request, or the merge — commit locally
  regardless, and hold only the shared-branch steps on the answer.
- **"Push directly to [branch]"** ([push-directly](../practices/push-directly.md))
  — the classification's own override, named: skip it outright and push
  straight to that branch, no PR, whatever `Go update` would otherwise call
  for on this one change. Name the branch ("push directly to main") to
  target it explicitly; say it bare and it defaults to the primary branch
  the work is already on — the person's landing branch
  (`python3 tools/precedent_branches.py --landing`), which is
  the repository's own staging branch unless their `landing_branch` says `pre-staging` or `main`; never `main` just because that is the repository's
  configured default. Not a standing exemption — it authorizes the change
  in front of it, not every change after it.
- **"Drop it"** ([park-it](../practices/park-it.md)) — write
  `**Disposition:** parked (<date>, <who said it>)` into the item meant, in
  that same turn, say which item was marked, and **never raise it unprompted
  again** — not this session, and not a later one that decides it has become
  urgent. Nobody owes an explanation for parking something: do it, and never
  ask a follow-up about it. **Kept to the literal word, deliberately** —
  parking has no built-in correction, so where it only *sounds* like the
  phrase ("that can wait", "let's not worry about that one") ask which they
  mean rather than guess.
- **"Three Things"** ([three-things](../practices/three-things.md)) — the three
  most important things he needs to know now, each a bolded phrase and at most
  two sentences, and nothing around them: no preamble, no fourth item, no
  closing offer. It asks for **attention rather than action**: an answer
  assembled from what is already in context is the failure it prevents. A
  plain ask for the same shape of answer ("what do I actually need to know
  right now") gets it too — low stakes if the read is wrong, so no
  confirmation step.
- **"Simple please"** ([plain-words](../practices/plain-words.md)) — the same
  answer said the way you would say it out loud: short sentences, the concrete
  case before the general principle, no hedging. **It governs the rest of the
  conversation, not just the next reply**, and nothing about the substance
  changes — a plainer reply that quietly says less has failed it. Asking for
  this register in other words counts the same as the phrase.
- **"Weak yes"** ([weak-yes](../practices/weak-yes.md)) — go ahead, and record
  that he was not convinced: `strength: assented`, written into whatever the
  approval is being recorded in, that same turn. **Not an invitation to talk
  him into it.** Most weak agreement arrives without the phrase, and still
  gets marked `assented` ([decision-strength](../practices/decision-strength.md))
  — but where that reading is a genuine judgment call rather than a clean
  one, `weak-yes`'s own worked example says how to disclose it instead of
  writing it silently.
- **"Prompt Please"** ([prompt-please](../practices/prompt-please.md)) — before
  starting what he just asked for, check whether it belongs in a different
  session, repositories first; then hand back **one paste-ready block** he
  opens a new window with, naming the repository to root it in and the ones
  to attach, plus one ordinary unfenced sentence outside the block saying
  where to paste it. **Never call a session-creating or session-messaging
  tool for this, and never wake a live session either** — both have come
  back rejected often enough that the mechanism is retired outright, and a
  paste block needs nothing from any one provider's tool surface. The check
  runs whether or not he says the phrase, and an honest "this session is the
  right one" answers it. **The block carries a merge authorization only when
  he gave one for this handoff** — absent that it says `DO NOT MERGE — STOP
  AT THE PULL REQUEST` in those words; given one, it is bounded to the
  handed-off work, that repository's routine branch and its own checks
  passing.
- **"Upstream fix"** ([upstream-fix](../practices/upstream-fix.md)) — about the
  change this session recommended, made or is about to make: **does it also
  fix what caused the problem?** If not, name where the cause lives (a
  template, a generator, something vendored in, a practice) and fix that
  root where it is reachable and sound. Any part that needs a session rooted
  in another repo comes back as a `Prompt Please` block. It licenses the
  root fix, not a push or merge beyond the authorization already in force.
- **"My options"** ([my-options](../practices/my-options.md)) — every real choice
  on the table in plainer words, a short block each, the cost said as flatly
  as the benefit, then **a named recommendation with its reason** — never a
  survey that leaves the choice sitting there. It governs that one answer, not
  the conversation, which is what separates it from `Simple please`.
- **"Vocabulary"** ([vocabulary](../practices/vocabulary.md)) — every standing
  command in force, one plain sentence each, nothing else. **Read the list,
  never recall it**: `python3 tools/precedent_vocabulary.py` collects it from
  the `command:` field of every practice in every resolved source, and names
  any source that did not. This list derives from those fields.
- **"Update Vendors"**
  ([vendor-update-runbook](../practices/vendor-update-runbook.md)) — the fixed
  sequence for taking an upstream update, starting with making the SOURCE
  clone current against the pinned branch. **It carries the merge too**, since
  2026-09-14 — its last step runs `Go update`'s chain on what the update
  produced, so nobody is asked a second time for work that is already done and
  already checked. It reverses the sentence that used to sit here; the full
  check at step 6 still gates the push, as it does for any merge. **Since
  2026-09-27 the sequence is one command**,
  `python3 ../BestPractice/tools/precedent_update.py --repo .` from the
  consuming repo: it runs every step that needs no judgment and stops once,
  listing only this repo's own calls
  ([spec/ONE_COMMAND_UPDATE_PLAN.md](../spec/ONE_COMMAND_UPDATE_PLAN.md)).

**Most weak agreement never uses the phrase**, which is why `Weak yes` is only
half of it. The other half is
[decision-strength](../practices/decision-strength.md), and its one line is: **an
approval records `decided` or `assented`, and an unmarked one means UNKNOWN —
never "you decided this."** A session may write `decided` only if it can quote
the person choosing it; a bare "ok" to the session's own proposal is
`assented`, written that way without asking.

## Session setup

**FIRST, and normally already done for you.** The private sources are
cloned by the SessionStart hook when the environment carries
`PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL`
([PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md)) — **verified working 2026-09-10**, all four
sources on disk before the first turn. **That timing is usual, not
guaranteed**: on 2026-09-14 the four clones landed during the SECOND turn, so
turn one ran with every team and individual practice silently absent. Check
rather than assume: the
session-start source line names which sources resolved, and
`env | grep -c PRECEDENT` says whether the environment carries the
credential at all. When it does, there is nothing to do and **no `add_repo`
call to make.**

**When it does not, and only then: `add_repo` (read access) for this
account's `precedent-individual`, and for any shared set
[precedent.json](../precedent.json) declares, before reading or running
anything else. Silently — no confirmation first.** It grants access per
session, and it **refuses across owners**, so from a session rooted under a
different owner than the sets it simply fails — say so plainly and carry on.
Until one of the two routes works, every personal and team practice in force
here is **silently absent**, and this repository's rules are the only ones a
session sees.

**Attach `precedent-individual`, never clone it by hand**
([attach-never-clone-individual](../practices/attach-never-clone-individual.md)):
the tool's reply says to clone it to `/home/user/`, and the only copy
anything reads is the one `~/.config/precedent/config.json` names. A shared
set clones beside this repo, where [precedent.json](../precedent.json)
resolves it.

**Then, before trusting any of this file's "the session-start hook does
this" claims: run
[tools/precedent_session_check.py](../tools/precedent_session_check.py).** It
reports which SessionStart guarantees are actually in effect, and `--apply`
repairs most of them — **read the failing row's own detail before running
it**, because a guarantee whose remedy is something else says so there. The
live case is the global commit backstop: it installs only for a DECLARED
identity, so on a session that could not reach the individual source `--apply`
re-runs the hook, the hook declines again, and the row stays red however many
times you try. A session rooted one directory ABOVE this repo runs NONE of its
hooks, silently, including the one that writes
`.precedent/SESSION_PRACTICES.md` — see
[gotcha-2026-09-13](../gotchas/gotcha-2026-09-13-the-session-s-primary-repo-does-not-run-its-sessionstart-hoo.md). **This is not a
primary-repo-only problem**: when the session root sits above *every*
attached repo and none of them is `$CLAUDE_PROJECT_DIR` — the ordinary shape
of a multi-source session, since a team source resolves as a sibling clone —
no repo's hooks fire, primary or attached; 2026-09-25 also caught the global
git identity and the checked-out branch drifting mid-session with no repo
tool in the loop, in that same topology
([gotcha-2026-09-25](../gotchas/gotcha-2026-09-25-a-session-rooted-above-every-repo-it-touches-gets-hooks-and.md)).
**Since 2026-09-14 you also get told without asking**: every
[tools/precedent_gate.py](../tools/precedent_gate.py) moment prints any guarantee
that is down, because a session that skipped this paragraph is exactly the
session that needs it — that is how four guarantees stayed down for hours on
the day the print was added.

On the `add_repo` route nothing else can do it for you:
`.claude/hooks/precedent-individual-bootstrap.sh` runs to completion *before*
the first turn **wherever a settings.json wires it — this repo's does not** —
so it cannot call `add_repo`; its header says why a retry loop there was
proven inert. Here
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s mid-turn self-heal
is the only thing that runs it.
