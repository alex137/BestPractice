---
slug:        filename-separator
title:       One word separator per directory, and never two for the same kind
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Every directory that holds files, which is every path -- the rule is about a directory's contents as a set, so no narrower glob describes it. Enforced tree-scope instead of routed. Decided: 2026-09-08, when the practice landed."
occasion:    "naming or adding a file"
gates:       ["push"]
gates_why:   "The rule is a property of the tree at rest, and the push check's full sweep runs its tree check, so a mixed directory is refused at push before it reaches a shared branch. index_required: false records that the push arrives in time: renaming a file before it is shared costs nothing. Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: decided)."
index_clause: "beside others of its kind: one word separator; never both - and _"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-08"
approved_by: "Morgan, 2026-09-08; push gate, index line dropped: Morgan, 2026-10-01 (\"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)\", strength: decided)"
---
## Rule
**Files of the same kind, in the same directory, use the same word
separator.** Not both `BUSINESS_RISKS.md` and `BUSINESS-MODEL-CONCEPTS.md`
side by side. "Same kind" means same directory and same extension — the set
a person scanning that folder reads as one list.

**Which separator is usually not a choice, and asking who picked the name
settles it:**

- **A name something else determines** — a language's import rules
  (`build_views.py`; Python cannot import a hyphen), a platform's required
  filename (`pull_request_template.md`), a slug the catalogue already owns
  (`go-update.md`), or the name of the file this one generates
  (`leak-blocklist.txt.template`) — takes that separator, and mixing is fine
  because nobody chose either one.
- **A name nobody else determines** — an ordinary document — takes the
  directory's existing convention. If the directory is empty, pick one; if
  it already has three files, you have already picked.

**When a directory does mix and every name was determined elsewhere, say
which one determined each.** An exemption nobody can name a reason for is
the inconsistency this rule exists to stop, wearing a justification.

**When a person asks for a name that breaks the directory's convention, say
so before creating it**: one sentence naming the convention, with a link to
this practice, and the name that would fit. If they still want theirs, use
it and record the exemption then, with their words as the reason. Never
rename silently, and never exempt silently.

## Detail
**The rule is per directory, not per repository, because that is where the
cost lands.** A reader scanning one folder sees one list; a repository-wide
mandate would force renames across vendored trees, generated output and
language-mandated names, all to fix something nobody was confused by.

**Renaming is not free** — [rename-updates-links](rename-updates-links.md)
applies in the same commit, and a file other repositories vendor or link to
should usually be left alone and the *new* files brought into line instead.
Consistency going forward beats a rename sweep that breaks inbound links.

**Some names are not yours to choose, and the first question is whether
the check can be taught that, rather than exempted from it.** A file whose
name must MIRROR something outside the directory — the file it is pasted
into, an external tool's expected name, a name other repositories vendor
verbatim — has no freedom to be consistent with its neighbours, and forcing
it costs the correspondence that made the name useful. **Where an engine
tool fixes the name, declare it in that tool** as a module-level `*_NAME`
constant: the check reads those, so every repository stops counting the
name at once, and no exemption is needed anywhere. A year-month-day date inside a
stem is already ignored for the same reason. **Only when the check cannot
learn it**, exempt the directory with that as the reason, and a `root_fix`
saying why ([upstream-fix](upstream-fix.md)): a better answer than a rename
that breaks inbound links across repositories, and a much better one than a
mixed directory nobody has explained. **Say which external name each side follows**, so the next reader
can tell this from an unexplained mess — that is the whole difference
between an exemption and a shrug. (Raised 2026-09-08 by a dependent voice
repository whose `templates/` mixed both separators because each file's name
matched the file it is pasted into, and every one is vendored by name in
turn.)

**The two separators have nicknames, and this practice avoids them on
purpose.** You will see *snake_case* (words joined by underscores) and
*kebab-case* (words joined by hyphens — the picture is food on a skewer) in
programming writing. They are jargon, they are easy to mix up, and nothing
here needs them: say **hyphen** and **underscore**, which nobody has to
learn. Recorded because a session used both nicknames in a reply without
glossing either, which is what [readers-vocabulary](readers-vocabulary.md)
exists to stop.

**Case is a separate question and this rule does not touch it.**
`ALL_CAPS.md`, `Title-Case.md` and `lowercase.md` are all fine; what is not
fine is two separators for the same kind of file in one place.

