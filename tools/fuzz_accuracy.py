"""fuzz_accuracy: sample the input space of F5 against a precise oracle.

SOEN 6011, Summer 2026, Deliverable 3. Student ID: 40324569.

WHY THIS EXISTS
---------------
The D2 submission stated a worst relative error of 5.2e-11 over 120,000
sampled inputs. The D2 evaluation observed that the ten cases published
in verify_f5.py do not reproduce that figure, and that the sampling did
not cover every numerically difficult combination of scales.

This script settles the question by measurement rather than argument. It
draws inputs log-uniformly across the full representable range of double
precision, which concentrates samples where the two scales oppose each
other -- the region the D2 sampling under-covered.

STATUS UNDER DC-03
------------------
This is an instrument, not calculator code. It uses the decimal module
and the built-in power operator as oracles, exactly as verify_f5.py
already does. Neither f5_core nor f5_gui imports it, so the from-scratch
constraint on the calculator is unaffected.

USAGE
-----
Run from the repository root, not from inside tools/:

    python3 tools/fuzz_accuracy.py
"""

import random
import sys
from decimal import Decimal, getcontext

# The calculator modules live in the repository root, one level up from
# this tools/ directory, so the root is placed on the search path before
# they are imported. The two suppressions below are the standard way to
# tell each checker that this ordering is deliberate, not an oversight.
sys.path.insert(0, ".")

# pylint: disable=wrong-import-position
from f5_core import compute_f5                        # noqa: E402
from f5_errors import AlgorithmRangeError, F5Error    # noqa: E402

# Sixty significant digits: far beyond double precision, so the oracle
# contributes no measurable error of its own.
getcontext().prec = 60

# Fixed seed. The same inputs are drawn on every run, so a figure quoted
# on the poster can be reproduced on demand by the evaluator.
SEED = 7
SAMPLES = 200000

# Decade limits for the log-uniform draw.
EXP_LIMIT = 300
X_LIMIT = 400.0

# IEEE-754 double boundaries. Results outside the normal range are not
# judged: NFR-01 excludes subnormal results by its own stated scope.
MIN_NORMAL = 2.2250738585072014e-308

# The claim printed in the D2 appendix, for comparison.
D2_CLAIM = 5.2e-11


def oracle(a, b, x):
    """Return a * b**x to 60 digits, or None if outside the real domain.

    The sign is handled separately so that a negative base with a whole
    exponent is evaluated on |b| and signed afterwards, which mirrors
    the mathematics rather than the algorithm under test.
    """
    if b == 0.0:
        return None
    whole = x // 1.0
    if b < 0.0 and x != whole:
        return None
    value = Decimal(abs(b)) ** Decimal(x)
    value = Decimal(a) * value
    if b < 0.0 and whole % 2.0 != 0.0:
        value = -value
    return value


def draw(rng):
    """Return one (a, b, x) drawn log-uniformly over the double range.

    Drawing the EXPONENT uniformly rather than the value itself is what
    reaches the opposing-scale region. A uniform draw over the values
    would place almost every sample near the top decade and would
    reproduce the D2 blind spot.
    """
    a = rng.uniform(1.0, 10.0) * 10.0 ** rng.randint(-EXP_LIMIT, EXP_LIMIT)
    b = rng.uniform(1.0, 10.0) * 10.0 ** rng.randint(-EXP_LIMIT, EXP_LIMIT)
    a *= rng.choice((1.0, -1.0))
    b *= rng.choice((1.0, -1.0))
    if rng.random() < 0.5:
        x = float(rng.randint(int(-X_LIMIT), int(X_LIMIT)))
    else:
        x = rng.uniform(-X_LIMIT, X_LIMIT)
    return a, b, x


def judgeable(reference):
    """True when the exact result is a normal double worth comparing."""
    try:
        as_float = float(reference)
    except (OverflowError, ValueError):
        return False
    # as_float != as_float is true only for NaN. Written this way because
    # the calculator itself may not use math.isnan; pylint's R0124 does
    # not know the idiom, so it is suppressed here deliberately.
    if as_float != as_float or as_float in (  # pylint: disable=R0124
            float("inf"), float("-inf")):
        return False
    if as_float == 0.0:
        return False
    return abs(as_float) >= MIN_NORMAL


def run():
    """Sample, compare, and report the worst relative error found."""
    rng = random.Random(SEED)
    judged = 0
    refused = 0
    worst = 0.0
    worst_case = None

    for _ in range(SAMPLES):
        a, b, x = draw(rng)
        reference = oracle(a, b, x)
        if reference is None or not judgeable(reference):
            continue
        try:
            produced = compute_f5(a, b, x)
        except AlgorithmRangeError:
            refused += 1
            continue
        except F5Error:
            refused += 1
            continue
        judged += 1
        error = abs((Decimal(produced) - reference) / reference)
        if error > worst:
            worst = error
            worst_case = (a, b, x, produced, float(reference))

    report(judged, refused, worst, worst_case)


def report(judged, refused, worst, worst_case):
    """Print a summary compact enough to screenshot legibly."""
    print()
    print("F5 accuracy sampling -- D3 baseline")
    print("oracle: decimal, 60 significant digits;  seed:", SEED)
    print("draw:   log-uniform, |a| and |b| over 1e-300 .. 1e300")
    print("judged: normal-range results only (NFR-01 scope)")
    print()
    print(f"  samples drawn        {SAMPLES:>10}")
    print(f"  samples judged       {judged:>10}")
    print(f"  refused under DC-04  {refused:>10}")
    print()
    print(f"  worst relative error {float(worst):>10.2e}")
    print(f"  D2 documented claim  {D2_CLAIM:>10.2e}")
    print(f"  ratio                {float(worst) / D2_CLAIM:>9.1f}x")
    print()
    if worst_case is not None:
        print("  worst case:")
        print(f"    a = {worst_case[0]!r}")
        print(f"    b = {worst_case[1]!r}")
        print(f"    x = {worst_case[2]!r}")
    print()


if __name__ == "__main__":
    run()
