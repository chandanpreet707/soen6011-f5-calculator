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
from f5_errors import AlgorithmRangeError, DomainError, RangeError

# The overflow sentinel, formed by arithmetic rather than by float("inf").
# float() is a built-in type conversion; DC-03 permits only input, output,
# arithmetic and interface functions, and multiplying two finite numbers
# past the representable range yields the infinity we need.
# Semantic Versioning (https://semver.org). MAJOR is
# incremented for each deliverable because each has changed
# the public behaviour of the calculator in an incompatible
# way: D2 replaced the interface, D3 changed which faults
# are caught and the values returned for extreme bases.
__version__ = "3.0.0"

_INF = 1e308 * 10.0

# The two ends of the representable range. These are properties of the
# IEEE-754 double format, not values from a mathematical table, and the
# logarithms of them are computed by the from-scratch ln at import.
_MAX_DOUBLE = 1.7976931348623157e308     # largest finite double
_MIN_NORMAL = 2.2250738585072014e-308    # smallest normal double


def _unusable(v):
    """True when a factor has left the representable range."""
    # v != v is true only for NaN. math.isnan would say so more plainly
    # but is a library function, and DC-03 permits only input, output,
    # arithmetic and interface functions. Pylint does not know the
    # idiom, so the check is suppressed rather than the code changed.
    # pylint: disable=comparison-with-itself
    return v != v or v == _INF or v == -_INF or v == 0.0


def _report_range_failure(a, b, x):
    """Raise the error that correctly describes why no value can be formed.

    A factor of the product has left the representable range, but that
    does not by itself say the ANSWER is out of range. The scale of the
    exact answer is ln|a| + x*ln|b|, which can be formed even when the
    factors cannot, so it decides which of two different failures this is:

      NFR-02  the exact result is outside the representable range
              -> RangeError, overflow or underflow
      NFR-05  the exact result is representable, but Algorithm B would
              have to form an intermediate value that is not
              -> AlgorithmRangeError

    Reporting the second as the first would tell the user that a
    representable result cannot be represented, which is untrue.
    """
    scale = ln(absolute(a)) + x * ln(absolute(b))
    if scale > _LN_MAX:
        raise RangeError(
            "The result is too large to represent (overflow).",
            "reduce the magnitude of a, b, or x.")
    if scale < _LN_MIN_NORMAL:
        raise RangeError(
            "The result is too small to represent (underflow).",
            "increase the magnitude of a, b, or x.")
    raise AlgorithmRangeError(
        "The exact result is representable, but this input requires an "
        "intermediate value outside the supported computational range.",
        "reduce the magnitude of the base or the exponent.")


_FACTOR_COUNT = 4


def _balanced_product(f0, f1, f2, f3):
    """Multiply four factors in an order that keeps the product near 1.

    Multiplication is associative in mathematics but not in floating
    point: a product whose value is representable can still be reached
    through an intermediate value that is not. With a = 1e-300,
    b = 1e300 and x = 2 the answer 1e300 is an ordinary double, yet
    computing b**2 first gives 1e600, which overflows, and multiplying
    by a afterwards cannot recover it. Reaching an extreme and coming
    back also costs accuracy: an intermediate value in the subnormal
    range keeps only two or three significant digits. On
    a = 6.7e248, b = -6.73, x = -390 the answer is an ordinary
    7.85e-75, but b**x alone is 1.17e-323, barely two steps above the
    smallest double, so the expression a * b**x loses fifteen percent
    before a is applied. The built-in operator is not at fault: it
    returns the correctly rounded value of what it was asked. This
    ordering never forms that intermediate.

    The rule below avoids both. While the running product is above 1,
    multiply by the smallest factor left; while it is at or below 1,
    multiply by the largest. Opposing factors then cancel as they are
    applied, and the running product stays as close to 1 as the four
    factors allow.
    """
    factors = [f0, f1, f2, f3]
    used = [False, False, False, False]
    result = 1.0
    step = 0
    while step < _FACTOR_COUNT:
        want_smallest = absolute(result) > 1.0
        best = -1
        i = 0
        while i < _FACTOR_COUNT:
            if not used[i]:
                if best < 0:
                    best = i
                elif want_smallest:
                    if absolute(factors[i]) < absolute(factors[best]):
                        best = i
                elif absolute(factors[i]) > absolute(factors[best]):
                    best = i
            i += 1
        result = result * factors[best]
        used[best] = True
        step += 1
    return result


