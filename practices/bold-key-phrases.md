---
slug:        bold-key-phrases
title:       Bold the key phrases by default -- people skim
tier:        resident
severity:    default
applies_to:  ["**/*.md"]
occasion:    "writing any document meant to be read"
gates:       []
index_clause: "bold the key phrases by default, without being asked"
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       2026-08-31
approved_by: "Morgan F, migrated from RepoPersonalPreferences by the private-set migration session PROMOTED to the universal catalogue 2026-09-07, Morgan F, from
  precedent-team-maintainers. Both team sets had landed this same practice, byte
  for byte, within a day of each other -- and two sources at the same level
  defining one slug is a hard `ResolveError`, so any repo declaring both team
  sources could not resolve at all. Two different teams wanting the identical
  rule is what a universal rule looks like (practice: layered-practice-packs);
  the team sets were simply where it was written down first. Deleted from both
  on promotion rather than left as copies. A repo this does not bind exempts it
  in `not_binding` with a stated reason, which is the mechanism that makes one
  copy safe"
---
## Rule
People don't read; they skim, and bolding makes skimming easy. Bold the key phrases in a document by default, without being asked, scaling with length -- a long paragraph or document is where a skimmer most needs a spine to follow, a short note usually needs little or none.

## Detail
Don't overdo it -- emphasis is a budget, not a decoration; when a lot is bold, nothing is. Two rough tests: someone reading only the bolded phrases should come away with the document's actual argument, and the bolded share of a page should still read as highlighting rather than as the page's normal typeface. A suggestion, not a gate: judge that density against running prose, and let a page whose own structure already carries the emphasis -- headings, short bolded items -- leave its section lead-ins plain. The default is off on an explicit instruction, a recipe saying otherwise, or a register that doesn't take it -- a contract, a filing, an academic or otherwise conventional document -- and out of scope entirely for code, configuration, and other work meant to run.

## Why
This is the mechanism proportional emphasis governs the amount of: that rule says how much weight a point should carry relative to its importance, this one says bolding is the default way to give a point weight.

## Story
Migrated here from RepoPersonalPreferences by the phase-3 private-set
migration. That pack recorded no originating incident for this rule; it is a
stated preference with its reasoning attached, and this Story says so rather
than inventing a failure it never had.

The reasoning is an observation about how the documents this rule governs
are actually consumed: people do not read them, they skim them, and bolding
is what makes a skim land on the argument instead of on whatever the eye
happened to catch. The payoff scales with length, which is why the rule is
about defaulting to bold rather than about a quota.

The counterweight is the part worth keeping: emphasis is a budget. When a
lot of a page is bold, nothing on it is -- the bolding stops being a signal
and becomes texture, and the reader is back to reading everything or
nothing. The two tests in the Rule are both judgment calls by design, since
any threshold precise enough to check mechanically would be wrong for some
register.

The heading-dense clause in the Detail arrived on 2026-09-07, from a page
the rule had been applied to correctly and then outgrown. A pre-launch audit
sweep ([`spec/PRELAUNCH_AUDIT.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/spec/PRELAUNCH_AUDIT.md))
found [`documentation/WHAT_IS_THIS_AND_BENEFITS.md`](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/documentation/WHAT_IS_THIS_AND_BENEFITS.md)
at a fraction of the bold density of every other outward-facing document
there and added emphasis throughout, which was right for the page as it
stood. The page then grew another group and half again as many items, and at
that density a bold lead-in under every heading marked nothing -- the
headings and the short bolded items were already doing the emphasis. Morgan
asked for the lead-ins to be plain and named the clause a suggestion,
deliberately weak, rather than a gate: a spans-per-100-words ratio cannot
tell a heading-dense page from an under-emphasized one, so a check here
would only re-flag the page he had just fixed.

## Install
No mechanical check: whether a phrase is "key" and whether the bolded share of a document matches its own two rough tests (a skimmer gets the argument; bold still reads as highlighting, not the normal typeface) is a judgment about that document's own content and audience. A count of bold spans can't tell correct restraint from under- or over-bolding without knowing what the document is actually arguing.

