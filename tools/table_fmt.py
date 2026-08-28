#!/usr/bin/env python3
"""One formatter per quantity kind (practice 51) — the engine.

A reader comparing two table cells must never have to normalize
precision in their head ("2 t" beside "2.0 t"). The rule this module
mechanizes: every value of one quantity kind, everywhere it prints,
goes through ONE formatter object carrying that kind's whole precision
policy — never an inline format string. A host repo declares its kinds
once in a thin shim (practice 50) and imports them in every emitter.

Policy guidance (the practice text carries the reasoning):
- pick decimals from the estimate's own noise — tenths a model cannot
  resolve are false precision;
- when a kind uses an integer threshold (`int_at`), check that no
  threshold straddles a COMPARISON PAIR: two values a reader compares
  side by side must format under the same branch of the policy.
"""


import math


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
