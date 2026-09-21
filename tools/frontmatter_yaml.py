#!/usr/bin/env python3
"""frontmatter_yaml.py -- shared real-YAML frontmatter check, called from
both tools/verify_harness.py (check_frontmatter_is_real_yaml, deep check)
and tools/doc_lint.py (light check, gated on touched files: (practice:
two-check-levels), whose Install section folds a repo's own JSON/YAML
syntax checks into the fast pass rather than leaving them deep-only). One
parser, two call sites, so a fix or a new edge case lands once instead of
drifting between two copies.

This repo's own frontmatter reader takes everything after a line's first
colon and is happy with `title: Build/buy: decompose before deciding`.
PyYAML is not -- the second colon opens a nested mapping and it rejects the
whole block. A format whose only conforming parser is its author's is not a
format, so both the fast and the full check hold every scanned file's
frontmatter to a real parser, not just this repo's own reader.
"""
import re

try:
    import yaml as _yaml
    HAVE_YAML = True
except ImportError:
    _yaml = None
    HAVE_YAML = False

_FENCE_RE = re.compile(r'---\n(.*?)\n---\n', re.S)


def frontmatter_yaml_error(text):
    """None if TEXT claims no --- frontmatter, PyYAML is unavailable, or the
    frontmatter is valid; otherwise a one-line reason a real YAML parser
    rejected it. A caller that must tell "PyYAML missing" apart from "valid"
    checks HAVE_YAML itself before calling this."""
    if not HAVE_YAML or not text.startswith('---\n'):
        return None
    m = _FENCE_RE.match(text)
    if not m:
        return 'opens a --- fence that is never closed'
    try:
        _yaml.safe_load(m.group(1))
    except Exception as e:
        return str(e).split('\n')[0]
    return None
