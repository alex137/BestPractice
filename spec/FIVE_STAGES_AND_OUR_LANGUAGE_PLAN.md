---
title:         Five stages and our language -- one ladder for work, one page of words
kind:          proposal
status:        accepted
opened:        2026-09-27
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       "Two linked changes. First, a short page of the words this project uses (practice, universal set, individual set, shared set, full set, primary branch, and the stage names), printed as a second list under Vocabulary, plus a cleanup that retires 'team set' for 'shared set' everywhere live. Second, the work ladder: five stages, Consider, Act, Booked, Debut, Picked up (step 5's word still open), each reachable as 'Promote N' or by its word, each read back aloud before it runs. Optional for everyone; required for Morgan through his individual set. Go update becomes step 3's other name."
---

# Five stages and our language -- one ladder for work, one page of words

Morgan approved the direction on 2026-09-27 and asked for this write-up in
the same message ("Go update"). Nothing here is built yet. A few choices are
still open and listed at the end; the build order is in
[What gets built, in order](#what-gets-built-in-order).

This plan came out of one brainstorm session. It is written for a reader who
was not there.

## Contents

- [The problem](#the-problem)
- [Part 1 -- Our language](#part-1----our-language)
- [Part 2 -- The five stages](#part-2----the-five-stages)
- [Part 3 -- Retiring "team set"](#part-3----retiring-team-set)
- [Step 5's word -- the brainstorm](#step-5s-word----the-brainstorm)
- [Analysis -- what was tried, and the holes found](#analysis----what-was-tried-and-the-holes-found)
- [What gets built, in order](#what-gets-built-in-order)
- [Open questions](#open-questions)
- [Decision record](#decision-record)

## The problem

**Three problems, found in one conversation.**

1. **There was no word for the four repositories Morgan edits as a group.**
   Every repository he works in follows the universal set (this repository's
   own catalogue), his own individual set (`precedent-individual`), and any
   shared sets it declares (today `precedent-shared-repo-maintenance`,
   `precedent-shared-writing` and `precedent-shared-working-style`). He
   called the four non-universal ones "the four precedent-star files".
   Meanwhile the older word **"team set"** still appears about 390 times
   across roughly 140 markdown files here, although the code switched the
   level name to `shared` on 2026-09-18
   ([tools/precedent_resolve.py](../tools/precedent_resolve.py) keeps
   `LEVEL_ALIASES = {'team': 'shared'}` so older repos still load). Two
   words for one thing, and nothing that names the group.

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
| **full set** | Your individual set plus your shared sets -- the ones you edit together. **It does not include the universal set.** |
| **in force** | A practice that actually applies here, right now. |
| **source** | Where a set of practices comes from, usually a repository. |
| **level** | Whether a source is universal, shared, individual, or local to one repository. |
| **primary branch** | The one shared branch regular work lands on. |
| **feature branch** | The short-lived branch one session works on, on GitHub -- the kind named like `claude/<topic>-<random>`. GitHub's own word for it; some teams say "topic branch". It survives a lost container but is easy to forget, and it is deleted once merged. |
| **pre-staging, staging, main** | The three branch tiers ([spec/BRANCH_TIERS_PLAN.md](BRANCH_TIERS_PLAN.md)). In the stage names below, `main` is called **production**. |
| **the five stages** | Consider, Act, Booked, Debut, Picked up -- see Part 2. |

**"Full set" is the word Morgan chose** (*"it's like complete but it doesn't
imply these are the only ones"*). "Full" can still sound like "everything",
so the definition says outright that the universal set is not part of it.
See [Open questions](#open-questions): the reading that "full set" means the
four non-universal sets, not everything in force, is the session's and
still wants his yes.

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

| # | Word | Long title | What happens | Where the work ends up |
|---|---|---|---|---|
| 1 | **Consider** | Plan | Decide how much planning this needs, then do that much. | Nowhere yet, or a plan |
| 2 | **Act** | Build | Make the change. | The session's feature branch on GitHub |
| 3 | **Booked** | Shared Save | Move it from the feature branch to pre-staging. After this it **won't be lost**. | pre-staging |
| 4 | **Debut** | Test Readiness | Move pre-staging into staging, with the full checks. | staging |
| 5 | **Picked up** *(word still open)* | Production | Move staging into main, with the full checks plus the GitHub test. | main |

**Each stage is also "Promote N".** "Promote 3" and "Booked" mean the same
thing. Morgan kept one word for the whole ladder on purpose: *"I want one
word to just use everywhere ... promote is good enough"* -- step 1 is
promoting an idea into something worth preparing, even though nothing moves
between branches until step 3.

**"Graduate" is another word for Promote**, and **"Spec it out" another word
for Write it up** -- the two words stranded on `claude/graduate-synonym`
(BestPractice), folded in here rather than merged on their own.

### Every stage is read back before it runs

Every time a stage is triggered -- by its word, by "Promote N", or by a
plain request that means the same -- the session says the full version out
loud first, naming the repository and the branches:

> Now Promote 3: Booked, the Shared Save -- moving
> `claude/precedent-terminology-vs3o6q` into pre-staging (BestPractice).

When one request covers several stages, the read-back names all of them:
*"Now Promote 3 then 4: Booked, the Shared Save, into pre-staging, then
Debut, Test Readiness, into staging (BestPractice)."* The existing
[Promote](../practices/promote.md) already opens with *"Now promoting from
pre-staging to staging"*; this extends that to every stage and adds the
stage's name.

### Reading the request -- intent, never a keyword match

**No stage fires on a text search for its word.** Morgan, on step 5: the
session *"should not just do a simple grep for that exact word ... I might
use it in a slightly different grammatical way or ... I may not use that
exact word ... you have to apply your intelligence."* That is how every
command here is already read ([practices/go-update.md](../practices/go-update.md)),
and it matters most at step 5, which changes production. Where a message
could honestly go either way, the session says its reading and confirms
before any shared-branch step.

**The same step can be asked for many ways**, and all of them mean it:
"Debut", "Promote 4", "promote pre-staging to staging", "move BestPractice
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

### Consider: four sizes of plan

Consider chooses how much planning the work deserves, from four sizes, and
names its choice in the read-back:

| Size | What it produces | When |
|---|---|---|
| **One-line plan** | One sentence in the reply: what will change and where. Then straight to Act. | Tiny changes -- a typo, a link, a one-line fix. |
| **Brainstorm** | Discussion only. Nothing is written or committed ([practices/brainstorm-holds-commits.md](../practices/brainstorm-holds-commits.md)). | The idea itself is still open. |
| **Plan it** *(new)* | A written plan in the session: numbered steps, the risks, what "done" looks like, and what is out of scope. No file. | Real work, clear enough to build in this session. |
| **Write it up** / **Spec it out** | A full committed report, as [practices/write-it-up.md](../practices/write-it-up.md) says -- like this file. | Big or cross-session work, or anything someone else will pick up. |

**The one-line plan matters most.** Morgan: *"Very, very, very important. We
don't want to have lots of documents ... when it's not needed."* Forcing a
planning step on a typo is friction; the one-line plan is how Consider stays
cheap.

"Plan it" is new and gets its own practice file and command.

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

### Go update becomes Booked's other name

`Go update` stays in the universal set, working exactly as it does for
everyone else. **For work on the ladder it is step 3**: it already lands
Morgan's work on pre-staging, because his landing branch is pre-staging
([spec/BRANCH_TIERS_PLAN.md](BRANCH_TIERS_PLAN.md)). What moves:

- Go update's rules for **which branch** work lands on move into Booked's
  practice, so they are written once.
- Its **classification** -- direct push by default, the full pull request
  chain only for high-risk changes -- stays, and Booked uses it.
- Nothing is deleted outright: whatever text is superseded is marked that
  way, in place (practice: current-rule-governs).

`Push directly` is unchanged: it still overrides the classification for one
change.

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
  comments, and the messages tools print -- here and in the four sets of the
  full set.
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

## Step 5's word -- the brainstorm

Morgan's set reads like a show's life: considered, acted, booked, debuts,
picked up. He prefers **"Picked up"** over **"Launch"** because launch is
common in tech and usually means something much bigger. He is not set on it
and asked for other ideas.

**What the word needs:** rare in everyday talk about code, so it is not
triggered by accident; reads as an instruction; fits the show; not grander
than "merge staging into main". Measured by counting whole-word uses across
this repository and the four sets' markdown on 2026-09-27:

| Candidate | Uses found | For | Against |
|---|---|---|---|
| **Picked up** | 7 ("pick up": 8 more) | His choice; in television, the network commits to the show. | Common in everyday coding talk ("CI picked up the change", "picks up where it left off"). |
| **Aired** | 0 | The show is on air: in production. Past tense, like Booked. Almost never said about code. | Slightly odd as a command ("air it"). |
| **On air** | 0 | Plain and vivid. | Two words; reads as a state more than an order. |
| **Premiere** | 0 | Rare in tech. | Means the same as Debut, step 4. |
| **Launch** | 24 | Everyone understands it. | Rejected by Morgan: too common, and too big. |
| **Ship** | 120 | Short. | Very common here already. |
| **Green-lit** | -- | Television word. | Wrong order: green-lighting happens before production starts. |
| **Syndicated** | -- | Television word. | Far too big a claim for one merge. |

**Recommendation: "Aired".** It fits the show, fits "production", and has no
everyday meaning in coding talk to collide with. The read-back and
intent-reading make any word workable, but step 5 changes production, so it
should have the fewest accidental matches. If Morgan keeps "Picked up", it
works: the read-back catches a misfire before anything moves. Either way,
**one word only** -- two words for the step that touches production is two
chances to misfire.

## Analysis -- what was tried, and the holes found

**The name for the four sets.**

- *Add-on sets*: rejected by Morgan as ambiguous.
- *Private sets*: rejected by the session after checking -- all three shared
  sets declare `visibility: public`, so the word would be false.
- *Complete sets*: implies everything is included, when the biggest set, the
  universal one, is left out.
- *Custom sets*: the session's pick; not chosen.
- **Full set** (chosen). Hole: "full" still leans towards "everything".
  Answer: the definition says outright that it excludes the universal set.

**Vocabulary.** Adding nouns breaks Vocabulary's "commands only" design.
Answer: two clearly separate lists, the commands first. Hole: a second copy
of the definitions drifts. Answer: one registry, rendered into both places.

**Forcing the ladder on everyone.** Rejected by Morgan: Alex does not work
this way, and other repositories have no pre-staging. Answer: optional in
the universal set, required only through Morgan's individual set.

**Everyday words as triggers.** "Act", "Booked" and "Picked up" all occur in
ordinary sentences. Answer: intent-reading, never keyword matching, plus the
read-back before anything moves. Step 5 gets the strictest reading, and a
rarer word is recommended.

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

**Deprecating Go update.** It is universal, and other people rely on it.
Answer: keep it as Booked's other name and move only its branch rules into
Booked.

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
5. **The stages**: practice files for Consider (with "Plan it"), Act,
   Booked, Debut and step 5; Promote's practice gains "Promote N", the
   read-back, the bare-Promote rule and "Graduate"; Write it up gains
   "Spec it out"; Go update's branch rules move into Booked. *Changes an
   authorization practice (Go update, Promote): high-risk.*
6. **Morgan's individual practice** requiring the ladder, in
   `precedent-individual`.
7. **The archive guard** in the reply gate. *Enforcement code: high-risk.*
8. **Close `claude/graduate-synonym`** (BestPractice) once item 5 carries its
   two words, with the reason recorded -- the branch itself is never
   deleted by a session (practice: never-delete-a-remote-branch).

**What reaches other repositories:** items 1–5 and 7 change files this
repository ships (practices, the vocabulary tool, the reply gate, a
template). They reach consumers through Update Vendors, not on their own
(practice: vendor-rollout-disclosed).

## Open questions

1. **Step 5's word.** Recommendation: "Aired". Morgan's current word:
   "Picked up".
2. **"Full set" means the four non-universal sets** -- confirm, or say it
   should mean everything in force.
3. **Does Consider choose the plan size itself, or suggest and wait?**
   Recommendation: choose it and say so in the read-back; one word from
   Morgan overrules. Asking every time adds a round trip, and the read-back
   already makes the choice visible.
4. **Does a "Plan it" plan get saved?** Recommendation: no -- it lives in
   the session. Work that spans sessions is Write it up's job.
5. **"Act" as step 2's word.** Not questioned so far; noted because it is
   the commonest word on the ladder.

## Decision record

Strength per [practices/decision-strength.md](../practices/decision-strength.md):
`decided` is quoted, `assented` is a yes to the session's own proposal, and
`proposed` has had no answer yet.

| Decision | Strength | Morgan's words |
|---|---|---|
| "Shared set" is the word; "team set" retires | decided | *"I think we should say shared sets."* |
| The group of four is the "full set" | decided (definition to confirm) | *"for the Complete Set I like calling it "Full set" - it's like complete but it doesn't imply these are the only ones"* |
| Vocabulary becomes two lists, commands then our language | decided | *"the vocabulary should be two lists, the ... list of commands and then the list of useful words to know or our language"* |
| The words also live on a documentation page | decided | *"it should be on the documentation page ... and repeat it on the vocabulary list"* |
| "Primary branch" moves to the second list | decided | *"'primary branch' should be on the second list"* |
| Internal docs and comments move to the new words | decided | *"we can go through ... all of our internal docs and comments and fix it there"* |
| Dated records untouched; code alias kept | proposed | -- |
| Five stages, each "Promote N" | decided | *"if I say the short title or promote with a number, it does that step I named"* |
| Every stage read back with its long title | decided | *"every time you hear the ... [trigger] ... it repeats back the longer version"* |
| Consider chooses among plan sizes, "Plan it" in the middle | decided | *"you decide if it is a "brainstorm" ... or a "write it up" ... or maybe another option in the middle ... "plan it""* |
| One-line plan for tiny changes | decided | *"Very, very, very important."* |
| Optional for everyone, required only for Morgan | decided | *"people can use staging, but they don't have to"* |
| Step 5's long title is Production | decided | *"let's do that"* (on "production for the last stage") |
| The session's short-lived branch is called a "feature branch" | decided | *"can we add in the word ... feature branch, to mean the short-lived ... branch just in that session"* |
| Act lives on the feature branch; Booked makes it safe | decided | *"booked is all about moving it from there to pre-staging so ... it won't get lost"* |
| Bare Promote: next step not done; lowest when unclear | decided | *"If I'm ambiguous, start at the ... lowest one"* |
| Booked checks readiness first | decided | *"you need to use your judgment and say, do you think it's ready?"* |
| Promote stays the one word, step 1 included | decided | *"I want one word to just use everywhere ... promote is good enough"* |
| Go update becomes part of Booked | decided | *"maybe we move the current "go update" practice to be a part of "booked" stage"* |
| "Graduate" and "Spec it out" folded in | decided | *"yes fold that in"* |
| The archive guard | assented | *"Okay, I like these ideas"* |
| Step 5's word | open | *"I'm not insistent on that"* |
