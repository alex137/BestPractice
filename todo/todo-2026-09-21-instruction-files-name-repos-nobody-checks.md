---
slug:              todo-2026-09-21-instruction-files-name-repos-nobody-checks
kind:              manual
domain:            tooling
severity:          medium
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "Build it inside the very deep check, beside the per-source probe -- Morgan, 2026-09-21"
decision_strength: decided
waiting_on:        null
noted:             2026-09-21
closed:            2026-09-21
---
## What

An always-loaded instructions file can name a repository that does not
exist, and nothing asks. Found 2026-09-21 in an Update Vendors pass: a
consuming repo's `AGENTS.md` named `VoiceDefinitionMorgan` **twice** — in
the session-start step and again in a tool's description — where the real
repository is `VoiceDefMorgan`. The file's own step 1 warns about a source
name going stale silently.

## Why nothing caught it

Two checks come close and neither asks this question.

- `repo-reference-allowlist` (in [tools/precedent_check.py](../tools/precedent_check.py))
  asks **may this name be mentioned here** — a leak control. It runs in the
  push gate, offline, deliberately, so it cannot ask whether the name
  resolves.
- [tools/very_deep_check.py](../tools/very_deep_check.py) **does** ask
  GitHub, via `_api_json('repos/{owner}/{name}')`, but only about the
  repositories in force as sources. A name in prose is not a source.

So a repository reference is checked for *permission* and never for
*existence*.

## The fix

Collect every `owner/repo` string from the always-loaded instructions files
in each repo in scope, and pass each through the existence probe
`very_deep_check.py` already uses. A 404 is a finding; a redirect means a
rename, which is the more interesting one, because it keeps working until
somebody takes the old name.

Until it lands, this is a hand-run step in `very-deep-check`'s pass 3
(the close-read item added the same day), which names this file.

## Answered and built, 2026-09-21

Morgan chose the first shape: inside the very deep check, beside the
per-source probe. Built as `instruction_file_repo_refs_audit()` in
[tools/very_deep_check.py](../tools/very_deep_check.py), reported in its own
`instruction-file repo references` line, and it shares the existing probe's
calls -- a name already asked about as a source is never asked twice, so the
bill this tool reports stays honest.

The pattern is anchored two ways, and the second is what makes it usable: a
full `github.com` URL, or a bare `owner/name` whose owner appears on a real
remote in this session. Unanchored, `owner/name` matches `practices/park-it.md`
and `tools/doc_lint.py` on nearly every line, and a probe reporting fifty
phantom repositories is one nobody runs twice. Seven stated cases in
[tools/verify_harness.py](../tools/verify_harness.py), of which the noise
control is the load-bearing one.

First real run here found two references and one worth knowing about:
`alex137/GitAround`, named in `WHERE_THINGS_ARE.md`, which this session
cannot reach -- correctly reported as NOT CHECKED with the reason, never as
a claim that it is missing.

## The question, as it stood

**The API budget.** `very_deep_check.py` reads and reports its own GitHub
bill, deliberately, and this adds one request per distinct repository named
across every instruction file in scope. That is small, and it is not zero,
and this check is the one place where spending is a declared concern rather
than an afterthought.

Two shapes, and the choice is yours:

- **Inside the very deep check**, alongside the existing per-source probe.
  Rare, already budgeted, reported in the same section. Costs a handful of
  requests per run.
- **Its own occasional tool**, run when an instructions file is edited
  rather than on every deep check. Cheaper per deep check, and one more
  thing that only runs when somebody remembers — which is how this class of
  staleness happens in the first place.

My recommendation is the first. The cost is a handful of requests on a
check that already asks GitHub about every repository in force, and the
alternative relies on the exact habit that failed here.
