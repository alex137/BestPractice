---
title:         Precedent commands, session setup and check levels, in full
kind:          reference
status:        current
opened:        2026-09-28
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       "The long form of AGENTS.md's command list, session-setup notes and check levels, moved here word for word when AGENTS.md became an index (Morgan, 2026-09-28; check levels 2026-09-29)."
---
# Precedent commands, session setup and check levels, in full

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
  `Booked` is the one to lead with (Morgan, 2026-09-29), and `Go update`,
  its older name, still works whether or not a merge is literally in the
  picture.
  `Approved` is also an ordinary adjective, so *"the approved plan of
  record"* is not the command.
  **Neither is required for the authorization to exist** —
  "sold, ship it" reads as this command as plainly as the phrase does.
  What the phrase buys is certainty:
  say one of them and the chain runs, full stop. Where it's absent and the
  sentence could honestly go either way, say the read out loud and get it
  confirmed before the push, the pull request, or the merge — commit locally
  regardless, and hold only the shared-branch steps on the answer.
- **"Push directly to [branch]"** (push-directly, retired 2026-09-30: a
  direct push is already Booked's default; the long form below is history)
  — the classification's own override, named: skip it outright and push
  straight to that branch, no PR, whatever Booked (`Go update`) would otherwise call
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
- **"Root issues"** / **"Root fixes"** ([root-issues](../practices/root-issues.md))
  — look back over **everything this session has done**, warnings and its
  own fixes and band-aids included, and hand back each one that also
  belongs in Precedent, a precedent-* repo, the template that generates the
  file, or another related repo, **each as a `Prompt Please` block**. Ones he may
  already have passed on are given anyway, marked if this session raised
  them before; none found is said in one line. It replaced **"Upstream
  fix"** on 2026-10-01: whether a fix removes its cause is now answered for
  every fix without being asked ([upstream-fix](../practices/upstream-fix.md)).
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
  2026-09-14 — its last step runs Booked's (`Go update`'s) chain on what the update
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
turn one ran with every shared and individual practice silently absent. Check
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
Until one of the two routes works, every personal and shared-set practice in force
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
of a multi-source session, since a shared source resolves as a sibling clone —
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

## Two check levels

Moved here word for word from [AGENTS.md](../AGENTS.md)'s "Working in this
repo" section by a reduction pass (Morgan, 2026-09-29 -- "Reduction pass"),
when that file had about 10% headroom left under its ceiling. Only the
relative links changed, to resolve from `spec/`. AGENTS.md keeps a
five-line index entry that points here.

**Two check levels** (practice `two-check-levels`): **light check** is
`python3 tools/doc_lint.py` on the markdown you touched — the fast,
constant pass above, run before every commit without thinking about it.
**deep check** is the full gate suite run before push or merge:
`python3 tools/verify_harness.py --as-ci`, `python3 tools/doc_lint.py`,
`python3 tools/leak_gate.py`, `python3 tools/precedent_check.py`, and
`python3 tools/doc_sync.py` -- **all five in one command:
`python3 tools/precedent_push_check.py`**, which is also what
`push-check-gate.sh` runs before any `git push` a session makes. A pass
is recorded against the tree, so running it first makes the push
instant; skipping it makes the push wait for it. **Run bare, with no
destination named, it checks what a push to your landing branch gets**
(Morgan, 2026-10-01, strength: assented: a session ran it bare before every
landing on pre-staging and paid the full suite each time); `--tier full`
asks for everything, and where the landing branch takes the quick tier it is
refused unless given a reason, `--because "<why>"` (Morgan, 2026-10-01,
strength: decided: the same day, a session still typed `--tier full` before
every pre-staging landing, and wrote it into its helpers' briefs). **Which of the two a push
gets depends on the branch** ([spec/BRANCH_TIERS_PLAN.md](../spec/BRANCH_TIERS_PLAN.md)):
a push to `staging` or `main` runs the deep check; a
push to any other branch runs the basic tier -- the lint, the leak gate
and the commit author, date and trailer checks, seconds -- unless the person's
`branch_push_checks` says `full`. A push or pull request into
`pre-staging` also checks the files it changes, and nothing more, in
seconds ([checks-follow-the-tier](../practices/checks-follow-the-tier.md)). A pull request merged through GitHub
gets the same check at its base branch's tier, from `merge-check-gate.sh`.
`python3 tools/precedent_branches.py` says what this checkout resolves. **What matters is `0 failed` and
`0 violated`, never a passed/skipped count** — those grow as checks are
added, so a figure written down here goes stale by design; see
[spec/ATTENTION_CEILING.md](../spec/ATTENTION_CEILING.md)'s closing section,
which says the same thing and records the audit that found a hardcoded
one already wrong. Light check gates a commit; deep check gates a push.
**A failing test the deep check ran is not "pre-existing" when a source
shipped it**: `tools/checks/tests/run_all.sh` names each failing test's
source, and that source is where it gets fixed and reported
([two-check-levels](../practices/two-check-levels.md)). A practice source's
own push check also runs its tests shaped like a consumer
([tools/precedent_consumer_shape.py](../tools/precedent_consumer_shape.py)).
**`--as-ci` is not decoration**: CI shards the harness across two jobs
using variables a plain local run never sets, so the bare command
certifies a shape nobody ships — it hid a crash on 2026-09-21 that turned
both CI jobs red on a locally green tree. The two shards partition the
suite, so the pair costs about what one run costs (measured 4m01s against
~4m20s, 2026-09-22). It reproduces CI's command SHAPE, never CI's
environment: a local session resolves private sources CI cannot, so green
here means the sharding is not what breaks, not that CI will be green.
