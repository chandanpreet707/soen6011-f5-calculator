"""f5_core: the F5 function f(x) = a * b**x on the real domain.

SOEN 6011, Summer 2026, Deliverable 2, Problem 5. Student ID: 40324569.

Implements Algorithm B (integer-fraction splitting) selected in
D1/Problem 4, using only the from-scratch subordinate functions in
f5_math and raising only the custom exceptions in f5_errors.

Algorithm B, for the fractional exponent case:
    x = n + f,  n = floor(x),  f in [0, 1)
    b**x = b**n * b**f = pow_int(b, n) * exp(f * ln(b))
The integer part is computed exactly; the series runs only on the small
fractional part, where it converges quickly.
"""

from f5_math import absolute, floor_int, pow_int, ln, exp
from f5_errors import DomainError, RangeError


def compute_f5(a, b, x):
    """Return a * b**x on the real domain.

    Domain rules (traceable to the D1 requirements):
      FR-02  b > 0            general case, any real x
      FR-03  b = 0, x <= 0    rejected (0**0 and 0**negative undefined)
      FR-04  b < 0, x not int rejected (no real value)
      FR-05  b < 0, x integer computed with sign tracking
    """
    # FR-03: zero base.
    if b == 0.0:
        if x > 0:
            return 0.0
        raise DomainError(
            "Zero raised to a non-positive exponent is undefined.",
            "choose x > 0 when b = 0.")

    # FR-04: negative base with a non-integer exponent has no real value.
    if b < 0.0 and x != floor_int(x):
        raise DomainError(
            "A negative base with a non-integer exponent has no real value.",
            "use an integer x when b < 0.")

    # Split the exponent: x = n + f, with n whole and f in [0, 1).
    n = floor_int(x)
    f = x - n

    # Integer part, computed exactly on the magnitude of b.
    p = pow_int(absolute(b), absolute(n))
    if n < 0:
        if p == 0.0:
            raise RangeError(
                "The result is too large to represent (overflow).",
                "reduce the magnitude of x or b.")
        p = 1.0 / p

    # FR-05: restore the sign for a negative base with an odd exponent.
    if b < 0.0 and n % 2 != 0:
        p = -p

    # Fractional part, via the series, only when there is one.
    if f > 0.0:
        q = exp(f * ln(absolute(b)))
    else:
        q = 1.0

    return a * p * q