# Conventions become audits

A rule violated once with real cost is promoted to a script that **fails
loudly** — and keeps its origin story in the docstring.

- `practice_audit.py` — scrub (public-safety) + manifest drift + integrity
- `doc_lint.py` — markdown footguns, on the files you touched
- `checkin.py` — the upstream loop: status / scrubbed push / verified record

A chat thread can only *promise* to follow a convention.
A repo can *check* it.

<!-- notes -->
Every audit exists because its rule was broken once despite being written
down. That's the pitch for mechanical enforcement — not distrust, memory.
