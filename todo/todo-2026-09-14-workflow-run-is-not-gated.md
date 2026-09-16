---
slug:              todo-2026-09-14-workflow-run-is-not-gated
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "verifying the run behaviour itself against GitHub's own documentation, which a hosted session cannot reach (docs.github.com is blocked by the proxy) — a person with a browser, or the throwaway repository."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-14
closed:            null
---
## What

- <a id="workflow-run-is-not-gated"></a>**`CODEOWNERS` gates the merge of
    an edited workflow, not its first run.** As the 2026-09-14 review
    understands GitHub (unverified, read from no documentation): a Write
    collaborator who edits a file under `.github/workflows/` on their own
    branch gets it executed on push, with the repository's secrets, before
    anyone reviews it. Owning `/.github/` stops it landing, not running once.
    The mitigation is policy: a document project's workflows carry no secret
    beyond the default `GITHUB_TOKEN` and declare a read-only `permissions`
    block. [templates/github-actions/](../templates/github-actions/)'s three
    templates all declare `permissions`; whether each is read-only, and
    whether [templates/document-project/README.md](../templates/document-project/README.md)
    should say so at instantiation, has not been checked.
    **Audited the same day**: all three templates and this repository's own
    three workflows declare `permissions: contents: read`, and the
    document-project README's step 6 now says to keep the workflows
    secret-free. **Blocked on:** verifying the run behaviour itself against
    GitHub's own documentation, which a hosted session cannot reach
    (docs.github.com is blocked by the proxy) — a person with a browser, or
    the throwaway repository. **Disposition:** wait (2026-09-14, the review)

## How It Closes

Not open until: verifying the run behaviour itself against GitHub's own documentation, which a hosted session cannot reach (docs.github.com is blocked by the proxy) — a person with a browser, or the throwaway repository.

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
