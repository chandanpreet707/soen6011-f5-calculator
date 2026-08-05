"""defect_probe: expose the D2 accuracy defect under the debugger.

SOEN 6011, Summer 2026, Deliverable 3. Student ID: 40324569.

WHY THIS EXISTS
---------------
fuzz_accuracy.py shows THAT the D2 accuracy claim was overstated. This
script shows WHY, at the one line where it happens, so that the cause
can be observed in pdb rather than inferred.

THE DEFECT
----------
f5_math.EPSILON is 1e-12, and it is applied as an ABSOLUTE tolerance on
the series terms. The module constant _LN2 therefore carries roughly
1e-12 of absolute error.

Range reduction computes ln(b) = ln(m) + p * _LN2, where p counts the
halvings needed to bring b into [1, 2). For an extreme base p reaches
into the hundreds, multiplying that 1e-12 into about 1e-9 of absolute
error in ln(b).

exp() then turns an absolute error in its argument into a relative
error in its result, so the 1e-9 arrives in the answer intact. The
tolerance, not the floating-point format, is the limiting factor.

STATUS UNDER DC-03
------------------
An instrument, never imported by f5_core or f5_gui. LN2_REFERENCE is an
oracle used only for the diagnostic subtraction below; the calculator
still computes ln(2) from its own series.

USAGE
-----
Run from the repository root:

    python3 -m pdb tools/defect_probe.py

Then type these, one per (Pdb) prompt:

    c
    b f5_math.py:126
    c
    print(b)
    print(p)
    print(_LN2)
    print(0.6931471805599453 - _LN2)
    print(p * (0.6931471805599453 - _LN2))
    q

The first c runs as far as the staged breakpoint, which is placed after
the import so that pdb can resolve f5_math.py. The last two lines are
the defect: the error in _LN2, then that error multiplied by p.
"""

import sys

# The calculator modules live in the repository root, one level up from
# this tools/ directory. The suppressions mark the ordering deliberate.
sys.path.insert(0, ".")

# pylint: disable=wrong-import-position
import f5_math    # noqa: E402

# The base from the worst case reported by fuzz_accuracy.py. Its
# magnitude is what drives the range-reduction exponent p upward.
B = 1.5759100997500323e+281

# NOTE: inside the ln() frame only f5_math's own names are visible, so
# the pdb commands above spell out 0.6931471805599453, which is ln(2) to
# full double precision. It is an oracle for the diagnostic subtraction
# only; the calculator still computes ln(2) from its own series.

# Staged breakpoint. Execution stops here, AFTER f5_math is imported and
# after the path change above, which is what lets the next pdb command
# resolve "f5_math.py" to a real file.
# pylint: disable=forgotten-debug-statement
# The call is the point of this script, not a leftover: it is what
# stages the debugging session described in the docstring above.
breakpoint()

VALUE = f5_math.ln(B)

print()
print("B                          :", repr(B))
print("ln(B) computed by f5_math  :", repr(VALUE))
print()