def compute_f5(a, b, x):
    """Return a * b**x on the real domain.

    Domain rules (traceable to the D1 requirements):
      FR-02  b > 0            general case, any real x
      FR-03  b = 0, x <= 0    rejected (0**0 and 0**negative undefined)
      FR-04  b < 0, x not int rejected (no real value)
      FR-05  b < 0, x integer computed with sign tracking

    NFR-01: accurate to at least six significant digits for results
    inside the normal representable range.

    NFR-02: a result outside the representable range is reported as a
    RangeError rather than returned as inf or silently flushed to zero.
    """
    # FR-03: zero base. Checked first because the sign and domain rules
    # below all assume a non-zero base.
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

    # A zero multiplier makes the result zero whatever b and x are, and
    # returning here avoids forming 0 * inf (which is NaN) further down.
    # This test sits BELOW the two domain rules on purpose: an input that
    # FR-03 or FR-04 rejects must be rejected whatever the value of a, so
    # a = 0 must not become a shortcut past the domain of the function.
    if a == 0.0:
        return 0.0

    # Split the exponent: x = n + f, with n whole and f in [0, 1).
    n = floor_int(x)
    f = x - n

    # Integer part, computed exactly on the magnitude of b, but in two
    # halves so that a can be folded in between them.
    #
    # Computing the whole of |b|**n first, and only then multiplying by a,
    # can leave the representable range on the way to a result that is
    # inside it: a = 1e-300, b = 1e300, x = 2 has the representable answer
    # 1e300, yet |b|**2 = 1e600 overflows before a is ever applied.
    #
    # Each half carries at most half the exponent, and a is itself a finite
    # double, so it can compensate at most about 308 decades. Any product
    # a * b**n that is representable therefore has both halves and both
    # partial products representable too.
    magnitude = absolute(n)
    half = floor_int(magnitude / 2.0)
    p1 = pow_int(absolute(b), half)
    p2 = pow_int(absolute(b), magnitude - half)
    if n < 0:
        p1 = _INF if p1 == 0.0 else 1.0 / p1
        p2 = _INF if p2 == 0.0 else 1.0 / p2

    # DC-04: a half of the integer power has left the representable range,
    # so Algorithm B cannot form this product however the factors are
    # ordered. Which failure that is depends on the exact answer, not on
    # the factor, so the decision is delegated.
    if _unusable(p1) or _unusable(p2):
        _report_range_failure(a, b, x)

    # Fractional part, via the series, only when there is one.
    if f > 0.0:
        q = exp(f * ln(absolute(b)))
    else:
        q = 1.0

    # The answer is the product a * p1 * p2 * q, but the ORDER matters:
    # see _balanced_product.
    result = _balanced_product(a, p1, p2, q)

    # FR-05: restore the sign for a negative base with an odd exponent.
    if b < 0.0 and n % 2 != 0:
        result = -result

    # NFR-02: report a result that left the representable range instead of
    # handing back inf or 0.0. Without this the interface would display
    # "f(x) = inf", which states no cause and offers no corrective action.
    # result != result is true only for NaN; see _unusable above.
    # pylint: disable=comparison-with-itself
    if result != result or result == _INF or result == -_INF:
        raise RangeError(
            "The result is too large to represent (overflow).",
            "reduce the magnitude of a, b, or x.")
    if result == 0.0:
        raise RangeError(
            "The result is too small to represent (underflow).",
            "increase the magnitude of a, b, or x.")

    return result


# Computed once at import by the from-scratch ln, so no logarithm of a
# format constant is copied from a table.
_LN_MAX = ln(_MAX_DOUBLE)
_LN_MIN_NORMAL = ln(_MIN_NORMAL)