**What this repository actually uses, measured rather than declared** — the
pattern is that the separator follows *what reads the name*:

| Directory | Separator | Why |
|---|---|---|
| `practices/` | hyphen (78 files) | the filename **is** the slug a tool looks up |
| `tools/` | underscore (48 files) | Python cannot import a name with a hyphen |
| `spec/` | underscore (22 files) | documents in capitals, read by a person |
| `decisions/`, `.claude/hooks/` | hyphen | dated slugs and hook names, looked up by name |

No directory here mixes them, and none of those choices was free: three of
the four are forced by whatever consumes the name.

## Why
A folder is a list, and an inconsistent list makes a reader stop and ask
whether the difference means something. It never does — which is exactly why
it costs attention every time rather than once.

The second cost is worse and quieter: **anything that matches filenames by
pattern has to handle both forms, or silently miss half of them.** A glob, a
link check, a sync tool, a person's `grep` — each becomes a place where the
inconsistency can turn into a bug rather than an irritation.

## Story
**Raised by Morgan, 2026-09-08**, from a real folder: a project's
`business-modeling/` held `BUSINESS_RISKS.md`, `CASE_CORPUS.md` and
`REVENUE_MODEL.md` beside `BUSINESS-MODEL-CONCEPTS.md`, `ONE-PAGER.md` and
`ONE-PARAGRAPH.md` — eight snake, three kebab, all the same kind of
document, nothing distinguishing the two groups. He asked for it as a
universal rule rather than that project's own, and the measurement is why
the rule is shaped the way it is.

**The naive rule — "one separator per directory" — was written first and
measured against real trees before shipping, which is what killed it.** It
flagged `tools/`, where every `.py` file must be snake because Python cannot
import a hyphen, next to a `leak-blocklist.default.txt` that is named after
the thing it is. And it flagged `templates/`, where
`pull_request_template.md.template` and `leak-blocklist.txt.template` are
each named after the file they produce — one of those names is GitHub's to
choose, not this repository's.

That is the whole insight: **the separator is usually inherited, and a rule
that does not know the difference between an inherited name and a chosen one
generates findings nobody can act on.** A check producing permanently
unactionable output is one people learn to skip, which costs more than the
rule protects.

**Push gate, and off the occasion index, from 2026-10-01.** The reduction pass for precedent-individual's session-start file ([the session-file open item](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-09-30-session-file-cut-to-4000.md)) counted this among the lines a mechanical check already refuses at push: its tree check runs in the push check's full sweep. no-version-suffix keeps the shared "naming or adding a file" line. Morgan approved (strength: decided): *"Booked, attach both shared sets, and do both Tier 2 items (and note as a possibility for the future in a Todo the other tier 2 items to consider)"*

## Install
Enforced by [tools/precedent_check.py](../tools/precedent_check.py), which
groups tracked files by (directory, extension) and reports a group using
both separators. It ignores vendored and materialized trees — those names
belong to whoever produced them — and takes an exemption list in
`precedent.json` where a mixed group is genuinely all-inherited:

```json
"filename_separator_exempt": [
  {"path": "templates", "ext": ".template",
   "reason": "each is named after the file it generates, and those names are set elsewhere"}
]
```

**The reason is mandatory**, the same discipline `not_binding` already uses:
an exemption nobody argued for is the silence this check replaces.

**Names a tool fixes are collected, not listed.** Every module-level
constant named `*_NAME`, `*_FILENAME` or `*_MANIFEST` in the engine's
`tools/` whose value is a file name (`CONFIG_NAME = 'reply_check.json'`) is
skipped. Until 2026-09-29 that was a hand-kept set holding only
`precedent-source.json`, so a set carrying `reply_check.json` beside
`very-deep-check-decisions.json` was refused for a clash no one in it could
fix, and exempted its whole root to get past it. The exemption hid the
cause; the fix was to teach the check (Morgan, 2026-09-29, strength:
decided: an exemption is a root-fix opportunity).

What the check cannot see, and a reader should: a directory that is
internally consistent and wrong for its kind (a `practices/` full of
`SCREAMING_SNAKE.md` is uniform and still breaks the slug convention), and
two directories that disagree with each other where a person moves files
between them.
