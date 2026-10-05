---
slug:        private-repo-scrub
title:       Private repo names and specifics get scrubbed before anything vendors or is shared
tier:        on-demand
severity:    blocking
applies_to:  ["**"]
applies_to_why: "Any file can be content that ships, depending on what a repository vendors out, so no single glob names them; the occasion index reaches the moment of writing it, and the check reads practices/*.md, the part every source ships."
occasion:    "writing content that ships into another repo"
gates:       ["merge", "push"]
index_clause: "name a private repo only in general terms"
index_required: true
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-05"
approved_by: "Morgan F, drafted 2026-10-05, moved from the shared set precedent-shared-repo-maintenance; merged in PR #880 on 2026-10-05"
strength: decided
---
## Rule
Anything that actually ships into another repo may describe the situation that prompted a rule only in general terms ("a dependent repo," "an earlier project," "a past install"), never by a private repo's real name, its URL, or specifics about its internal layout that would identify it. This doesn't reach content that never leaves the authoring repo -- its own decision records, its own conventions section, commit messages -- which can and should keep naming the real repo, since that is exactly where the full story belongs.

## Detail
**A convention name is not an identifying name.** Precedent's `source-naming` fixes a practice set's name by its level -- every person's individual set is called `precedent-individual`, every shared set `precedent-team-<slug>` -- so those bare strings name a convention that every adopter uses, not anybody's repository. What identifies is the owner: `<owner>/precedent-individual` points at one specific person's private set; `precedent-individual` on its own points at nothing. Scrub the owner-qualified form; leave the bare convention name alone, since vendored content is often *required* to use it.

Keep the complete, specific account in the authoring repo's own decision record: the real repo name, what happened, why it mattered. Alongside it, write out the exact scrubbed sentence that actually appears in the vendored text, labeled "Vendor-safe version:" -- so a later session reuses an already-approved scrub instead of re-deriving one from scratch each time.

## Why
Marked blocking for the same reason as scrubbing sensitive characterizations: it guards against a real leak of private information into content that, once vendored, ships to every downstream repo -- not something a personal writing preference should be able to override.

## Story
Found the hard way when a team's own rule text, written to be vendored elsewhere, named one of its private repos directly and linked to it in text that shipped on every future install.

Writing this practice's own `checked_by` found the exact same thing again, in this repo: the install practice's own text named a sibling private set directly, as a worked example. Fixed in the same commit that added the check.

The list then went stale in the other direction, and a consuming repo is what surfaced it. `source-naming` landed upstream on 2026-09-06 and turned `precedent-individual` and `precedent-team-repo-maintenance` from this account's private repo names into the fixed public names every adopter carries. The check still held the bare strings, so a consumer's own gate reported findings against a word the convention obliges it to use -- and, being materialized output, one it could not fix where it was reading it. A blocklist entry has a shelf life: the term it guards can become public without anyone editing the entry.

**Considered for the universal catalogue on 2026-09-28, and kept here.** Morgan approved moving the rules in this set that apply to any repository into universal (strength: assented). This one was taken back out of that move before it merged: its enforcement was a script in that set, `check_private_repo_scrub.py`, holding a list of this account's private set names, which cannot be published. A universal copy with the same slug would have won over this one, and the check would have stopped reaching the consumers it protects. So the rule stays where its check can run; BestPractice's own general enforcement remains [`tools/leak_gate.py`](https://github.com/alex137/BestPractice/blob/staging/tools/leak_gate.py).

**Moved into universal on 2026-10-05**, as pass 2 of folding the repository-maintenance set into universal (Morgan, strength: decided). What stopped it on 2026-09-28 was the check's literal list of one account's private sets. The universal check carries no list: it asks each source in force here whether it declares itself private, and reads the owner-qualified name from that source's own `origin`.

## Install
Checked mechanically by [tools/precedent_check.py](../tools/precedent_check.py)'s `private-repo-scrub` check, scope `tree`, over `practices/*.md` -- the content that ships into other repositories. It builds its word list at run time from the sources in force: each one whose `precedent-source.json` declares `visibility` other than `public` (an individual set that says nothing counts as private) contributes its owner-qualified name, read from its own `origin`, and that name's github.com URL contains it. A bare convention name is never flagged. Where no private source is in force, the check reports skipped. README files, commit messages and decision records are not scanned: they stay local, and the Detail says that is where the full story belongs. Its planted case in `tools/verify_harness.py` brings a private individual set through the person's config and names it in a practice file.
