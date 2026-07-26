# Share: delivery plan

The specification is [SPEC.md](SPEC.md). This plan turns it into
working code in six milestones, each independently mergeable and each
leaving the repo in a coherent state (a session picking up cold at
any milestone boundary finds the spec, this plan, and everything
built so far).

## Milestones

### M0 — Spec sign-off *(this PR)*

Review [SPEC.md](SPEC.md); answer its five open questions (framework,
single-provider Worker variant, read-side auth, shared instance,
quota defaults). Decisions get recorded by editing the spec — the
spec stays the single source of truth; this plan only sequences it.

**Done when:** open-questions section is empty and the PR is merged.

### M1 — Provider verification spike *(small; no service code)*

The host and storage claims in the spec are dated 2026-07 and
unverified against live APIs. Before code depends on them, verify by
actually doing each once with scratch resources:

- **Cloudflare R2 (storage, primary):** scoped-token bucket
  creation; public read via custom domain; lifecycle rule deleting
  N days after upload; and the load-bearing one — **an overwrite
  resets the lifecycle clock** (the whole refresh design leans on
  this; if it fails, refresh must become delete-and-rewrite or
  copy-in-place, and the spec's Retention section changes).
- **Fly.io (gateway host):** token-scoped app creation, secret
  setting, deploy, all API/CLI-driven end to end.
- Record results *with dates* in a short `HOSTS.md` in this
  directory: exact API endpoints/CLI invocations used, token scopes
  needed, anything that contradicts the spec (practice 16: volatile
  facts carry verification dates).

**Done when:** `HOSTS.md` exists with dated, reproduced-by-hand
steps for both providers and an explicit verdict on
overwrite-resets-lifecycle.

### M2 — Gateway core *(the heart of the work)*

`share/service.py` (plus the storage abstraction): publish, expiry,
both backends.

- Storage backend interface with both implementations: `bucket`
  (S3-compatible: put/delete/list, user table in the private state
  bucket) and `disk` (blobs + user table on disk, `GET /out/...`
  route, in-process TTL sweeper).
- `POST`/`DELETE /in/...` — both auth forms; path validation;
  content-type capture; 303 + JSON response with the
  backend-appropriate `content_base_url`.
- Scope-hash HMAC derivation; quota enforcement (per-file and
  per-user); auth-failure rate limiting.
- Logging exactly per the spec's logging rules.
- Users are inserted by a dev script for now (admin API is M3);
  passwords hashed per spec from day one.
- Tests (`share/test_service.py`, stdlib `unittest`, disk backend +
  a fake in-memory bucket): the auth matrix (header form, path
  form, bad password, rate limit), path traversal attempts, quota
  edges, expiry-resets-on-rewrite, the relative-links property
  (publish two files, follow a relative reference), and log-hygiene
  (assert `/in/` paths never appear in captured logs).

**Done when:** tests pass; a local `curl` round-trip in disk mode
(POST → redirect → GET, wait past a short test TTL → 404) works as
scripted in the module docstring; the same round-trip works in
bucket mode against a real R2 bucket by hand.

### M3 — Admin API + email *(small)*

- `PUT`/`DELETE`/`GET /admin/users...`, `GET /healthz` per spec.
- Email backends: `smtp` (stdlib) and `console`; the
  password-generation → mail → store-hash-only flow.
- Tests: rotation replaces the hash, `?purge=1` removes content,
  admin routes reject non-admin tokens, console backend never runs
  under a production flag.

**Done when:** a user can be created end to end against a locally
running instance with the console backend, and publish with the
mailed (printed) password.

### M4 — Deployer *(depends on M1, M3)*

`share/deploy.py` per spec: Fly.io gateway + R2 storage.

- Idempotent provision/deploy/verify loop across both providers:
  buckets (create, public read, custom domain, lifecycle rule from
  TTL) and gateway (app, secrets generated on first deploy, image,
  health-check gate on `/healthz` version). Tokens from environment
  only.
- Dockerfile for the gateway (also the disk-mode escape-hatch
  artifact).
- A real instance is deployed and stays up as the reference/test
  instance (operator + billing per the M0 shared-instance answer).

**Done when:** running the deployer twice from a clean checkout
produces a live instance then a verified no-op, documented in
`HOSTS.md` with dates.

### M5 — Publisher *(depends on M2; can start in parallel with M4)*

`share/publish.py` per spec: registry, `publish` / `refresh` /
`list` / `revoke`, scrub-blocklist check, staleness warning,
explicit-file read links (no directory URLs).

- Tests against a local disk-mode instance: fresh scope per entry,
  refresh resets server expiry, prune-after-lifetime deletes
  server-side, revoke, blocklist refusal + override flag.
- Docs: a "how a dependent repo wires the refresh cadence" section —
  Routine/cron, session-start hook, or manual — with the
  registry-location caveat (private repo: commit it; public repo:
  untrack it) stated where users will actually see it.

**Done when:** the spec's workflow example runs end to end against
the M4 instance: one command publishes, the registry commit shows
who it was for, `refresh` keeps it alive, lifetime expiry prunes it.

### M6 — Hardening + storage neutrality *(cleanup)*

- Prove the bucket backend is genuinely S3-neutral by running it
  against Amazon S3 (or another S3-compatible store) unchanged;
  record differences in `HOSTS.md`.
- Abuse-posture items: instance front page with operator contact,
  `list`-style admin visibility already in place from M3.
- Revisit quotas/limits against real usage; fold lessons back into
  [SPEC.md](SPEC.md).
- Update the repo's top-level [README](../README.md) layout table
  and [AGENTS.md](../AGENTS.md) quick index (row added at M0 already
  points here).

**Done when:** the same gateway build runs green against two
S3-compatible providers, and the spec matches what is actually
running.

## Sequencing at a glance

```
M0 spec ──► M1 providers ──────► M4 deployer ──► M6 hardening
   │                                  ▲               ▲
   └──────► M2 gateway ──► M3 admin ──┘               │
                 └───────► M5 publisher ──────────────┘
```

M2 is the long pole; M1 is deliberately first and tiny so provider
surprises — above all the lifecycle-reset question — arrive before,
not after, the service is built around them.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Lifecycle rules don't reset on overwrite | M1 verifies this first, by hand, before M2 starts; fallback designs (delete-and-rewrite refresh) identified in M1. |
| Provider API drift invalidates deployer assumptions | M1 verifies by doing, `HOSTS.md` dates everything (practice 16); disk-mode Dockerfile means no provider is load-bearing. |
| Secret leakage via logs or URLs | Logging rules are spec'd, not advisory; M2 has a test asserting `/in/` paths never hit logs; bucket access logs stay disabled. |
| Storage loss breaks live links | By design: refresh cycles republish everything (spec, Retention). |
| Email deliverability (passwords not arriving) | SMTP backend is provider-agnostic; admin rotation is the retry path; M3 keeps `console` for dev only. |
| Shared-instance abuse | 72 h TTL, per-user quotas + accounting, purge remedy, operator contact (spec, Operating a shared instance). |
| Capability URLs committed to a public repo | Registry-location caveat in spec + publisher docs (M5); scrub gate integration refuses blocklisted content. |
