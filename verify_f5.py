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
                   are combined in the right order, and the boundary
                   beyond which the algorithm reports instead of guessing
  4. convergence   NFR-04, forced by lowering the iteration limit

Run:  python3 verify_f5.py
"""

from decimal import Decimal, getcontext

from f5_core import compute_f5
from f5_errors import (AlgorithmRangeError, ConvergenceError,
                       DomainError, RangeError)
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


# The boundary of DC-04. In each of these the exact result IS
# representable, but Algorithm B would have to form an intermediate factor
# that is not, so NFR-05 requires the calculator to say so rather than
# claim the result is out of range. The last two are genuine range
# failures and must still be reported as such.
BOUNDARY_CASES = [
    (2.132253711254229e-238, 8.645627300825678e-110, -4.624952379652598,
     AlgorithmRangeError),
    (4.432680122329864e-148, 3.510001819757236e-159, -2.1167520077523676,
     AlgorithmRangeError),
    (1, 10, 400, RangeError),
    (1, 0.5, 4000, RangeError),
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
    print("a      b        x      | ours              "
          "| reference         | rel err")
    print("-" * 78)
    worst = 0.0
    for a, b, x in CASES:
        ours = compute_f5(a, b, x)
        ref = a * (b ** x)
        err = abs(ours - ref) / abs(ref) if ref else abs(ours - ref)
        worst = max(worst, err)
        print(f"{a:<6g} {b:<8g} {x:<6g} | {ours:<17.10g} "
              f"| {ref:<17.10g} | {err:.1e}")
    print("-" * 78)
    print(f"worst relative error over {len(CASES)} cases: {worst:.1e}")
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
            print(f"  a={a:<8g} b={b:<7g} x={x:<6g} | "
                  f"NOT REJECTED, returned {got!r}")
            failures += 1
        except expected as error:
            print(f"  a={a:<8g} b={b:<7g} x={x:<6g} | "
                  f"{type(error).__name__}: {error.cause}")
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
            print(f"  a={a:<8g} b={b:<8g} x={x:<6g} | "
                  f"REJECTED ({error.cause}) but "
                  f"{float(reference):.6g} is representable")
            failures += 1
            continue
        err = relative_error(ours, reference)
        worst = max(worst, err)
        print(f"  a={a:<8g} b={b:<8g} x={x:<6g} | ours {ours:<14.8g} "
              f"| exact {float(reference):<14.8g} "
              f"| rel err {float(err):.1e}")
    print("-" * 78)
    print(f"all compensated-scale cases computed: {failures == 0} "
          f"(worst rel err {float(worst):.1e})")
    print("  note: a=1, b=10, x=-320 has a SUBNORMAL result. NFR-01 is scoped")
    print("  to the normal range because a uniform six-significant-digit"
          " bound")
    print("  is not guaranteed throughout the subnormal range. Precision"
          " there")
    print("  degrades gradually: values near the normal boundary still carry")
    print("  well over six digits, values near zero carry almost none.")

    # A case where this implementation is MORE accurate than the
    # expression a * b**x. The built-in operator is correctly rounded;
    # the loss happens because b**x alone is subnormal, so the digits are
    # gone before a is applied. The balanced product never forms that
    # intermediate.
    a, b, x = 6.737065165365105e248, -6.730304257494641, -390
    reference = exact(a, b, x)
    ours = compute_f5(a, b, x)
    builtin = a * (b ** x)
    print()
    print(f"  a={a:g}, b={b:g}, x={x:g}")
    print(f"    exact       {float(reference):.10g}")
    print(f"    ours        {ours:<22.10g} "
          f"rel err {float(relative_error(ours, reference)):.1e}")
    print(f"    built-in ** {builtin:<22.10g} "
          f"rel err {float(relative_error(builtin, reference)):.1e}")
    # DC-04 and NFR-05: the algorithm boundary must be distinguished from
    # a genuine range failure, not merged into it.
    print()
    print("  algorithm boundary (DC-04, NFR-05)")
    boundary_failures = 0
    for a, b, x, expected in BOUNDARY_CASES:
        try:
            got = compute_f5(a, b, x)
            print(f"    a={a:<9g} b={b:<9g} x={x:<8g} | "
                  f"NOT REPORTED, returned {got!r}")
            boundary_failures += 1
        except expected as error:
            print(f"    a={a:<9g} b={b:<9g} x={x:<8g} | "
                  f"{type(error).__name__}")
        # pylint: disable=duplicate-except
        # False positive. `expected` above is bound per iteration to ONE
        # class from BOUNDARY_CASES, so this clause catches the OTHER
        # range class and reports a wrong classification. Pylint cannot
        # resolve a dynamic exception class, so it assumes an overlap
        # that never occurs at run time.
        except (RangeError, AlgorithmRangeError) as error:
            print(f"    a={a:<9g} b={b:<9g} x={x:<8g} | WRONG CLASS: "
                  f"{type(error).__name__}, expected {expected.__name__}")
            boundary_failures += 1
    print("  each condition reported under the correct class:",
          boundary_failures == 0)
    return failures == 0 and boundary_failures == 0


def convergence_section():
    """NFR-04: a series that runs out of iterations reports, not crashes."""
    print()
    print("4. CONVERGENCE (NFR-04)")
    print("-" * 78)
    print("  After range reduction ln needs about 16 terms and exp about")
    print("  1900, against a cap of 10000, so no admissible input reaches")
    print("  the cap. It is exercised here by lowering the limit.")
    try:
        ln(1.9, max_iter=3)
        print("  ln(1.9, max_iter=3) | NO ERROR RAISED")
        return False
    except ConvergenceError as error:
        print(f"  ln(1.9, max_iter=3) | ConvergenceError: {error.cause}")
        print(f"                      | corrective action: {error.action}")
    print("-" * 78)
    print("NFR-04 exercised and reported without terminating: True")
    return True


def main():
    """Run the four sections and report whether all of them passed."""
    results = [accuracy_section(), rejection_section(),
               scale_section(), convergence_section()]
    print()
    print("=" * 78)
    print("ALL SECTIONS PASSED:", all(results))


if __name__ == "__main__":
    main()
