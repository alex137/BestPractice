<!-- Last updated: 2026-09-21 (Buenos Aires), first version -->

# Shared Practice Sets

*The question this document answers:* **I have a rule I want in some of my
projects but not all of them — where does it go?**

Short answer: **a shared set**. Make one, declare it in the projects that
should follow it, leave it out of the ones that shouldn't. This page is
about how, and about why you'd want several rather than one.

## The Four Kinds of Rule, and Where Each Lives

Every practice a session obeys comes from one of four places. They differ
in **who they bind**, and that is the only thing that decides where a rule
belongs.

| Kind | Binds | Where it lives | You choose per project? |
|---|---|---|---|
| **Universal** | everybody using Precedent | this repository | no — it comes with the tool |
| **Shared** | whoever declares it | your own `precedent-shared-<subject>` repository | **yes** |
| **Individual** | you, everywhere | your own `precedent-individual` repository | **no — see below** |
| **Repo-local** | one project | that project's own `local/practices/` | it is already only there |

**Your individual set goes into every project you touch.** That is
deliberate, and it is the point of having one: how you like to be talked
to, how you want sessions titled, what you want confirmed before it
happens — those follow you. They are not facts about a project, so a
project never has to ask for them.

**Which is exactly why a rule you want in *some* projects is not an
individual rule.** Put it in your individual set and it turns up
everywhere, including the repositories where it is wrong. Put it in a
shared set and you decide, per project, one line at a time.

**Want your own rules, just for you, in project X but not project Y? Then
go make your own `precedent-shared-*` set.** It does not have to be
shared with anybody. "Shared" names the *mechanism* — a set any number of
projects can declare — not an obligation to hand it to other people. A
shared set with exactly one reader is a completely ordinary thing to
have, and it is the right shape for "this rule, these repos".

## Make One

```
python3 tools/precedent_bootstrap_source.py \
    --level shared --name precedent-shared-<subject> \
    --dest ../precedent-shared-<subject> \
    --approver "Your Name:your-github-handle"
```

That gives you a real, working set: the practice format, a vendored engine
that can check itself, its own CI workflow, and the manifest that keeps it
refreshable. It does **not** create the GitHub repository — that stays a
step you take, on purpose, because a tool that creates remotes is a tool
that creates them by accident.

Then push it, and declare it in each project that should follow it, in
that project's `precedent.json`:

```json
"sources": [
  {"level": "universal", "name": "precedent", "path": "precedent/universal"},
  {"level": "shared",    "name": "precedent-shared-<subject>",
                         "path": "../precedent-shared-<subject>"},
  {"level": "repo-local", "name": "local", "path": "local"}
]
```

A project that does not list it does not get it. That is the whole
control.

**`--level team` still works** and means the same thing — it is the
pre-2026-09-18 spelling. Everything the engine prints says `shared`.

## Name It for Its Subject, Not for a Group of People

`precedent-shared-writing`, `precedent-shared-repo-maintenance`,
`precedent-shared-working-style`. **Not** `precedent-shared-my-team`.

A subject-named set answers "should this project follow it?" by itself: a
project that does no writing does not declare the writing set. A
group-named set answers nothing — everyone on the team declares it in
everything, and it becomes a second individual set with extra steps.

Subjects also split cleanly when they grow. A set that is really two
subjects can become two sets, and the projects that only wanted one half
stop carrying the other.

## Make Them. Share Them. This Is the Good Part.

**We want an ecosystem of shared sets** — public ones anybody can declare,
private ones inside a company or a family or a two-person project. If you
have worked out how something should be done and written it down properly,
that set is worth more outside your own repositories than inside them.

**Declaring somebody else's set puts its rules in force.** Public or
private makes no difference to that: if you include it, you follow it.
That is the deal, and it is what makes a set worth publishing — nobody has
to wonder which parts you meant.

**Don't want all of it?** Then don't declare it — clone it and keep your
own version. A set is plain files in a git repository; forking one is the
normal answer to "I like most of this". It is a far better outcome than a
set that hedges every rule so nobody has to disagree with it.

## What It Costs

Every practice in force is read by every session, before it does anything.
That budget is real and it is small — see
[session-load-budget](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/practices/session-load-budget.md),
which declares a ceiling on each always-loaded file and fails the build
when one is exceeded.

Practically: a practice that must be in front of a session always is
**resident** and costs tokens on every turn. Most practices are
**on-demand** — reached by the occasion index or by the files they apply
to — and cost nothing until they are relevant. Writing a rule as
on-demand where it honestly is on-demand is how a set stays affordable to
declare, and it is the main thing that makes one set pleasant to adopt and
another a tax.

## A Private Set in a Public Project

A shared set can be private. A project that declares one and is itself
**public** will not render that set's practice text into its tracked
[AGENTS.md](../AGENTS.md) — publishing it there would publish the set. The generated
block says so out loud rather than quietly dropping it.

If the gate flags a directory your set legitimately has — a drafting
`candidates/` folder, say — declare it once in your own
`precedent-source.json` rather than weakening the rule for everybody:

```json
"leak_structural_exempt": [
  {"path": "candidates",
   "reason": "this set's own drafting outbox; reviewed before publication"}
]
```

**The reason is mandatory.** An entry without one is ignored, so the
exemption cannot be taken silently.

## Telling Whether Your Tree Is Machine-Dependent

Because an individual set resolves through your machine's user-level
config rather than through the project's `precedent.json`, **the same
project installed by two people resolves two different sets of
practices**. That is the design, not a bug — but it is worth being able to
see.

Since 2026-09-21 the generated loader block says so, in the projects where
it is true: it names how many practices came from an individual source and
states plainly that the tree is machine-dependent. A project with no
individual practice in force — every public set, every CI checkout —
renders exactly as it did before.

If a diff surprises you, that line is the first thing to read.

## Related

- [FOR_DEVELOPERS.md](FOR_DEVELOPERS.md) — working in a Precedent project
  day to day, including making your own set
- [ADOPTING.md](ADOPTING.md) — the non-technical introduction
- [spec/BOOTSTRAP_NEW_SOURCES.md](../spec/BOOTSTRAP_NEW_SOURCES.md) — the
  full procedure
  [precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py)
  mechanizes, including the
  parts that stay a human step
- [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) — what a set's own CI costs and
  how to control it
