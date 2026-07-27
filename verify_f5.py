"""verify_f5: reproducible accuracy evidence for compute_f5.

SOEN 6011, Summer 2026, Deliverable 2. Student ID: 40324569.

Compares compute_f5 against Python's built-in ** as a reference oracle
across the real domain. The from-scratch rule applies to the
implementation, not to the test oracle: using ** here only to CHECK the
result is standard practice and keeps the evidence honest.

Run:  python3 verify_f5.py
"""

from f5_core import compute_f5
from f5_errors import DomainError, RangeError

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
    (1, 10, 400, RangeError),    # NFR-02 overflow
    (1, 10, -400, RangeError),   # NFR-02 underflow
]


def main():
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
    print("requirement NFR-01 (>= 6 significant digits) satisfied:",
          worst < 1e-6)

    print()
    print("rejected-input cases")
    print("-" * 78)
    failures = 0
    for a, b, x, expected in REJECT_CASES:
        try:
            got = compute_f5(a, b, x)
            print("  a=%-5g b=%-7g x=%-6g | NOT REJECTED, returned %r"
                  % (a, b, x, got))
            failures += 1
        except expected as error:
            print("  a=%-5g b=%-7g x=%-6g | %s: %s"
                  % (a, b, x, type(error).__name__, error.cause))
    print("-" * 78)
    print("all rejection cases behaved as required:", failures == 0)


if __name__ == "__main__":
    main()
