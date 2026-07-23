"""verify_f5: reproducible accuracy evidence for compute_f5.

SOEN 6011, Summer 2026, Deliverable 2. Student ID: 40324569.

Compares compute_f5 against Python's built-in ** as a reference oracle
across the real domain. The from-scratch rule applies to the
implementation, not to the test oracle: using ** here only to CHECK the
result is standard practice and keeps the evidence honest.

Run:  python3 verify_f5.py
"""

from f5_core import compute_f5
from f5_errors import F5Error

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


if __name__ == "__main__":
    main()