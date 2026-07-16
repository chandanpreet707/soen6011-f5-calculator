"""f5_math: subordinate functions for F5, f(x) = a * b**x.

SOEN 6011, Summer 2026, Deliverable 2, Problem 5. Student ID: 40324569.

Everything in this module is implemented from first principles: no
imports, no math module, no built-in numeric helpers. Only the
arithmetic operators (+, -, *, /, //, %) and comparisons are used,
which the project description permits.

Build order (one commit per function):
    1. absolute, floor_int
    2. pow_int              <- this commit
    3. ln
    4. exp
"""


def absolute(y):
    """Return |y| without using the abs() built-in.

    Used by ln/exp for tolerance tests (|term| >= eps) and by the F5
    core for sign handling when the base b is negative.
    """
    return -y if y < 0 else y


def floor_int(y):
    """Return the greatest integer n with n <= y, as an int.

    Needed by Algorithm B to split the exponent x = n + f into its
    integer part n and fractional part f in [0, 1).

    int(y) truncates toward zero, which differs from floor for
    negative non-integers (int(-2.5) == -2 but floor(-2.5) == -3),
    so that case is corrected explicitly.
    """
    n = int(y)              # truncation toward zero (type conversion)
    if y < 0 and y != n:    # negative and not already a whole number
        n -= 1
    return n


def pow_int(b, n):
    """Return b**n for a whole number n >= 0, by squaring.

    Persona context (Elodie): a culture that doubles every hour has a
    growth factor of 2**13 after 13 hours. Since 13 = 8 + 4 + 1
    (binary 1101), we can build 2**13 from repeated squares:
    2**13 = 2**8 * 2**4 * 2**1. This needs only ~log2(n) rounds
    (4 rounds for n = 13; ~10 for n = 1000) instead of n
    multiplications, so it is both faster and accumulates less
    floating-point rounding error.

    The integer part of the exponent is computed EXACTLY this way,
    which is the reason Algorithm B splits x = n + f (D1/Problem 3).
    """
    result = 1.0
    while n > 0:
        if n % 2 == 1:      # current binary digit of n is 1
            result *= b     # this power belongs in the answer
        b *= b              # b becomes b^2, b^4, b^8, ...
        n //= 2             # move to the next binary digit
    return result