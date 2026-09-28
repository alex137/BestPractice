---
slug:        private-repo-scrub
title:       Private repo names and specifics get scrubbed before anything vendors or is shared
tier:        on-demand
severity:    blocking
applies_to:  ["**"]
occasion:    "writing content that will vendor or ship into another repo"
gates:       ["merge", "push"]
index_clause: "name a private repo only in general terms in anything that ships elsewhere"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-28"
approved_by: "pending PR review -- moved 2026-09-28 from the shared set precedent-shared-repo-maintenance, Morgan F accepting the session's recommendation to move it (the move: strength assented); the rule itself: Morgan F, migrated from RepoPersonalPreferences by the private-set migration session"
---
## Rule
Anything that actually ships into another repo may describe the situation that prompted a rule only in general terms ("a dependent repo," "an earlier project," "a past install"), never by a private repo's real name, its URL, or specifics about its internal layout that would identify it. This doesn't reach content that never leaves the authoring repo -- its own decision records, its own conventions section, commit messages -- which can and should keep naming the real repo, since that is exactly where the full story belongs.

## Detail
**A convention name is not an identifying name.** Precedent's [source-naming](source-naming.md) fixes a practice set's name by its level -- every person's individual set is called `precedent-individual`, every shared set `precedent-shared-<slug>` -- so those bare strings name a convention that every adopter uses, not anybody's repository. What identifies is the owner: `<owner>/precedent-individual` points at one specific person's private set; `precedent-individual` on its own points at nothing. Scrub the owner-qualified form; leave the bare convention name alone, since vendored content is often *required* to use it.

Keep the complete, specific account in the authoring repo's own decision record: the real repo name, what happened, why it mattered. Alongside it, write out the exact scrubbed sentence that actually appears in the vendored text, labeled "Vendor-safe version:" -- so a later session reuses an already-approved scrub instead of re-deriving one from scratch each time.

**Moving a practice from a private source to a public one is the moment this bites hardest.** A practice written inside a private set names that set's siblings, its people's other repositories and its own incidents freely, because until the move nothing it said left the set. The move is what publishes it, so the rewrite into general terms is part of the move, done before the pull request, never tidied up after.

## Why
Marked blocking because it guards against a real leak of private information into content that, once vendored, ships to every downstream repo -- not something a lower-level preference should be able to override.

## Story
Found the hard way when a team's own rule text, written to be vendored elsewhere, named one of its private repos directly and linked to it in text that shipped on every future install.

Writing the rule's first mechanical check found the exact same thing again, in the set that carried it: another practice's text there named a sibling private set directly, as a worked example. Fixed in the same commit that added the check.

The check's list then went stale in the other direction, and a consuming repo is what surfaced it. `source-naming` landed on 2026-09-06 and turned the individual and team set names from one account's private repo names into the fixed public names every adopter carries. The check still held the bare strings, so a consumer's own gate reported findings against a word the convention obliges it to use -- and, being materialized output, one it could not fix where it was reading it. A blocklist entry has a shelf life: the term it guards can become public without anyone editing the entry.

**Moved to the universal catalogue on 2026-09-28**, from the shared set for repository maintenance, on Morgan's accepting a session's recommendation that it applies to any repository that ships content elsewhere, not only to maintaining practice sets. The move itself needed the rule: the set's text named that account's own private sets and repositories, and each was rewritten in general terms here. The paragraph on moving a practice from private to public is new with the move, and records what doing it involved.

## Install
**The engine's general enforcement is [tools/leak_gate.py](../tools/leak_gate.py)**, run by every push check: it learns private repository names from the sibling clones beside the checkout and from each declared private source, and fails on any it finds in a public tree, alongside the repo's own blocklist. It sees only the names it can learn or was told -- a private repository with no clone beside the checkout and no blocklist entry is invisible to it, which is why a move from private to public also greps its own diff for the names of the repositories the session can see.

The shared set this rule moved from carries a narrower check of its own, a fixed list of one account's private sets in their owner-qualified forms, scanned over `practices/*.md`. It did not move: its list is those private names, so publishing it would be the leak it guards against.
