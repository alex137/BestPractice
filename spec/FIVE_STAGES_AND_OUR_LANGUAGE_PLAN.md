---
title:         Five stages and our language -- one ladder for work, one page of words
kind:          proposal
status:        accepted
opened:        2026-09-27
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Two linked changes. First, a short page of the words this project uses (practice, universal set, individual set, shared set, full set, repo-local, primary branch, feature branch, and the stage names), printed as a second list under Vocabulary, plus a cleanup that retires 'team set' for 'shared set' everywhere live. Second, the work ladder: five stages, Consider, Act, Booked, Debut, Produce, each reachable as 'Promote N', by its word or by its synonym, each read back aloud before it runs. Optional for everyone; required for Morgan through his individual set. Go update becomes step 3, Booked, and Consider sizes the plan from a one-line plan up to a full write-up."
---

# Five stages and our language -- one ladder for work, one page of words

Morgan approved the direction on 2026-09-27 and asked for this write-up in
the same message ("Go update"), then settled the remaining choices on
2026-09-28. Nothing here is built yet; the build order is in
[What gets built, in order](#what-gets-built-in-order).

This plan came out of one brainstorm session. It is written for a reader who
was not there.

## Contents

- [The problem](#the-problem)
- [Part 1 -- Our language](#part-1----our-language)
- [Part 2 -- The five stages](#part-2----the-five-stages)
- [Part 3 -- Retiring "team set"](#part-3----retiring-team-set)
- [Analysis -- what was tried, and the holes found](#analysis----what-was-tried-and-the-holes-found)
- [What gets built, in order](#what-gets-built-in-order)
- [Open questions](#open-questions)
- [Decision record](#decision-record)

## The problem

**Three problems, found in one conversation.**

1. **There was no word for all the practice sets a person works under.**
   Every repository he works in follows the universal set (this repository's
   own catalogue), his own individual set (`precedent-individual`), and any
   shared sets it declares (today `precedent-shared-repo-maintenance`,
   `precedent-shared-writing` and `precedent-shared-working-style`). He
   called the four non-universal ones "the four precedent-star files", and
   there was no word for everything together. Meanwhile the older word **"team set"** still appears about 390 times
   across roughly 140 markdown files here, although the code switched the
   level name to `shared` on 2026-09-18
   ([tools/precedent_resolve.py](../tools/precedent_resolve.py) keeps
   `LEVEL_ALIASES = {'team': 'shared'}` so older repos still load). Two
   words for one thing, and nothing that names the whole.

2. **Vocabulary lists commands only, and people need the nouns too.**
   [practices/vocabulary.md](../practices/vocabulary.md) prints every
   standing command and "nothing else".
   [GLOSSARY.md](../GLOSSARY.md) has around 80 terms -- too many to learn
   from. Someone new cannot follow a conversation about "the individual set"
   or "pre-staging" without a short list of the words that matter.
   "Primary branch" is listed as a command today, but it names a thing, not
   an action.

3. **The steps from idea to production are scattered and easy to lose work
   between.** Today `Brainstorm`, `Write it up`, `Go update`, `Push directly`
   and `Promote` each cover one piece, with no single picture of the order.
   The concrete failure: the branch `claude/graduate-synonym` (BestPractice)
   holds two finished commits from 2026-09-26 -- "Graduate" as a second word
   for Promote and "Spec it out" for Write it up -- that never reached
   pre-staging. Morgan: *"It was an accident that that wasn't merged in."*
   The reply gate has printed a NOT YET LANDED line for exactly this since
   2026-09-21 ([tools/precedent_gate.py](../tools/precedent_gate.py)), and
   the branch was stranded anyway. **A warning alone did not stop it.**

## Part 1 -- Our language

### The words

One short list of the nouns a person needs to follow a conversation here.
Each gets one plain line.

| Word | What it means |
|---|---|
| **practice** | A rule -- one file, with the rule, the reason, and the story of how it came about. |
| **universal set** | The practices everyone gets. This repository's own catalogue, named `precedent`. |
| **individual set** | The practices just for you. Usually a repository named `precedent-individual`. |
| **shared set** | Practices a group of people share. A repository may declare none, one, or several. |
| **full set** | Every practice set in force for you: the universal set, your individual set, your shared sets, and the repo-local practices of the repository you are in. |
| **repo-local** | Belonging to the repository you are working in -- your work repository, the one with BestPractice vendored into it. Its own practices, kept in its `local/` folder, are its repo-local practices, and apply only there. |
| **in force** | A practice that actually applies here, right now. |
| **source** | Where a set of practices comes from, usually a repository. |
| **level** | Whether a source is universal, shared, individual, or repo-local. |
| **primary branch** | The one shared branch regular work lands on. |
| **feature branch** | The short-lived branch one session works on, on GitHub -- the kind named like `claude/<topic>-<random>`. GitHub's own word for it; some teams say "topic branch". It survives a lost container but is easy to forget, and it is deleted once merged. |
| **pre-staging, staging, main** | The three branch tiers ([spec/BRANCH_TIERS_PLAN.md](BRANCH_TIERS_PLAN.md)). In the stages below, `main` is **production**, and step 5, Produce, is what puts work there. |
| **the five stages** | Consider, Act, Booked, Debut, Produce -- see Part 2. |

**"Full set" means everything**, the universal set included -- Morgan's
call on 2026-09-28. It is the natural reading of "full", which was the
worry with the earlier definition that left the universal set out. The four
repositories he edits together have no single word of their own; "your
individual and shared sets" is short enough.

**"Repo-local" already exists as a level** in the code and in
[practices/source-naming.md](../practices/source-naming.md): a repository's
own practices, in its `local/` folder. The definition above keeps that
meaning and adds the plain one -- the repository you are working in -- so
the two never disagree.

### Where the words live

- **One page, "Our language"**, a new OUR_LANGUAGE.md in
  [documentation/](../documentation/), linked
  from [README.md](../README.md) and [SETUP.md](../SETUP.md), because a new
  person meets these words before anything else.
- **Vocabulary prints two lists**: the commands first, as today, then
  "Our language". The Vocabulary rule's "and nothing else" changes to allow
  the second list.
- **One source, never two copies.** The definitions live in one small
  registry (proposed: `tools/our_language.json`), and both the page and
  [tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py) render
  from it, the way [MAP.md](../MAP.md) is generated rather than hand-kept
  (practice: registry-source-of-truth). A hand-typed list in two places is
  how "team" and "shared" drifted apart in the first place.
- **"Primary branch" moves** from the command list to the second list. Its
  practice keeps its trigger -- a person can still ask "which is the primary
  branch?" -- but it stops being listed as something you tell a session to
  do.
- [GLOSSARY.md](../GLOSSARY.md) stays as the full reference and links to
  the page for the short version.

## Part 2 -- The five stages

### The ladder

| # | Word | Synonym | What happens | Where the work ends up |
|---|---|---|---|---|
| 1 | **Consider** | Plan | Decide how much planning this needs, then do that much. | Nowhere yet, or a plan |
| 2 | **Act** | Build | Make the change. | The session's feature branch on GitHub |
| 3 | **Booked** | Shared Save | Move it from the feature branch to pre-staging. After this it **won't be lost**. | pre-staging |
| 4 | **Debut** | Test Readiness | Move pre-staging into staging, with the full checks. | staging |
| 5 | **Produce** | Make live | Move staging into main -- production -- with the full checks plus the GitHub test. | main (production) |

**Each stage answers to three names: its word, its synonym, and "Promote
N".** "Booked", "Shared Save" and "Promote 3" all mean the same thing. These
are not exact phrases to match -- each is read for what the message means
(below), so other wordings count too. Morgan kept one word for the whole ladder on purpose: *"I want one
word to just use everywhere ... promote is good enough"* -- step 1 is
promoting an idea into something worth preparing, even though nothing moves
between branches until step 3.

**The words follow a theater production**: consider it, act it, book it,
debut it, produce it. The last step is a verb like the others ("Produce"),
while its result keeps the noun people already use for it: the work is in
**production**. That carries the "go live" feel the last step needs, without "launch", which is common in tech and usually means
something much bigger.

**"Graduate" is another word for Promote**, and **"Spec it out" another word
for Write it up** -- the two words stranded on `claude/graduate-synonym`
(BestPractice), folded in here rather than merged on their own.

### Every stage is read back before it runs

Every time a stage is triggered -- by its word, its synonym, "Promote N",
or a plain request that means the same -- the session says the full version
out loud first, naming the repository and the branches:

> Now Promote 3: Booked, the Shared Save -- moving
> `claude/precedent-terminology-vs3o6q` into pre-staging (BestPractice).

When one request covers several stages, the read-back names all of them:
*"Now Promote 3 then 4: Booked, the Shared Save, into pre-staging, then
Debut, Test Readiness, into staging (BestPractice)."* The existing
[Promote](../practices/promote.md) already opens with *"Now promoting from
pre-staging to staging"*; this extends that to every stage and adds the
stage's name.

### Reading the request -- intent, never a keyword match

**No stage fires on a text search for its word.** Morgan, on the last step: the
session *"should not just do a simple grep for that exact word ... I might
use it in a slightly different grammatical way or ... I may not use that
exact word ... you have to apply your intelligence."* That is how every
command here is already read ([practices/go-update.md](../practices/go-update.md)),
and it matters most at step 5, which changes main. Where a message
could honestly go either way, the session says its reading and confirms
before any shared-branch step.

**The same step can be asked for many ways**, and all of them mean it:
"Debut", "Test Readiness", "Promote 4", "promote pre-staging to staging", "move BestPractice
staging to main", "book it into precedent-individual". A request may name
the repository, the branch, or the from-and-to pair. **A named step wins
over any guess**, as Promote's `--to` already does.

### A bare "Promote"

**A bare Promote means the next step this work has not done yet, and it
never skips a step.**

- If more than one move is possible and the request does not say which,
  **take the lowest**. Morgan: *"If I'm ambiguous, start at the ... lowest
  one."* If the feature branch, pre-staging and staging each hold
  different work, the bare Promote means Booked: the feature branch into
  pre-staging.
- Asking for a higher stage runs the lower ones first. "Debut" on work still
  on the feature branch runs Booked, then Debut, and the read-back says so.
  (Promote already lands the session's own unsaved work first; this keeps
  that.)
- A bare Promote never sends finished work back to Consider.

### Booked asks one question: is it ready?

Booked usually comes in the middle of a busy session, so it is the step most
likely to be misread. **Before booking, the session judges whether the work
is actually ready** -- finished, checks passing, nothing half-edited. If it
thinks the work is not ready, it says so and asks what was meant, instead
of booking it. Morgan: *"that could be a source of misunderstanding if I
say that, but you don't think it's ready, maybe I meant something else. Or
... I meant it at ... a higher level"* -- for instance, moving work booked
earlier up to staging. This is the one stage that may stop to ask.

### Consider -- how much plan

**Consider always happens, and it is usually small.** It decides how much
planning the work deserves, from four sizes, lightest first, and names its
choice in the read-back ("Now Promote 1: Consider -- a one-line plan").

**The session chooses the size itself, without asking** -- from the context
and how complex the work is, and from whatever guidance Morgan gives in
passing: *"Consider this, it's a brainstorm"* settles it. Asking every time
would add a round trip, and the read-back already shows the choice, so a
wrong pick is corrected in one word.

| Size | What it produces | When |
|---|---|---|
| **One-line plan** | One sentence in the reply: what will change and where. Then straight to Act. | Tiny changes -- a typo, a link, a one-line fix. Most work. |
| **Brainstorm** | The existing command: think it through in the session and write nothing to the repository ([practices/brainstorm-holds-commits.md](../practices/brainstorm-holds-commits.md)). | The idea itself is still open. |
| **Plan it** *(new)* | The middle ground: a written plan in the session -- numbered steps, the risks, what "done" looks like, what is out of scope. More than a brainstorm, far less than a write-up. No file: it is handed back as **one paste-ready prompt**, so it can be copied into another session for a second opinion. | Real work, clear enough to build in this session. |
| **Write it up** / **Spec it out** | The existing command: a full report committed to the repository, as [practices/write-it-up.md](../practices/write-it-up.md) says -- like this file. | A detailed plan is needed: big or cross-session work, or anything someone else will pick up. |

**The one-line plan is fine, and it matters most.** Morgan: *"Very, very,
very important. We don't want to have lots of documents ... when it's not
needed."* Forcing a bigger planning step on a typo is friction; the
one-line plan is how Consider stays cheap. Consider moves up a size only
when the work needs it, and says why when it does.

"Plan it" is the one new command here and gets its own practice file.
**Its plan is not saved to the repository** -- work that spans sessions is
Write it up's job -- **but it is always given as one self-contained,
paste-ready prompt**: a fenced block that says where to paste it (a new
session, which repository to root it in, what to attach), opens by naming
the session that wrote it (practice: seeded-prompt-names-its-origin), and
asks the receiving session for its critique of the plan. Getting a second
session's feedback on a plan is then one copy and one paste.

### Who it applies to

- **Optional for everyone.** The stages ship in the universal set, so anyone
  can say "Booked" or "Promote 4". Nobody has to. Morgan: *"people can use
  staging, but they don't have to ... I just don't think I can force Alex
  ... into this framework."* A repository or person without pre-staging or
  staging simply has fewer stages: when the landing branch is staging,
  Booked lands on staging and Debut has nothing to do; when it is main,
  Booked lands in production. The read-back says which stages were skipped
  and why.
- **Required for Morgan**, through a practice in his individual set:
  - no Act without a Consider first, where a one-line plan counts;
  - every stage read back;
  - the archive guard below.

### What happens to Go update

**This is the biggest change in shape.** Today `Go update` (and its twin
`Approved`) is the one broad "finish this" command: it classifies the
change, lands it on the person's landing branch -- directly, or through a
pull request for a high-risk change -- confirms on GitHub that it arrived,
and never asks a second time. It also means "finish whatever this needs"
when the work is not a branch move at all. Around 30 other practice files
lean on it: [Promote](../practices/promote.md) runs it first,
[Update Vendors](../practices/vendor-update-runbook.md) ends by running its
chain, [Prompt Please](../practices/prompt-please.md) hands its
authorization to another session, and [Push directly](../practices/push-directly.md)
is its override.

**On the ladder, Go update is step 3, Booked.** "Go update", "Approved",
"Booked", "Shared Save" and "Promote 3" become five names for one step: move
this session's work from its feature branch to the landing branch, where it
won't be lost. For Morgan that is pre-staging. What that changes:

- **It stops at pre-staging.** Go update never reached further anyway,
  because Morgan's landing branch is pre-staging; the ladder makes that
  explicit, and staging and main are Debut and Produce, separate steps.
- **It is read back as a stage**: *"Now Promote 3: Booked, the Shared Save
  -- ..."*, not only "landing on pre-staging".
- **It may stop to ask, once.** Go update today never asks. Booked judges
  whether the work is ready first, and says so when it thinks it is not
  (above). That is a real change to Go update's promise, and it applies only
  where the ladder is in force -- for Morgan.
- **What stays exactly as it is:** the classification (a direct push by
  default, the full pull request chain for a high-risk change -- that pull
  request targets pre-staging), bringing pre-staging in before the push,
  confirming the result on GitHub, `Push directly` as the override, and the
  broad "finish whatever this needs" meaning for work that is not a branch
  move.

**What Go update does today, and where each piece goes.** Everything
[practices/go-update.md](../practices/go-update.md) does today is kept;
most of it moves into a new Booked practice file, four pieces become common
to every stage, and one becomes its own small practice because two commands
share it.

| What Go update does today | Where it goes |
|---|---|
| **Decides whether the change is high-risk.** High-risk means it touches enforcement or gating code, changes a governance or authorization practice, is hard to reverse once live, or the session is not confident it is none of those. | **Its own small practice**, referenced by both Booked and [Push directly](../practices/push-directly.md), because both depend on it and it should be written once. The four tests do not change. |
| **Ordinary change: pushes straight to the landing branch, no pull request** (the default since 2026-09-20). | **Booked**, unchanged. |
| **High-risk change: the full chain** -- sync, say the branch, commit, push, open a pull request into the landing branch, merge it. | **Booked**, unchanged. For Morgan the pull request targets pre-staging, as it already does. |
| **A direct instruction about this one change wins** ("skip the PR", "open a PR for this"). | **Booked**, unchanged. `Push directly` stays the named form of "skip the PR". |
| **Works out the landing branch** (`precedent_branches.py --landing`: pre-staging, staging or main, from the person's `landing_branch`). | **Booked**, unchanged; the tool does not change. |
| **Brings pre-staging in first** (`--sync-pre-staging`, then merging `origin/pre-staging` before the push). | **Booked**, unchanged. |
| **Runs the checks**: the light check before the commit, the push check at the target branch's tier (basic for pre-staging, full for staging and main). | **Unchanged** -- the hooks run them, whatever the command is called. |
| **Says the target branch out loud** before pushing or merging. | **Every stage**, as the read-back ("Now Promote 3: Booked ... into pre-staging (BestPractice)"). |
| **Says which path it took and why**, in one clause ("pushed directly -- a plan document"). | **Booked**, unchanged. |
| **Confirms on GitHub that the work arrived** before saying where it went. | **Every stage** -- a stage is not done until a fetch shows the branch carries the work. |
| **Hands off a step it cannot perform** as a Prompt Please block, the authorization travelling with it, after finishing everything it can. | **Every stage**, unchanged ([practices/prompt-please.md](../practices/prompt-please.md), [practices/relayed-authorization.md](../practices/relayed-authorization.md)). |
| **Reads intent, not the phrase**; says its reading and confirms when a message could honestly go either way; commits locally regardless. | **Every stage**, as the ladder's own reading rule (above). |
| **"Approved" means the same thing.** | **Booked**: "Go update", "Approved", "Booked", "Shared Save" and "Promote 3" are its names. |
| **"Finish whatever this needs"** when the work is not a branch move at all. | **Booked**, as its meaning when there is no branch to move -- so "Go update" keeps working for that too. |
| **One plain Boildown line** when a high-risk change landed on pre-staging, saying how far pre-staging is ahead of staging. | **Stays in** [practices/the-boildown.md](../practices/the-boildown.md), repointed to Booked. |
| **"Go merge" is retired**, kept only as history. | Stays history, in the old file's story. |

**What happens to the old file.** [practices/go-update.md](../practices/go-update.md)
is marked `deduplicated` into Booked -- the existing mechanism
([practices/current-rule-governs.md](../practices/current-rule-governs.md))
by which `precedent_show.py go-update` follows the old name to the live
rule, so every link to it keeps working. Nothing is deleted. The practices
that call Go update (Promote, Update Vendors, Prompt Please, Push directly
and the rest) are repointed to Booked in the same change
(practice: rename-updates-links); "Go update" keeps working as a phrase
throughout.

**For everyone else nothing changes.** Someone not using the ladder says
"Go update" and gets exactly today's behavior: their work lands on their own
landing branch (staging or main), with no readiness question and no stage
read-back. If they do use the stage words, Booked lands on that same branch.

### The archive guard

**A session whose work reached Act but not Booked cannot say "You can
archive this session".** Instead it says where the work is sitting and
recommends Booked -- or names the branch and says plainly that it is meant
to be dropped, the same way a container's unsaved checkouts are handled
today. This is the stronger form of the NOT YET LANDED line, which only
requires a mention. It is enforcement code, so it goes through the full
pull request chain when built.

### Finding work that already slipped

Two commands already look for stranded branches, and both run only when
asked:

- **Very deep check** lists every unmerged branch before its passes start
  and writes each one up with what it does, a link, when it last changed,
  and a recommendation: merge, take part, or close
  ([practices/very-deep-check.md](../practices/very-deep-check.md),
  results in [record/stale_branches.md](../record/stale_branches.md)). Its
  last recorded run was 2026-09-22, four days before the Graduate branch was
  made.
- **Chief of Staff** ends on Promotion Reviews, which read the week's stale
  branches and judge each keep or discard
  ([practices/chief-of-staff.md](../practices/chief-of-staff.md)).

The archive guard stops new cases. These two find old ones.

## Part 3 -- Retiring "team set"

**"Shared set" everywhere live; history left as it was written.**

- **Changed:** live documentation, practice text (Rule and Detail), code
  comments, and the messages tools print -- here and in the individual set
  and the three shared sets.
- **Left alone:** dated records -- `## Story` sections, closed items,
  decisions, gotchas. "Team" was the right word when they were written, and
  rewriting them makes history harder to follow.
- **The code alias stays.** Removing `LEVEL_ALIASES = {'team': 'shared'}`
  would break any older repository whose `precedent.json` still says
  `"level": "team"`.
- **Two live bugs, fixed first:**
  - [templates/document-project/precedent.json](../templates/document-project/precedent.json)
    still writes `"level": "team"` into every new repository, so it keeps
    making the problem.
  - [tools/precedent_gate.py](../tools/precedent_gate.py) prints "some rules
    below come from PRIVATE sources (team, individual)" on every turn. That
    is wrong twice: the old word, and all three shared sets declare
    `visibility: public` in their `precedent-source.json`.
- **A small check** flags "team set" in new text so it cannot creep back,
  skipping the dated records above.
- **Consumers** get the cleaned text the ordinary way, through Update
  Vendors.

## Analysis -- what was tried, and the holes found

**The name for the sets together.** The first aim was a word for the four
non-universal sets.

- *Add-on sets*: rejected by Morgan as ambiguous.
- *Private sets*: rejected by the session after checking -- all three shared
  sets declare `visibility: public`, so the word would be false.
- *Complete sets*: implies everything is included, when the biggest set, the
  universal one, was left out.
- *Custom sets*: the session's pick; not chosen.
- **Full set**, first defined as the four without the universal set. Hole:
  "full" reads as "everything". Answer (Morgan, 2026-09-28): make it mean
  everything, the universal set included, and let the four go without a
  word of their own.

**Vocabulary.** Adding nouns breaks Vocabulary's "commands only" design.
Answer: two clearly separate lists, the commands first. Hole: a second copy
of the definitions drifts. Answer: one registry, rendered into both places.

**Forcing the ladder on everyone.** Rejected by Morgan: Alex does not work
this way, and other repositories have no pre-staging. Answer: optional in
the universal set, required only through Morgan's individual set.

**Everyday words as triggers.** "Act", "Booked" and "Produce" all occur
in ordinary sentences. Answer: intent-reading, never keyword matching, plus
the read-back before anything moves. Step 5 gets the strictest reading.
Morgan, on "Act" in particular: since every request is read in context, a
common word is not a problem -- the session does not follow a word blindly.

**Step 5's word.** "Launch" was rejected as common in tech and too big.
"Picked up" was the first choice, but "picked up" is ordinary coding talk
("CI picked up the change"). **Production** came next: it continues the
theater metaphor, has the "go live" feel, and names exactly where the work
ends up. It became **Produce**, a verb like the other steps, with
"production" kept as the noun for where the work lands.

**Where Act lives.** First draft: the local clone. Hole: a cloud container is
reclaimed, and local-only work is lost. Answer: Act lives on the session's
feature branch on GitHub. Hole found in that: feature branches strand
work -- `claude/graduate-synonym` (BestPractice) is the live example, and a
warning had existed for six days. Answer: the archive guard, which blocks
the archive line instead of only asking for a mention.

**Bare Promote.** First reading: "err toward the bottom". Hole: taken
literally, a bare Promote after building could restart planning. Answer:
"the next step this work hasn't done", and between possible branch moves,
the lowest.

**Booking unready work.** Pre-staging gets only the basic checks, so
half-done work booked by mistake travels up. Answer: Booked's readiness
question.

**Planning overhead.** A required Consider on a one-character fix is
friction. Answer: the one-line plan.

**"Promote 1" for planning.** Nothing moves between branches at steps 1–2,
so "promote" is a stretch there. Morgan kept it on purpose: one word
everywhere beats accuracy at the bottom rung.

**Deprecating Go update.** It is universal, and other people rely on it,
and some 30 practice files call it. Answer: keep the phrase as one of
Booked's names, move the rule's text into Booked with the old file
deduplicated into it, and leave behavior unchanged for anyone not on the
ladder. Hole: Booked's readiness question breaks Go update's "never asks
again" promise. Answer: accepted, and only where the ladder is in force.

## What gets built, in order

Each numbered item is its own landing, through the ladder itself.

1. **Our language**: `tools/our_language.json`, the page rendered from it,
   and links from README and SETUP. *Ordinary change.*
2. **Vocabulary's second list**: [tools/precedent_vocabulary.py](../tools/precedent_vocabulary.py) reads the
   registry; the Vocabulary practice allows the second list; "Primary
   branch" moves. *Ordinary change.*
3. **The two "team" bugs**: the template and the gate message. The gate
   message is inside enforcement code, so *high-risk*.
4. **The "team" cleanup** across live text here and in the four sets, and
   the check that keeps it out. *The check is enforcement code: high-risk.*
   **The check is split out** (2026-09-29): the existing retired-words
   check (`process/retired_vocabulary.json`, practice
   migration-scrubs-vocabulary) exempts whole files only, and "team set"
   still lives, correctly, in the `## Story` sections of 16 practices and in
   about a hundred dated records. Exempting those files would switch the
   check off where it is needed, so it waits on a section-aware exemption
   -- its own change to the check code.
5. **The stages**: practice files for Consider (with "Plan it"), Act,
   Booked, Debut and Produce, each with its synonym; Promote's practice
   gains "Promote N", the read-back, the bare-Promote rule and "Graduate";
   Write it up gains "Spec it out"; the high-risk test moves into its own
   practice; Go update is deduplicated into Booked and its callers
   repointed. *Changes an authorization practice (Go
   update, Promote): high-risk.*
   **As built (2026-09-29), two departures, both smaller:** Booked lives in
   [practices/go-update.md](../practices/go-update.md) itself -- the file
   gains the names Booked, Shared Save and Promote 3 and the stage
   read-back -- rather than in a new file with go-update.md deduplicated
   into it. The behaviour is the same and none of the roughly 30 practices
   that link to it had to move. For the same reason the high-risk test
   stays in that file, where [Push directly](../practices/push-directly.md)
   already reads it. Booked's readiness question lives in Morgan's own
   individual set (step 6), since it applies only where the ladder is
   required.
6. **Morgan's individual practice** requiring the ladder, in
   `precedent-individual`.
7. **The archive guard** in the reply gate. *Enforcement code: high-risk.*
8. **Close `claude/graduate-synonym`** (BestPractice) once item 5 carries its
   two words, with the reason recorded -- the branch itself is never
   deleted by a session (practice: never-delete-a-remote-branch).
   **Done 2026-09-29:** item 5 carries both words, and the branch's
   approval quotes for them (Morgan, 2026-09-26) were folded into
   [practices/promote.md](../practices/promote.md) and
   [practices/write-it-up.md](../practices/write-it-up.md) with them.
   Nothing on the branch is left unlanded, so it is safe to delete:
   [that one row, with its trash icon](https://github.com/alex137/BestPractice/branches/all?query=claude%2Fgraduate-synonym).

**What reaches other repositories:** items 1–5 and 7 change files this
repository ships (practices, the vocabulary tool, the reply gate, a
template). They reach consumers through Update Vendors, not on their own
(practice: vendor-rollout-disclosed).

## Open questions

None right now. Everything raised during the brainstorm is settled in the
decision record below.

## Decision record

Strength per [practices/decision-strength.md](../practices/decision-strength.md):
`decided` is quoted, `assented` is a yes to the session's own proposal, and
`proposed` has had no answer yet.

| Decision | Strength | Morgan's words |
|---|---|---|
| "Shared set" is the word; "team set" retires | decided | *"I think we should say shared sets."* |
| "Full set" is the name | decided | *"for the Complete Set I like calling it "Full set" - it's like complete but it doesn't imply these are the only ones"* |
| "Full set" includes the universal set | decided | *"the "full set" I think should include the universal set"* |
| "Repo-local" is a word on the list | decided | *"we should also have "Repo-local" which refers to "your primary work repo that has bestpractice vendored in""* |
| Vocabulary becomes two lists, commands then our language | decided | *"the vocabulary should be two lists, the ... list of commands and then the list of useful words to know or our language"* |
| The words also live on a documentation page | decided | *"it should be on the documentation page ... and repeat it on the vocabulary list"* |
| "Primary branch" moves to the second list | decided | *"'primary branch' should be on the second list"* |
| Internal docs and comments move to the new words | decided | *"we can go through ... all of our internal docs and comments and fix it there"* |
| Dated records untouched; code alias kept | proposed | -- |
| Five stages, each "Promote N" | decided | *"if I say the short title or promote with a number, it does that step I named"* |
| Every stage read back with its full name | decided | *"every time you hear the ... [trigger] ... it repeats back the longer version"* |
| Consider chooses among plan sizes, "Plan it" in the middle | decided | *"you decide if it is a "brainstorm" ... or a "write it up" ... or maybe another option in the middle ... "plan it""* |
| One-line plan for tiny changes | decided | *"Very, very, very important."* |
| Optional for everyone, required only for Morgan | decided | *"people can use staging, but they don't have to"* |
| Step 5's theme is production | decided | *"For step #5 "PIcked up" maybe we say "Production"? That's used in the theater word as well"* |
| Step 5's word is the verb "Produce"; "production" stays the noun for where work lands | decided | *"the stage 5 word should be "Produce" to make it a verb like the previous ones"* |
| "Act" and other common words are fine, because requests are read in context | decided | *"since you review it in context, don't just blindly follow the use of the word, it's not a problem"* |
| Consider picks the plan size itself, from context, complexity and Morgan's guidance | decided | *"You should choose, based on the context, the complexity, and also, I will sometimes give you verbal guidance"* |
| The second name is a "Synonym" and triggers the stage too | decided | *"I think the "long title" should be called "Synonym""* |
| The session's short-lived branch is called a "feature branch" | decided | *"can we add in the word ... feature branch, to mean the short-lived ... branch just in that session"* |
| Act lives on the feature branch; Booked makes it safe | decided | *"booked is all about moving it from there to pre-staging so ... it won't get lost"* |
| Bare Promote: next step not done; lowest when unclear | decided | *"If I'm ambiguous, start at the ... lowest one"* |
| Booked checks readiness first | decided | *"you need to use your judgment and say, do you think it's ready?"* |
| Promote stays the one word, step 1 included | decided | *"I want one word to just use everywhere ... promote is good enough"* |
| Go update becomes part of Booked | decided | *"maybe we move the current "go update" practice to be a part of "booked" stage"* |
| Go update's high-risk call and its other duties are listed, each with where it goes | decided | *"Update the Go update section with these details and clarify where those details wil move to / what will happen to them"* |
| A "Plan it" plan is not saved, and is given as a paste-ready prompt for another session's feedback | decided | *"I agree, but it should be given in a prompt so that it is very easy to copy-paste that prompt to another session to get its feedback"* |
| The plan spells out what happens to Go update | decided | *"the plan also needs to have a paragraph or section on what happens with "go update""* |
| "Graduate" and "Spec it out" folded in | decided | *"yes fold that in"* |
| The archive guard | assented | *"Okay, I like these ideas"* |
