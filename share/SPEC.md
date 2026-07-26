# Share: single-file sharing without sharing the repo

**Status: draft for review — nothing here is implemented yet.** The
delivery plan is in [PLAN.md](PLAN.md).

BestPractice repos are often private: the repo is the memory, and the
memory is full of things outsiders must not see. But work constantly
produces artifacts that *should* go out — a built deck, a rendered
report, one HTML file — and today the options are bad: share the whole
repo (over-shares), or attach files to chat threads (loses the "agent
does the mechanics" premise). **Share** closes the gap: a tiny web
service that authorized users publish individual files to, producing
capability URLs they hand to exactly the people who should read them.

Two deliverables live in this directory when built:

1. **The gateway** — a small edge service any BestPractice user can
   run: use an instance someone else operates, or stand up their own
   with one command. It authenticates publishers and writes into
   object storage; recipients read straight from storage, never
   through the gateway.
2. **The client tooling** — a deployer that provisions/maintains the
   gateway and its storage given the operator's token, and a
   publisher an agent uses to post files, track who they were for,
   and keep links alive.

## Who needs which credential

The design goal this table makes checkable: **all cloud friction
lands on the operator, once; users and recipients never see it.**

| Role | Needs | Obtained how |
|---|---|---|
| Recipient | Nothing — just the link | — |
| User (publisher) | One password | Emailed automatically when the admin adds them |
| Operator | One Cloudflare API token (+ an email-provider API key) | From the provider dashboards, once, at deploy time |

## Terms

| Term | Meaning |
|---|---|
| *gateway* | The running service: authenticates publishers, writes storage. |
| *instance* | One gateway + its storage, at one HTTPS origin pair. |
| *operator* | Whoever deployed the instance; holds the admin token. |
| *user* | A person the operator authorized to publish (name + email). |
| *password* | A server-generated secret proving a user may publish. |
| *scope* | A user-chosen path segment grouping published files. |
| *scope-hash* | The unguessable public form of a scope; part of every read URL. |
| *capability URL* | A read URL; possessing it is what grants reading. |

## Trust model

- The **operator** controls who may publish (the user list) and holds
  the keys (admin token, scope-hash secret, storage credentials,
  email credentials).
- A **user** controls who may read: read URLs contain the scope-hash,
  which only the gateway can derive; a user shares a read URL with
  exactly the intended readers. Anyone holding the URL can read —
  that is the design (capability semantics), so the sharpest rule in
  this spec is: **a read URL is a bearer credential; treat it like
  one** (don't post it publicly, don't log it carelessly).
- **Readers** need nothing: no account, no cookie, just the URL.
- Content is whatever a user publishes. A shared instance's operator
  is hosting other people's files; see "Operating a shared instance"
  below.

Everything rides on HTTPS; the gateway refuses to serve over plain
HTTP outside local development.

## Architecture: a thin gateway over object storage

The gateway owns the *write* path and the user list; the *read* path
belongs to storage:

```
publisher ──POST /in/──► gateway ──put object──► content bucket
recipient ──────────────GET (read URL)─────────► content bucket
```

**One TypeScript codebase, two deployment modes** (the router is
[Hono](https://hono.dev), chosen because the same code runs
unchanged on both runtimes — as of 2026-07):

- **`workers` (default): Cloudflare Workers + R2.** The gateway is a
  Worker; content lives in a public R2 bucket, the user table in a
  second, *private* R2 bucket; expiry is an R2 lifecycle rule. No
  server, no container, no volume — **one provider, one operator
  token**, and typical use fits the free tier (as of 2026-07). A
  side benefit for an internet-facing service: the Worker runs in a
  V8 isolate sandbox — there is no OS or container image for the
  operator to patch, which is a bigger security win than any
  language choice.
- **`container`: the same code on Node, in Docker.** Storage backend
  is local disk (the gateway then also serves `GET /out/...` itself,
  with an in-process TTL sweeper) or any S3-compatible bucket. This
  is the escape hatch for self-hosters and the proof that no
  provider is load-bearing; any Docker host (a VPS, Fly.io, Render)
  works.

Everything user-facing is identical in both modes.

**Why TypeScript** (recorded per practice 5, since the surrounding
repo is Python): the gateway's language never touches users or
dependent repos — only the deployed artifact does. What matters is
the platform, and Workers' native language is TypeScript, with
first-class typed R2 bindings, local runtime emulation for tests,
and the deepest docs and ecosystem on that platform. Alternatives
were weighed: Python on Workers was in beta as of 2026-07;
TinyGo/Kotlin reach Workers only via WASM with weaker tooling and
thinner ecosystems (a worse target for agent maintenance, not a
safer one); Go or Python in a container would be fine languages on
a worse architecture (a second provider, an image to build and
patch). The client tools agents actually run inside repos — the
[publisher](#the-publisher-client-side) and the deployer — stay
plain Python stdlib, so nothing about the repo toolchain changes.

## The gateway

### Publishing: `POST /in/...`

Two equivalent request forms:

```
POST /in/{scope}/{path...}            with header  Authorization: Bearer {password}
POST /in/{password}/{scope}/{path...}   (no Authorization header)
```

The request body is the file's bytes; the request `Content-Type` is
stored on the object and replayed on reads (default
`application/octet-stream`).

The header form is **recommended**: URLs are copied into shell
history, chat messages, and proxy logs, and a password embedded in a
path travels with them. The path form is kept because it makes the
service usable from anything that can POST to a URL, per the original
design intent — with the mitigation that the gateway **never writes
`/in/` paths to its logs** (see "Logging rules").

On success the response is `303 See Other` with

```
Location: {content_base_url}/{scope-hash}/{path...}
```

and a JSON body `{"url": ..., "expires_at": ...}` for clients that
prefer parsing to redirect-following. `content_base_url` is the
content bucket's public domain (or the gateway's own `/out` route in
container-disk mode). Re-POSTing the same scope + path replaces the
content and resets that file's expiry clock — this is the
**refresh** operation; nothing else is needed to keep a link alive.

`DELETE` with the same two auth forms unpublishes early: a full path
deletes one file; a bare scope deletes every file in the scope.

Path rules: 1–64 segments, each matching `[A-Za-z0-9._-]{1,128}`,
no segment equal to `.` or `..`, no empty segments. Scope matches
`[A-Za-z0-9_-]{1,64}`. Anything else is `400`.

### Reading

`GET {content_base_url}/{scope-hash}/{path...}` serves the stored
bytes with the stored `Content-Type`; `HEAD` works. Unknown
scope-hash or path, or expired content: `404` — indistinguishable
from never-existed, so the URL space leaks nothing.

Because the full path structure is preserved under one stable prefix,
**relative links keep working**: publish `site/index.html`,
`site/style.css`, `site/img/logo.png` under one scope and the pages
reference each other exactly as they would on any static host. That
is the mechanism that lets a whole rendered site travel as a set of
individual file POSTs.

One constraint: a bare bucket does not map a directory URL
(`.../site/`) to `index.html`, so **read links always name an
explicit file** (`.../site/index.html`); the publisher tool emits
them that way.

### Passwords: generated, mailed, stored hashed

The admin API (below) creates a user from a name and email address.
The gateway then:

1. generates a random password: 26 characters of base32 (130 bits of
   entropy) — users never choose passwords;
2. emails it to the user (see "Email delivery");
3. stores only `SHA-256(password)` and discards the plaintext.

Because passwords are server-generated high-entropy random values —
never human-chosen — a fast unsalted hash is sound here: there is no
dictionary to attack and no rainbow table for a 130-bit random space.
This is a deliberate deviation from the usual "always use a slow
salted KDF" rule, and it buys the property the URL design needs:
the gateway finds the user by **O(1) hash lookup** on the presented
password, so the `/in/{password}/...` form needs no username and
costs no KDF work per request. If user-chosen passwords are ever
allowed, this decision must be revisited (that would require
scrypt/argon2 and a username in the request).

Lost password = rotate: the admin re-adds the same email, a new
password is generated and mailed, the old hash is replaced.

### Scope-hash: an HMAC, not a plain hash

```
scope_hash = base32( HMAC-SHA256( SCOPE_KEY, email + "\n" + scope ) )[:26]
```

- `SCOPE_KEY` is a per-instance random secret set at deploy time.
  A plain `hash(scope)` would let anyone who guesses the scope name
  ("docs", "deck", "report") compute the read URL — the HMAC is what
  makes the capability URL unguessable.
- The user's email is mixed in so two users choosing the same scope
  name get different, non-colliding scope-hashes.
- The construction is deterministic, so refreshes and multi-file
  publishes land under the **same stable prefix** — links stay valid
  across refreshes, and relative links work.
- 26 base32 characters ≈ 130 bits: unguessable by enumeration.

Rotating `SCOPE_KEY` orphans every outstanding read URL at once
(new writes land under new prefixes; old content ages out via TTL) —
that is the instance-wide kill switch.

### Retention: three days, refreshable

Every file lives `TTL` after its last write (default 72 h,
configurable per instance via `SHARE_TTL_HOURS`).

- **Bucket storage:** enforced by a lifecycle rule (delete objects
  N days after upload); an overwrite is a new upload, so a refresh
  resets the clock. The rule is provisioned by the deployer.
  Lifecycle granularity is daily on the major providers, so bucket
  TTL is expressed in whole days (default 3).
- **Disk storage (container mode):** an in-process sweeper deletes
  expired files at least every 15 minutes; expired means `404`
  immediately even if the sweep hasn't run yet.

Longer lifetimes are the **client's** job: the publisher tool
(below) re-POSTs on a schedule. This keeps the service free of
per-file policy — it enforces one simple invariant, and durability
beyond the TTL always has a live owner actively renewing it.

A useful consequence: losing the instance's storage is an
inconvenience, not a disaster — every live link's content is
re-published by its owner's next refresh cycle.

### Admin API

All admin routes require `Authorization: Bearer {ADMIN_TOKEN}` (an
instance secret set at deploy time).

| Route | Effect |
|---|---|
| `PUT /admin/users/{email}` body `{"name": ...}` | Create user, or rotate an existing user's password; generates + emails the password. |
| `DELETE /admin/users/{email}` | Remove the user; `?purge=1` also deletes all their published files. |
| `GET /admin/users` | List users: name, email, file count, bytes used. Never hashes. |
| `GET /healthz` | Unauthenticated; returns `{"ok": true, "version": ...}` — used by the deployer. |

### Email delivery

Pluggable backend, selected by configuration:

- `api` — an HTTPS email-provider API (adapter interface; first
  adapters: Resend and Amazon SES, as of 2026-07). HTTPS is used
  rather than SMTP because it works identically from Workers and
  from a container — Workers cannot speak SMTP reliably (as of
  2026-07).
- `console` — prints the message to the service log; development
  only (it would defeat "only a hash is stored" if used in
  production, since the log would hold the plaintext).

The mail contains the user's name, the instance origin, the
password, and two sentences of usage.

### Abuse and resource limits

- `SHARE_MAX_FILE_BYTES` (default 50 MB) — oversize POST: `413`.
  Must sit under the platform's request-body limit (Workers: 100 MB
  on the free plan as of 2026-07; verified in [PLAN.md](PLAN.md) M1).
- `SHARE_MAX_USER_BYTES` (default 500 MB) — a POST that would exceed
  the user's total: `413` with a JSON body saying so.
- Failed publish auth is rate-limited (default 10/minute per source
  IP, then `429`) so the password space can't be probed. On Workers
  this is a platform rate-limiting rule provisioned by the deployer;
  in a container, in-process counters.
- No rate limit on reads beyond the storage provider's own.

### Logging rules

Wrong logging silently defeats the security design, so it is
specified, not left to taste:

- **Never** log the path of an `/in/` request (it may contain a
  password). Log method, scope-hash, outcome, byte count.
- Read URLs are capabilities; they stay out of any log kept
  anywhere less protected than the instance itself (relevant to
  container-disk mode's `/out/` route and to bucket access logs,
  which the deployer leaves disabled by default).
- Never log passwords, `ADMIN_TOKEN`, `SCOPE_KEY`, storage
  credentials, or email bodies.

### Configuration reference

Keys are Worker secrets/bindings in workers mode, environment
variables in container mode; names are shared:

| Key | Meaning | Default |
|---|---|---|
| `SHARE_ADMIN_TOKEN` | Admin bearer token | required |
| `SHARE_SCOPE_KEY` | HMAC secret for scope-hashes | required |
| `SHARE_TTL_HOURS` | File lifetime after last write | `72` |
| `SHARE_MAX_FILE_BYTES` | Per-file cap | `52428800` |
| `SHARE_MAX_USER_BYTES` | Per-user total cap | `524288000` |
| `SHARE_CONTENT_BASE_URL` | Public base URL for read links | required |
| *(workers)* content + state buckets | R2 bindings, wired by the deployer | — |
| *(container)* `SHARE_STORAGE` | `disk` or `s3` | `disk` |
| *(container)* `SHARE_S3_*` | `ENDPOINT`, `KEY_ID`, `SECRET`, `CONTENT_BUCKET`, `STATE_BUCKET` | s3 mode |
| *(container)* `SHARE_DATA_DIR` | Blob + user-table location | `./data` |
| `SHARE_EMAIL_BACKEND` | `api` or `console` | `console` |
| `SHARE_EMAIL_*` | `PROVIDER`, `API_KEY`, `FROM` | api mode |

## Hosting and the deployer

### What Cloudflare must provide (workers mode — verify in PLAN M1)

All believed true as of 2026-07; every item is re-verified against
live docs and by hand in [PLAN.md](PLAN.md) M1 before code depends
on it (practice 16):

1. Worker deploys fully driven by `wrangler` with a scoped API
   token — no dashboard.
2. R2: bucket creation, public read via custom domain on the
   content bucket, private state bucket via binding, lifecycle
   rules deleting N days after upload where **an overwrite resets
   the clock** (load-bearing for refresh).
3. Request-body limit comfortably above `SHARE_MAX_FILE_BYTES`.
4. Platform rate-limiting rules attachable to the Worker's `/in/`
   routes.

### The container escape hatch

The same codebase ships as a Node Docker image for any container
host (a VPS behind a TLS proxy, Fly.io, Render) with disk or
S3-compatible storage. No adapter code per host — the image is the
interface. This is what keeps Cloudflare from being load-bearing:
the design survives any single provider's pricing or policy change.

### The deployer

`deploy.py` (in this directory when built) — plain Python driving
`wrangler` and the Cloudflare API; idempotent "make it so":

```
python3 share/deploy.py --name my-share [--domain share.example.com]
```

- Reads the operator's Cloudflare token from the environment
  (`CLOUDFLARE_API_TOKEN`) and email-provider key from
  `SHARE_EMAIL_API_KEY`; never from flags, never written to disk.
- Provisions storage: creates the content and state buckets if
  absent, enables public read + custom domain on content, sets the
  lifecycle rule from the TTL.
- Provisions the gateway: generates `SHARE_ADMIN_TOKEN` and
  `SHARE_SCOPE_KEY` on first deploy and sets them as Worker secrets
  (printing the admin token once, to the operator); wires bucket
  bindings, email configuration, and the rate-limiting rule;
  deploys the Worker.
- Waits for `GET /healthz` to return the deployed version.
- Re-run any time: no-op when current, redeploy when the local
  gateway version differs — that is the "maintain" half.
- Build-time needs Node + `wrangler` (declared in the gateway's
  `package.json`); the deployer checks and says so rather than
  failing obscurely.

## The publisher (client side)

`publish.py` (in this directory when built) — plain Python stdlib,
because this is the piece dependent repos vendor and agents run
everywhere. Configuration via environment: `SHARE_ORIGIN` (gateway
URL) and `SHARE_PASSWORD` (the user's mailed password — a secret, so
it lives in the agent environment or a local untracked file,
**never committed**).

### The registry

The publisher maintains a small JSON registry — the committed table
of what has been shared, for whom, for how long:

```json
{
  "entries": [
    {
      "id": "q3-deck",
      "files": ["deck/q3/Q3_Update_send.html"],
      "scope": "b3f7c2a9d4e1",
      "recipients": "johndoe@some-domain.com",
      "lifetime_days": 30,
      "first_published": "2026-07-24",
      "last_refreshed": "2026-07-24T09:00:00Z",
      "url": "https://share.example.com/GEZDGNBVGY3TQOJQ.../Q3_Update_send.html"
    }
  ]
}
```

- `scope` is generated per entry: a fresh random token, so each share
  has its own capability URL and can be revoked independently.
- `recipients` is a **label for humans** — the service never sees it;
  it exists so "what did we share with johndoe, and until when?" has
  a committed answer (practice 1).
- **Caveat for the registry's location:** `url` values are
  capabilities. In a private repo, committing the registry is exactly
  right — shared state, auditable. In a public repo the registry must
  be untracked, or every reader of the repo can read every shared
  file.

### Commands

| Command | Effect |
|---|---|
| `publish FILE... --id ID --to LABEL --days N` | New scope, POST each file, record entry, print the read URL(s). |
| `refresh` | For every entry within its lifetime: re-POST all files (resetting the TTL clock); prune entries past their lifetime (DELETE the scope server-side). |
| `list` | The registry as a table: id, recipients, expiry of the *lifetime*, last refresh. |
| `revoke ID` | DELETE the scope server-side, mark the entry revoked. |

`refresh` must run at an interval comfortably under the instance TTL
(72 h) for lifetimes to hold. How it gets run is the repo's choice:
a scheduled agent session (a Routine / cron trigger), a session-start
hook, or the habit that any working session runs it. The registry's
`last_refreshed` makes staleness visible: `list` warns loudly when
any live entry is within 12 h of TTL expiry.

### The workflow this exists for

> User: *send a link to* `deck/q3/Q3_Update_send.html`
> *to johndoe@some-domain.com, good for a month*

The agent runs
`publish deck/q3/Q3_Update_send.html --id q3-deck --to johndoe@some-domain.com --days 30`,
commits the registry update, and replies with the URL. The user
forwards the link over Signal or WhatsApp. For the next month, any
refresh cycle keeps it alive; on day 31 the entry is pruned and the
service forgets the file ≤72 h later.

Worth remembering: for a **single self-contained HTML file** (which
the [deck engine](../deck/README.md) produces by design), simply
attaching the file to the chat remains the zero-infrastructure
path — no link, no expiry, no service. Share earns its keep when the
artifact is multi-file, or the recipient experience must be
click-a-link.

## Operating a shared instance

A shared instance means the operator is hosting files they didn't
choose. Minimum posture: publish an abuse contact on the instance's
front page; the admin API's user list plus per-user byte counts is
the accountability mechanism (every file traces to an authorized
user); `DELETE /admin/users/{email}?purge=1` is the remedy. The
72 h TTL is itself the best abuse limiter — nothing stays up without
an active owner. Operators should also know their providers' terms
of service make them, not the users, answerable for content.

## Relation to the scrub gate

Publishing a file from a private repo takes it outside the repo's
protections — a read URL can be forwarded by any recipient. The
publisher therefore runs the same check the check-in gate uses: if
the repo has a `process/scrub_blocklist.txt`, `publish` scans the
outgoing bytes and refuses on a hit (override with
`--allow-blocklisted`, for the case where sharing the file is the
point). Deliberate, auditable, one flag.

## Open questions (answer before M2)

1. **Read-side auth:** is capability-URL-only right, or should a
   scope optionally require a read password too? Spec says
   capability-only (matches the stated design); flag if the threat
   model needs more.
2. **Shared flagship instance:** does anyone stand up a public
   instance for BestPractice users at large, and who operates it?
   The spec works either way; the README wording depends on it.
3. **Quota defaults** (50 MB/file, 500 MB/user, 72 h): confirm or
   adjust.
