#!/usr/bin/env python3
"""One formatter per quantity kind (practice: one-formatter-per-quantity) — the engine.

A reader comparing two table cells must never have to normalize
precision in their head ("2 t" beside "2.0 t"). The rule this module
mechanizes: every value of one quantity kind, everywhere it prints,
goes through ONE formatter object carrying that kind's whole precision
policy — never an inline format string. A host repo declares its kinds
once in a thin shim (practice: engine-plus-host-shims) and imports them in every emitter.

Policy guidance (the practice text carries the reasoning):
- pick decimals from the estimate's own noise — tenths a model cannot
  resolve are false precision;
- when a kind uses an integer threshold (`int_at`), check that no
  threshold straddles a COMPARISON PAIR: two values a reader compares
  side by side must format under the same branch of the policy.

The formatter↔renderer seam (this practice ↔ the sortable-render
practice): whatever this module
prints, the table renderer (tools/doc_html.py) must parse back to the
same value for sorting, frontier ranking, and decimal alignment.
`parse_key()` below is the Python mirror of the renderer's `keyOf`
grammar — the two are kept in lockstep, so extend BOTH when a notation
is added — and `roundtrip_check()` formats sample values through every
registered kind and asserts the parse recovers the printed value, plus
pins the grammar itself against canned notation samples. Host shims
expose it as `self_check()` so the repo's audit runner gates on it: a
new prefix, suffix, or magnitude notation that the renderer would
mis-sort fails loudly at commit time, not silently in the browser.
"""


import math
import re
import unicodedata


class Qty:
    """Formatter for one quantity kind.

    decimals   places printed below `int_at` (and everywhere when
               `int_at` is None)
    int_at     at/above this magnitude print thousands-separated
               integers instead (None: never)
    sig        significant figures (overrides `decimals`/`int_at`):
               the right policy for a kind whose values span orders of
               magnitude -- fixed decimal places would give a large
               value four significant digits and a small one two.
               Decimal count then varies with magnitude by design;
               integers keep thousands separators.
    approx     prepend '≈' (most model outputs are estimates)
    prefix     between the '≈' and the number (e.g. '$')
    suffix     after the number (e.g. ' t', ' mph')
    """

    def __init__(self, decimals=0, int_at=None, sig=None, approx=True,
                 prefix="", suffix=""):
        self.decimals = decimals
        self.int_at = int_at
        self.sig = sig
        self.approx = approx
        self.prefix = prefix
        self.suffix = suffix

    def __call__(self, v):
        if self.sig is not None and v != 0:
            d = max(0, self.sig - 1 - math.floor(math.log10(abs(v))))
        else:
            d = 0 if (self.int_at is not None
                      and abs(v) >= self.int_at) else self.decimals
        return (("≈" if self.approx else "")
                + self.prefix + f"{v:,.{d}f}" + self.suffix)


# ------------------- the formatter↔renderer seam contract ------------------
def _currency_magnitude(t, tail):
    """True when a digit run ending in `tail` (k or M) is preceded, over
    optional whitespace, by a Unicode currency symbol — the renderer
    treats k/M as magnitude ONLY on currency amounts (a bare "58 M" is a
    unit, not money). Mirrors keyOf's /\\p{Sc}\\s*[\\d.,]+k|M/u."""
    # A trailing boundary keeps "$5km" (kilometers) or "$5Mbps" from being
    # read as the k/M currency-magnitude suffix just because the digit run
    # happens to be followed by the right letter -- the suffix must END the
    # token, not merely start it.
    for m in re.finditer(r"[\d.,]+" + tail + r"(?![A-Za-z0-9])", t):
        i = m.start() - 1
        while i >= 0 and t[i].isspace():
            i -= 1
        if i >= 0 and unicodedata.category(t[i]) == "Sc":
            return True
    return False


def parse_key(text):
    """The numeric value the table renderer's sort/rank/align key
    recovers from a cell — the Python mirror of `keyOf` in
    tools/doc_html.py, kept in LOCKSTEP with it (extend both together).
    Returns None for the empty/em-dash cell and for text with no
    number."""
    t = text.strip()
    if t in ("—", ""):
        return None
    kmatch = _currency_magnitude(t, "k")
    mmatch = _currency_magnitude(t, r"\s*M")
    m = re.search(r"-?(?:\d+(?:\.\d+)?|\.\d+)", re.sub(r"[,≈≤≥]", "", t))
    if not m:
        return None
    v = float(m.group(0))
    if kmatch:
        v *= 1000
    if mmatch:
        v *= 1000000
    return v


# Canned notation pins: forms the renderer's grammar must keep parsing
# to these values. The unit-vs-money "M" case and the bare decimal are
# the ones history shows drift silently.
GRAMMAR_SAMPLES = [
    ("≈$1751k", 1_751_000.0),
    ("€14.8M", 14_800_000.0),
    ("~$.45", 0.45),
    ("~$0.45", 0.45),
    ("007", 7.0),
    (".59", 0.59),
    ("≈1,269 mi @15.4 t", 1269.0),
    ("≈58 MJ", 58.0),          # unit, not money: NO ×1e6
    ("$3.20 base", 3.2),
    ("2E", 2.0),
    ("—", None),
]


def roundtrip_check(kinds, samples=(0.0, 0.03, 0.45, 2.0, 14.8, 97.8,
                                    1234.5, -3.5, 1_751_000.0)):
    """Format each sample through every registered kind and assert the
    renderer-grammar parse recovers the PRINTED value (derived from the
    kind's own declared affixes, so the expectation is independent of
    the parser); then check the grammar pins. Returns a list of failure
    strings — empty means the seam holds. Host shims expose this as
    self_check() over their kind registry."""
    fails = []
    for name, qty in kinds.items():
        for v in samples:
            s = qty(v)
            core = s[1:] if s.startswith("≈") else s
            if qty.prefix and core.startswith(qty.prefix):
                core = core[len(qty.prefix):]
            if qty.suffix and core.endswith(qty.suffix):
                core = core[:len(core) - len(qty.suffix)]
            try:
                expected = float(core.replace(",", ""))
            except ValueError:
                fails.append(f"{name}({v!r}) -> {s!r}: printed core "
                             f"{core!r} is not numeric")
                continue
            got = parse_key(s)
            if got is None or abs(got - expected) > 1e-9 * max(1.0, abs(expected)):
                fails.append(f"{name}({v!r}) -> {s!r}: renderer grammar "
                             f"parses {got!r}, printed value is {expected!r}")
    for text, want in GRAMMAR_SAMPLES:
        got = parse_key(text)
        ok = (got is None and want is None) or (
            got is not None and want is not None
            and abs(got - want) <= 1e-9 * max(1.0, abs(want)))
        if not ok:
            fails.append(f"grammar pin {text!r}: parsed {got!r}, want {want!r}")
    return fails
