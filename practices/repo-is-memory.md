---
slug:        repo-is-memory
title:       The repo is the memory; sessions are ephemeral
tier:        resident
severity:    default
applies_to:  ["**"]
occasion:    "starting any session cold"
gates:       ["reply"]
checked_by:  null
defines:     []
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 1
---
## Rule
Everything a future session needs — orientation, open items,
decisions, lessons — lives in committed files. A session's chat thread is
disposable; if knowledge exists only in a thread, it is already lost.

## Detail

## Why
Agent sessions (and humans returning after a month) start cold.
Repos that kept context in threads paid a re-derivation tax every session —
re-finding files, re-learning environment quirks, re-making settled decisions.

## Story

## Install
The three living documents below (MAP, TODO, GLOSSARY) plus a
project instructions file (`AGENTS.md`, plus a per-harness pointer file —
see [session-bootstrap](session-bootstrap.md)). Everything else in this
catalog is a refinement of this rule.
