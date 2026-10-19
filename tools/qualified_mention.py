#!/usr/bin/env python3
"""Whether a line's mention of a path names another repository's file.

qualified_mention.py -- one rule, used by precedent_materialize (before it
removes a file no source ships any more) and by precedent_check's
rename-updates-links (before it flags a deleted path). Standard library
only, and imported lazily by both, so a checkout that copies some engine
files and not this one still loads either tool.
"""
import pathlib
import re

# A MENTION QUALIFIED BY ANOTHER REPOSITORY NAMES THAT REPOSITORY'S FILE
# (2026-10-19). An individual set stopped shipping tools/human_voice_check.py
# once a shared set shipped its own, and three consuming repositories' docs
# said "OtherSet's `tools/human_voice_check.py`" -- the shared set's checker,
# not the stale copy. Read as plain mentions of the copy, they kept it
# (_stale_ship_keep_reason) and then flagged its deletion
# (precedent_check's rename-updates-links). One answer for both, read off
# the line alone so a checkout with no other set on disk (GitHub's) judges
# it the same way: the line names another repository as `owner/name`
# (this repository's owner, or a github.com URL), or a possessive
# ("OtherSet's") stands right before the path.
POSSESSIVE_BEFORE = re.compile(r"([A-Za-z][\w.-]*)['\u2019]s\s+[`*\"']*(?:\./)?$")
NOT_A_REPO = {'it', 'that', 'there', 'what', 'who', 'here', 'one', 'this',
              'file', 'repo', 'repository', 'set', 'engine', 'pack', 'source'}


def mention_names_another_repo(line, path, own_slug):
    """True when `line`'s mention of `path` (or of its file name) is
    qualified by a repository other than `own_slug` ('owner/name')."""
    own = (own_slug or '').lower().removesuffix('.git')
    owner, _, name = own.partition('/')
    # With no origin to compare against, no slug is "another repository":
    # the same answer precedent_check's _strip_other_repo_urls gives.
    for m in re.finditer(r'(?:github\.com/)?([\w.-]+)/([\w.-]+)', line) if own else ():
        slug = f'{m.group(1)}/{m.group(2)}'.lower().removesuffix('.git')
        if slug != own and ((m.group(0).lower().startswith('github.com/'))
                            or (owner and m.group(1).lower() == owner)):
            return True
    for needle in {path, pathlib.PurePath(path).name}:
        at = line.find(needle)
        while at >= 0:
            m = POSSESSIVE_BEFORE.search(line[:at])
            if m and m.group(1).lower() not in NOT_A_REPO | {name}:
                return True
            at = line.find(needle, at + 1)
    return False
