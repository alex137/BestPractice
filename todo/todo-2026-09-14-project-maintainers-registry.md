---
slug:              todo-2026-09-14-project-maintainers-registry
kind:              analysis
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "item `generated-views-are-owned-paths` — the owned-path list is what the generator would write, and it is still being decided. **BUILT 2026-09-14, the same day, once item 108 was decided**: [tools/build_codeowners.py](../tools/build_codeowners.py) reads `maintainers` and `owned_paths` from a project's "
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="project-maintainers-registry"></a>**A document project's
    `CODEOWNERS` is hand-written while a practice set's is generated — two
    mechanisms for one question.**
    [tools/build_codeowners.py](../tools/build_codeowners.py) derives a set's
    file from `approvers.json`; the project template's
    [CODEOWNERS](../templates/document-project/.github/CODEOWNERS) says in its
    own header that it is not. A `maintainers` field in the project's
    `precedent.json`, and the same generator writing the project file from
    it, makes onboarding one invite plus one line and keeps the owned-path
    list in one place ([registry-source-of-truth](../practices/registry-source-of-truth.md)).
    Finding under "Define, manage, limit, control" in the 2026-09-14 review.
    **Blocked on:** item `generated-views-are-owned-paths`
    — the owned-path list is what the generator would write, and it is
    still being decided.
    **BUILT 2026-09-14, the same day, once item 108 was decided**:
    [tools/build_codeowners.py](../tools/build_codeowners.py) reads
    `maintainers` and `owned_paths` from a project's `precedent.json` when
    there is no `approvers.json`, writes `.github/CODEOWNERS` with one row
    per owned path and its reason, and takes `--repo PATH`. The set mode
    renders byte-for-byte what it did before — all three team sets'
    committed files still `--check OK`. The document-project template's
    CODEOWNERS is generated output now, and its README step 7 fills in the
    registry instead of the file. **Disposition:** wait (2026-09-14; done,
    kept for the record)

## How It Closes

Not open until: item `generated-views-are-owned-paths` — the owned-path list is what the generator would write, and it is still being decided. **BUILT 2026-09-14, the same day, once item 108 was decided**: [tools/build_codeowners.py](../tools/build_codeowners.py) reads `maintainers` and `owned_paths` from a project's 

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
