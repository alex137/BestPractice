<!-- Last updated: 2026-09-07 (Buenos Aires) by the session copying this document from WorkingWithAI into philosophy/; source: themorgan/WorkingWithAI content/RANDOM_NOTES.md, version 18. -->

# Random Notes — How to Work With AI

One entry per idea, prompt, workflow, or observation. Loosely grouped;
reorganize once a group gets big enough to need its own document (link it
from [MAP.md](https://github.com/themorgan/WorkingWithAI/blob/main/MAP.md) when that happens).

**How to use this file (proposed — see the meta-note at the bottom):** each
entry below is raw material dropped in from a session, lightly organized.
Treat it as a standing agenda, not a finished write-up — the point of doing
this in a repo instead of a doc is that any thread can pick up one entry,
argue it out with AI Assistant (per
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)),
and push the sharpened version back in.

## Frameworks

- **Rules for building a company around AI** — a full essay, promoted
  to its own document because it's one sustained argument rather than a
  loose list: [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md). Covers context as the
  scarce capital asset, transcription discipline (the "Ghost"), owning
  every word you pass on, treating the AI Chat as the intermediary for
  the work itself, co-creating instead of delegating, building
  workflows and the rules that fall out of them only once work actually
  repeats, hiring for drive, relationships, and taste over production,
  giving agents a human manager over the loop, killing "dark
  processes," and voice/style as evidence that someone actually thought.
- **Building AI systems for co-creation** — one level down from the above:
  how the AI systems themselves should be configured, built, and run so
  the healthy pattern is the default rather than something a disciplined
  user has to manufacture by hand:
  [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md). Covers durable memory as
  the default substrate, push-back as a config switch keyed to task shape,
  arguing in the open instead of posting finished-looking suggestions,
  visibly non-uniform confidence, situational (not fixed) cost-awareness,
  a structural check for AI-sounding prose, and self-surfacing of dark
  processes.
- **Where an idea from either essay actually goes next** —
  [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md), added 2026-08-27. Neither essay
  above is itself a set of rules anyone follows day to day; this is the
  document that turns an argument into a checklist actually in force, and
  tracks which of those checklist items have proven themselves enough to
  become real company-wide policy in [RepoPersonalPreferences](https://github.com/themorgan/RepoPersonalPreferences).
  See [README.md](README.md)'s pipeline explanation and this file's own
  meta section below for why that middle step exists at all.

## Why BestPractice Specifically Works (Semi-Organized Brainstorm)

*The premise: BestPractice — the practice layer this repo vendors under
`process/upstream/` — is being used here as a live case study of
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)
and
[`transcribe-everything`](COMPANY_BUILDING_RULES.md#transcribe-everything):
forced co-creation, forced transcription. The observations below are
about* why *it works, not just that it does.*

1. It's a structure for working with AI as a partner-in-thought, rather
   than the two usual extremes for non-dev work: blindly handing it
   everything, or using it lightly for research/writing and nothing more.
2. It forces "think in process" / "think in the how" — a way of working
   that's enormously powerful and very hard for most non-technical
   ("normie") employees to adopt voluntarily. This structure gives them no
   other option. (This is the "Nix approach" — see the open question
   below.)
3. Key information, learnings, and intentions are normally trapped inside
   private AI chat conversations. This surfaces them granularly and
   effectively, while still keeping the conversations themselves private.
   - **3a.** Corollary of #2 + #3 together: it doesn't just put learnings
     into the shared GitHub repo — it purposefully extracts *the rules*
     (this repo's own [AGENTS.md](https://github.com/themorgan/WorkingWithAI/blob/main/AGENTS.md)/`process/` layer is itself an
     instance of that), which amounts to automatic documentation generated as a
     side effect of doing the work.
   - **3b.** Consequence of 3a: it also extracts the TODOs, which
     otherwise get lost constantly unless someone is unusually organized.
     (Compare [TODO.md](https://github.com/themorgan/WorkingWithAI/blob/main/TODO.md)'s push-time gate in this repo — that's
     this exact mechanism, installed.)
4. Multiple people can work the same issue simultaneously — version
   control plus AI-assisted merging beats one-person-at-a-time editing.
5. It works especially well in multilingual contexts: people write and
   think in whatever language comes naturally, and the AI carries the
   translation into the repo's shared working language — nobody has to
   compose in a second language to participate.

### 2026-09-01 Entry — "A Way of Working," Not "a Pattern" or "a Repo," and Whether Decentralization Alone Is Enough

A run of Morgan's own comments from one session, kept verbatim and in
sequence rather than smoothed into a single paragraph — per this file's own
append-only, disagree-with-your-past-self convention above. Not yet argued
out or slotted into a formal document; flagged at the end for where it
might connect.

> I agree, and I thought that a few hours ago. I think what makes this
> harness unique is: [1] the focus on collaboration not merely production
> PLUS [2] the focus on protocol-generation PLUS [3] the approach of making
> AI/Chat the intermediary layer to ALL work [don't touch anything directly]
> including the situation that led to every little decision even tiny
> ones <---- THOSE THREE taken together are EXPLOSIVE in an AMAZING way

*In the quotes below, BestPractice (BP) is this project, now Precedent,
and WordPress (WP) is the blogging platform.*

> I don't think it's "BP is a pattern" nor is it "BP is a repo"; I would
> frame it more as.... we need to tweak this, but more like: "BP is a way
> of working" -> the three patterns in my penultimate message, taken
> together make work LOOK and FEEL very different - especially (I will
> predict) collaborative type work.

> I do love the idea of people forking it, doing their own BPs, suggesting
> them -- I love it. ANd that's part of it. The Practices arise organically.
> I just think that in the contexts and ways I want to use this now (beyond
> "just helping myself") it needs to be a bit more organized than "a few
> repos with similar but different things and people adding practices to
> their own repos" - see my earlier comment about how *I* don't feel
> comfortable suggesting practices to you, and most people don't even think
> in practices - for teams, you have *ONE PERSON* who kinda enforces it, and
> this is the tool taht that person needs and wants for this.

> Absolute decentralization was fun 20 years ago and also for the open
> source wild west; also, if (*if*) we really want to use this across
> different teams and projects and potentially even get other people using
> it etc, I think we need a bit more structure to this process of
> integrating and approving and sharing processes.

> Maybe a bit like WP: yeah, it is open source so anyone can do their own
> version -- but WP only really took off (20 years ago) after they added
> the "Plugins" making it trivial for anyone to build their own plugins --
> so people didn't just modify WP for themselves, rather, they did in a way
> so that it was very easy to contribute back to everyone else, for
> everyone else to use their plugins.

> Every harness I've read about or experimented with or saw youtubes about
> [granted, not that many, I'm only ramping up obsessing over this now]
> seems to focus on things like "making dev easier or better such as
> forcing planning stages" or "connecting to external services and tools"
> or "making sure tokens are used efficiently" etc etc. These three points
> I mentioned above are truly unique and are *WHAT IS MOST VALUABLE TO ME*
> (and I think MANY others in the "management" or "business" world as
> opposed to merely "devs" or "vibe coders"): doing sh\*t with other people
> in a smart way AND creating/enforcing rules/protocols/practices in a smart
> way AND forcing chat as an intermediary layer for EVERYTHING everything
> [don't edit any file directly yourself] ---> those three are new and
> explosive.

**Update, same day:** the three-part uniqueness thesis is now promoted —
see [CORE_PILLARS.md](CORE_PILLARS.md), a
one-page pitch naming the same three ideas (linked from
[OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md),
[COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md), and
[REASONS_WHY.md](REASONS_WHY.md)). One correction from the chat discussion
that led there: "chat as the sole intermediary" means chat is how a
*person* touches any document or artifact — talk to AI Assistant and have
AI Assistant edit it, instead of opening a doc and editing it yourself — not a claim
that chat is literally the only medium anything happens in (PR review
comments still carry part of the argument, per the merge runbook above). A
second correction, same day: the first bullet wasn't
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)
restated — that's one person co-creating with the model. The actual claim
is that this whole approach targets *groups* of people collaborating with
each other, not individual AI assistance, which most other "work better
with AI" advice already covers; that got its own new point,
[`groups-not-individuals`](OUR_PHILOSOPHY.md#groups-not-individuals), and
the formula's first bullet now points there instead.

The decentralization-vs-structure tension — forking and organic practices
staying good, but wanting one enforcer and a lower-friction way to
contribute a practice back (the WordPress Plugins comparison) — still
doesn't have a home: it's a genuine complication for
[`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)'s
"practices arise organically" framing, only partly answered by this repo's
own three-stage pipeline ([RULES_NOW_TESTING.md](RULES_NOW_TESTING.md)),
which gives "one person enforcing" but not yet a trivially-easy way for
someone else to contribute a practice back.

### Open Question: Forcing Deeper Engagement, Not Just Permitting It

For points 2 and 3: "normie" employees might default to the shallow use —
simple prompting — and never discover the deeper mode, unless something
pushes them there. Candidate mechanisms, none decided yet (this is a
**decision**-class item, see [TODO.md](https://github.com/themorgan/WorkingWithAI/blob/main/TODO.md)):

- Have AI Assistant push back harder than its default on direct instructions —
  question them instead of just complying.
- Constant, visible reminders of the deeper mode, rather than a one-time
  onboarding note.
- Make the automatic rule-extraction (3a) more "in your face" — if people
  *see* the rules being generated live, the "wow" reaction itself teaches
  them the system has more to offer than a simple prompt box.
- Have AI Assistant proactively surface a previously-extracted rule when it's
  relevant in a new context, rather than leaving it inert in a file
  nobody re-reads.

Push-back mode (the first candidate above) is decided and promoted — see
[`push-back-writing-thinking`](RULES_NOW_TESTING.md#push-back-writing-thinking).
The rest — visible
reminders, in-your-face rule-extraction, proactive resurfacing — remain
open; proactive resurfacing specifically also shows up as one of
[AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md)'s "Memory & context" ideas,
tracked as a not-yet-ready item in
[RULES_NOW_TESTING.md](RULES_NOW_TESTING.md) pending real infrastructure.

## Observations From Other Conversations

**Visibility as an incentive mechanism.** When contributions live in
version control, you can ask the AI to help you evaluate whether a given
person's contribution is good — and because the contributor knows that's
coming, they can (and will) ask the AI to help them tune their work toward
what you'll value. This only works cleanly if you've set explicit goals and
rules of the road in advance for them to tune toward. Performance on this
front becomes visible in the history, for that person and for everyone else
on the team simultaneously — a much stronger and more continuous signal
than a periodic review.

**Rethinking an ad campaign AI-first — a conversation with AI Assistant.** Prompted
by thinking through what it would mean to run an ad campaign in a truly
AI-first way. The framing generalizes well past ads:

> That changes my advice, and I'll retract part of the caution — but keep
> one piece of it.
>
> The part I'll keep: the campaign being real is exactly what makes this a
> good learning vehicle. Real money, real API failures, real dirty data,
> real consequences for being wrong. A todo app teaches you nothing about
> verification because nothing breaks. So don't let the campaign degrade —
> not because the campaign is the only goal, but because a live campaign is
> the thing generating the feedback you're trying to learn from.
>
> **What "partner, not lookup tool" actually cashes out to.** Mostly three
> things, and none of them are prompting tricks.
>
> *Context is the whole game.* The reason chat feels like a lookup tool is
> that I arrive at every conversation with nothing. I can't disagree with
> you usefully because I don't know enough to have a view. Working in a
> repo changes this: the repo *is* the shared context. So the
> highest-leverage thing you can do is write things down in files I'll read
> — a `CONTEXT.md` describing the business and the campaign, a
> `DECISIONS.md` with one line per architectural choice and why. Investing
> in context isn't housekeeping; it's what buys you a collaborator who can
> push back instead of one who can only comply. Related: explicitly invite
> disagreement. "Here's my plan, build it" gets you compliance. "Here's my
> plan, what's wrong with it" gets you something better.
>
> *Specification, not instruction.* The mode shift is from "write a
> function that does X" to "here are the constraints, here's how we'll
> know it's correct." Writing good specs is a real skill and it transfers
> — you'll write better issues and better docs as a side effect.
>
> *Verification is the bottleneck.* Generating code is nearly free now;
> knowing whether it's right is the constraint, and it's *your* constraint.
> Build the checking apparatus early: recorded fixtures so you can test
> without hitting live APIs, a dry-run mode, an assertion that running
> apply twice produces no second diff. Then hold one rule absolutely —
> never merge code you can't explain.
>
> **Habits worth adopting deliberately:** keep a failure log (when
> generated output is wrong, write down whether it was missing context, a
> bad spec, or genuine model error — after twenty entries you'll have a
> calibrated sense of where the leverage actually is); build one module
> twice, once mostly by hand and once with heavy AI involvement, and
> compare; keep commits small and reviewable, because long AI-generated
> diffs are where review discipline dies.

**Morgan's synthesis on the above:** this is implicitly what BestPractice is
already suggesting, just framed more sharply. Running an ad campaign — or
most operational work — normally means constantly tweaking options,
constantly pushing buttons, and never recording why any button got pushed.
The BestPractice approach forces recording every small decision and its
reason, and it does this *automatically*, purely as a side effect of the
system's shape: the only interface is prompting AI Assistant, and AI Assistant tracks
everything via the repo. Same mechanism as 3a/3b above. The other point
worth keeping from that conversation: having the AI push back harder,
explicitly, rather than defaulting to compliance — connects directly to the
open question above.

**Rejecting a request costs less when it comes from AI than from a
person.** Morgan's observation, not yet tied to a specific practice: saying
no to an AI assistant's proposal — a suggested plan, a permission ask, a
piece of pushed-back-on advice — carries less social weight than saying no
to the same request from a person. No relationship to manage, no face on
the other side to consider. Worth tracking as a real effect on its own,
before deciding what (if anything) it should change about how this repo
works. Not yet slotted into the formal docs; see this chat's reply for
where it might connect once it's been argued out.

## Meta: Using This Repo as "Google Docs on Steroids" for Brainstorming

Proposal, not yet decided (flag any of this you don't want — this is your
call as much as mine):

- **One entry per session, appended, not rewritten.** Keep the append-only
  discipline this repo already uses for [TODO.md](https://github.com/themorgan/WorkingWithAI/blob/main/TODO.md); resist the urge
  to silently smooth over an earlier, rougher version of an idea — better to
  add a dated follow-up entry that supersedes it, so the disagreement with
  your past self stays visible instead of vanishing.
- **Turn open questions into TODO.md decision items as soon as they're
  identifiable**, the way the "forcing deeper engagement" question above
  just did — that's the mechanism in 3a/3b, applied to this repo's own
  practice of self-reflection, not just to code.
- **Use PR review comments as the argument, not just the record.**
  [`co-create-dont-delegate`](COMPANY_BUILDING_RULES.md#co-create-dont-delegate)
  suggests the highest-value use of this repo isn't "paste a finished
  thought" but "open a PR with a half-formed one and have the
  back-and-forth happen as review comments" — the transcript of the
  disagreement becomes part of the corpus
  ([`capital-asset`](COMPANY_BUILDING_RULES.md#capital-asset)), not just
  the conclusion.
- **When a topic outgrows a bullet, promote it**, exactly as
  [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) just was. A dedicated file gets its
  own version history, so you can watch one idea sharpen over many sessions
  instead of only ever seeing its latest state.
- **Periodically ask AI Assistant to look for contradictions across entries.**
  Loosely-grouped brainstorm entries accumulated over many sessions will
  eventually disagree with each other (e.g.,
  [`build-five-kill-four`](COMPANY_BUILDING_RULES.md#build-five-kill-four)'s
  "kill four of five built" against
  [`think-in-workflows`](COMPANY_BUILDING_RULES.md#think-in-workflows)'s
  "don't systematize a one-off") — that tension is often more interesting
  than either entry alone, and it's the kind of thing a single session
  won't notice but a deliberate re-read will.

**2026-08-29 entry — a dropped rule, worth reconsidering later.**
[COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) used to carry a
rule, "own the spec and the eval before you own the output" — whoever
writes the acceptance criteria sets the direction, and if you can't say
how you'd know the result is right, you don't have a project. Morgan
flagged that it sits in tension with
[`build-five-kill-four`](COMPANY_BUILDING_RULES.md#build-five-kill-four):
one says commit to a definition of "good" before you build, the other
says building fast and killing four of five is often the better move
when an option costs nearly nothing. Removed rather than resolved — the
call was that owning the spec is real but doesn't earn a standalone rule
next to one that can read as its opposite. Worth a real pass later: is
this actually a contradiction, or two rules for two different situations
(cheap-to-build options vs. a project with real acceptance criteria) that
just needed sharper scoping instead of a cut?

**2026-08-27 entry — the pipeline needed a name and a middle stage.** A
session asked to recommend RepoPersonalPreferences changes based on this
repo's ideas went straight from brainstorm to "add this to the personal
pack." Morgan's correction: this repo's actual job is to *try* an idea in
real work first — going straight from an essay here to a rule that rolls
out to every project skips the step that's supposed to catch a good-sounding
idea that doesn't actually hold up. The fix wasn't a new rule, it was
naming the stage that was missing: [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md),
sitting between the essays here and RepoPersonalPreferences, holding
whatever's currently on trial. See [README.md](README.md)'s new pipeline
section and [TODO.md](https://github.com/themorgan/WorkingWithAI/blob/main/TODO.md) for the decision record.

## Ideas Set Aside, Not Carried Forward

*Surfaced while drafting [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md),
moved here instead of staying in that essay.*

- A mandatory eval-file gate before any output ships — unclear how it
  generalizes past code, where "eval" has an obvious technical meaning.
- Having the AI itself pick which raw, unfiltered sample a human reviews
  for [`human-only-zones`](COMPANY_BUILDING_RULES.md#human-only-zones) —
  the idea didn't land clearly enough in discussion to write down yet;
  worth re-raising once it's sharper, rather than forcing it in now.

## Prompts and Phrasing

- [ ] *(seed this with real prompts as they come up)*

## Workflows

- [ ] *(seed this with real workflows as they come up)*

## Things That Went Wrong, and Why

- [ ] *(seed this with real incidents as they come up)*

## See Also

- [OUR_PHILOSOPHY.md](OUR_PHILOSOPHY.md) — the underlying theoretical
  ideas everything else here assumes, named and explained on their own
  terms.
- [REASONS_WHY.md](REASONS_WHY.md) — the less obvious benefits those
  ideas actually produce in practice.
- [HUMANS_AT_OUR_BEST.md](HUMANS_AT_OUR_BEST.md) — the one list of what
  humans are good at, gathered from the shorter versions scattered here
  and elsewhere.
- [COMPANY_BUILDING_RULES.md](COMPANY_BUILDING_RULES.md) — standalone
  essay promoted out of the brainstorm: rules for building a company
  around AI.
- [AI_GOVERNANCE_TO_COCREATE.md](AI_GOVERNANCE_TO_COCREATE.md) —
  standalone essay promoted out of the brainstorm: how AI systems
  themselves should be configured, built, and run.
- [RULES_NOW_TESTING.md](RULES_NOW_TESTING.md) — pipeline stage 2: the
  practical rules actually being tried in real work right now.
- [CORE_PILLARS.md](CORE_PILLARS.md) — one-page
  pitch: the core ideas this repo argues are unique specifically taken
  together.
