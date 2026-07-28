"""verify_f5: reproducible accuracy evidence for compute_f5.

SOEN 6011, Summer 2026, Deliverable 2. Student ID: 40324569.

Compares compute_f5 against reference oracles across the real domain.
The from-scratch rule (DC-03) applies to the implementation, not to the
test oracle: using Python's ** and the decimal module HERE, only to
CHECK a result, is standard practice and keeps the evidence honest.

Four sections, one per kind of claim:
  1. accuracy      NFR-01, against the built-in ** operator
  2. rejection     FR-03, FR-04, NFR-02: inputs that must be refused
  3. range safety  results that are representable only when the factors
                   are combined in the right order
  4. convergence   NFR-04, forced by lowering the iteration limit

Run:  python3 verify_f5.py
"""

from decimal import Decimal, getcontext

from f5_core import compute_f5
from f5_errors import ConvergenceError, DomainError, RangeError
from f5_math import ln

getcontext().prec = 60

CASES = [
    (2, 3, 2.5),
    (100, 1.4, 3.5),
    (1, 2, 10),
    (5, 10, 0.5),
    (1, 0.5, 3.5),
    (2, 7, 3.25),
    (1, 1e15, 0.9),
    (1, -2, 3),
    (3, -2, 4),
    (1, -2, 0),
]

# Inputs that must be REJECTED, and the class that must reject them.
# Evidence for FR-03, FR-04 and NFR-02: a requirement that is never
# exercised is not evidence of anything.
REJECT_CASES = [
    (1, 0, 0, DomainError),      # FR-03  zero base, non-positive exponent
    (1, 0, -1, DomainError),     # FR-03
    (1, -2, 0.5, DomainError),   # FR-04  negative base, fractional exponent
    (0, -2, 0.5, DomainError),   # FR-04  must hold when a = 0 as well
    (1, 10, 400, RangeError),    # NFR-02 overflow
    (1, 10, -400, RangeError),   # NFR-02 underflow
]

# Results that are representable, but only if a and the integer power are
# combined in an order that never leaves the range on the way. Every one
# of these was reported as overflow or underflow before the balanced
# product was introduced. The expected value is computed exactly, because
# the built-in ** cannot compute some of them at all.
SCALE_CASES = [
    (1e-300, 1e300, 2),       # a compensates a b**n that overflows alone
    (1e300, 1e-100, 6),       # a compensates a b**n that underflows alone
    (1, 10, -320),            # reciprocal of an overflowing integer power
    (1e-300, 0.5, -2000),     # decay base with a large negative exponent
]


def exact(a, b, x):
    """Exact reference for a whole exponent, to 60 significant digits."""
    return Decimal(a) * (Decimal(b) ** int(x))


def relative_error(ours, reference):
    """Relative error of a result against a Decimal reference."""
    return abs(Decimal(ours) - reference) / abs(reference)


def accuracy_section():
    """NFR-01: at least six significant digits."""
    print("1. ACCURACY (NFR-01)")
    print("a      b        x      | ours              | reference         | rel err")
    print("-" * 78)
    worst = 0.0
    for a, b, x in CASES:
        ours = compute_f5(a, b, x)
        ref = a * (b ** x)
        err = abs(ours - ref) / abs(ref) if ref else abs(ours - ref)
        worst = max(worst, err)
        print("%-6g %-8g %-6g | %-17.10g | %-17.10g | %.1e"
              % (a, b, x, ours, ref, err))
    print("-" * 78)
    print("worst relative error over %d cases: %.1e" % (len(CASES), worst))
    print("NFR-01 (>= 6 significant digits) satisfied:", worst < 1e-6)
    return worst < 1e-6


def rejection_section():
    """FR-03, FR-04, NFR-02: inputs that must be refused."""
    print()
    print("2. REJECTED INPUTS (FR-03, FR-04, NFR-02)")
    print("-" * 78)
    failures = 0
    for a, b, x, expected in REJECT_CASES:
        try:
            got = compute_f5(a, b, x)
            print("  a=%-8g b=%-7g x=%-6g | NOT REJECTED, returned %r"
                  % (a, b, x, got))
            failures += 1
        except expected as error:
            print("  a=%-8g b=%-7g x=%-6g | %s: %s"
                  % (a, b, x, type(error).__name__, error.cause))
    print("-" * 78)
    print("all rejection cases behaved as required:", failures == 0)
    return failures == 0


def scale_section():
    """Results reachable only through a range-safe order of multiplication."""
    print()
    print("3. RANGE SAFETY (NFR-02, compensated scales)")
    print("-" * 78)
    worst = Decimal(0)
    failures = 0
    for a, b, x in SCALE_CASES:
        reference = exact(a, b, x)
        try:
            ours = compute_f5(a, b, x)
        except RangeError as error:
            print("  a=%-8g b=%-8g x=%-6g | REJECTED (%s) but %.6g is representable"
                  % (a, b, x, error.cause, reference))
            failures += 1
            continue
        err = relative_error(ours, reference)
        if err > worst:
            worst = err
        print("  a=%-8g b=%-8g x=%-6g | ours %-14.8g | exact %-14.8g | rel err %.1e"
              % (a, b, x, ours, reference, err))
    print("-" * 78)
    print("all compensated-scale cases computed: %s (worst rel err %.1e)"
          % (failures == 0, worst))
    print("  note: a=1, b=10, x=-320 has a SUBNORMAL result, a range in which")
    print("  the double format itself holds fewer than six significant digits.")
    print("  NFR-01 is scoped to the normal range for this reason.")

    # A case where this implementation is MORE accurate than the built-in
    # operator, because ** passes through a subnormal intermediate value
    # and the balanced product does not.
    a, b, x = 6.737065165365105e248, -6.730304257494641, -390
    reference = exact(a, b, x)
    ours = compute_f5(a, b, x)
    builtin = a * (b ** x)
    print()
    print("  a=%g, b=%g, x=%g" % (a, b, x))
    print("    exact       %.10g" % reference)
    print("    ours        %-22.10g rel err %.1e"
          % (ours, relative_error(ours, reference)))
    print("    built-in ** %-22.10g rel err %.1e"
          % (builtin, relative_error(builtin, reference)))
    return failures == 0


def convergence_section():
    """NFR-04: a series that runs out of iterations reports, not crashes."""
    print()
    print("4. CONVERGENCE (NFR-04)")
    print("-" * 78)
    print("  After range reduction ln needs about 30 terms and exp about")
    print("  1700, against a cap of 10000, so no admissible input reaches")
    print("  the cap. It is exercised here by lowering the limit.")
    try:
        ln(1.9, max_iter=3)
        print("  ln(1.9, max_iter=3) | NO ERROR RAISED")
        return False
    except ConvergenceError as error:
        print("  ln(1.9, max_iter=3) | ConvergenceError: %s" % error.cause)
        print("                      | corrective action: %s" % error.action)
    print("-" * 78)
    print("NFR-04 exercised and reported without terminating: True")
    return True


def main():
    results = [accuracy_section(), rejection_section(),
               scale_section(), convergence_section()]
    print()
    print("=" * 78)
    print("ALL SECTIONS PASSED:", all(results))


if __name__ == "__main__":
    main()
