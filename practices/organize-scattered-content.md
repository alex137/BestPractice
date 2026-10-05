---
slug:        organize-scattered-content
title:       Scattered end-user content gets a recommendation to group it
tier:        on-demand
severity:    advisory
applies_to:  ["**"]
applies_to_why: "Scattered content is a state of the whole tree, not of one path, so no narrower glob names it; the occasion index reaches it."
occasion:    "about four or more end-user content files sit scattered around a repo"
gates:       []
index_clause: "name a directory and its files, ask, move nothing until yes; recheck later"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  ["content-directory", "content-subdirs"]
overrides:   null
added:       "2026-10-05"
approved_by: "pending PR review -- drafted 2026-10-05 by Morgan F, moved from the shared set precedent-shared-working-style"
strength: decided
source_practice_number: null
---
## Rule
When **about four or more content files meant for end users** -- the
documents people actually read, not the machinery that runs the repo -- sit
scattered around a repo, **recommend to the person that you organize them
together**: name the directory, list the files that would move into it, and
ask. Move nothing until they say yes.

**Check again every so often**: when a session adds another content file,
and when a session starts in a repo it has not looked at in a while. Raise
it again only when the picture has changed since the last time it was
raised.

## Detail
- **Four is a guide, not a count to hit.** Three closely related chapters
  may be worth grouping; six files with nothing in common may not be.
- **The directory says what the files are** -- `book/`, `guides/`,
  `proposals/` -- rather than a generic name like `content/`.
- **Machinery stays where it is**: `AGENTS.md`, `README.md`, `MAP.md`, a
  glossary, tool scripts, hooks and config.
- **A layout the repo already has wins.** This is for files that have no
  home, not a reason to rearrange one that works.
- **A move repoints every link** to the moved files in the same commit
  ([rename-updates-links](https://github.com/alex137/BestPractice/blob/staging/practices/rename-updates-links.md),
  universal).
- **A no is remembered.** When the person declines, the same files are not
  raised again; a new batch of scattered files is a new question.

## Why
The two rules this replaces each carried a fixed answer -- always a
`content/` directory, or group once the root holds three documents -- and
too many repos fit neither: a code repo whose documents belong beside the
code, a repo with a `docs/` folder of its own, a project with three files
that are fine where they are. The question that keeps coming back is
simpler: are the things people read getting hard to find? A recommendation
with a named directory and a named list of files lets the person answer it
in one line.

## Story
2026-09-29, Morgan: *"I put in a practice at some point that content files
should go into a content/ directory. But I've been finding, so many
situations that doesn't apply and doesn't make sense, so maybe we remove
that, and instead replace it with another rule: when there are various
content files (maybe 4 or more?) for end-users that are scattered around,
that you should recommend to the session user that you guys organize them
together, like suggest a directory and which files should go in. And repeat
that check every once in a while."* The writing set's `content-subdirs`,
the same idea at three files in the root, was retired with it the same day
(*"Let's eliminate that one also"*), so one rule says it instead of two.

## Install
No mechanical check: whether files are scattered, and whether they are for
end users, is a judgment about what a reader needs. Reached through the
occasion index.
