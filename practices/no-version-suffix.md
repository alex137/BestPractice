---
slug:        no-version-suffix
title:       Filenames have no version suffix; the VCS is the version
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "naming a new file"
index_clause: "name a file for what it is; the repository is the version"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 18
---
## Rule
A new file is named for what it *is*, with no `_v1` / `_rev2` label —
the repository already versions every line, so a version number baked into the
filename is redundant at best and misleading at worst (it goes stale the moment
the file is edited without a rename). A numeric suffix earns its place only when
two versions must **coexist** and a reader has to tell them apart (a successor
kept beside its predecessor for history); then it is the *new* file that is
suffixed, not the old one retro-renamed. An existing suffixed backlog is left
alone — bulk-renaming breaks the very references (links, records) the names are
load-bearing for; drop the suffix only from a file already being moved for
another reason, fixing its references in the same pass.

## Detail

## Why
"`_v1`" is the classic redundant-with-VCS habit: it answers a question
the version-control history already answers, and unlike the history it does not
update itself — a `_v1` file edited fifty times still says `_v1`, so the label
actively lies. It also invites a rename on every real revision (churning the
references), or worse, a `_v2` copy that forks the file and splits its history.
Naming for identity instead keeps one stable handle per document and lets the
tool whose job is versioning do the versioning.

## Story

## Install
A naming convention; no tooling needed. The one judgment call —
"do two versions genuinely need to coexist?" — is rare and deliberate, so it is
left to the author rather than a lint.
