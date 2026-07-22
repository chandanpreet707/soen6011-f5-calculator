"""f5_math: subordinate functions for F5, f(x) = a * b**x.

SOEN 6011, Summer 2026, Deliverable 2, Problem 5. Student ID: 40324569.

Everything in this module is implemented from first principles: no
imports, no math module, no built-in numeric helpers. Only the
arithmetic operators (+, -, *, /, //, %) and comparisons are used,
which the project description permits.

Build order (one commit per function):
    1. absolute, floor_int
    2. pow_int
    3. ln
    4. exp                  <- this commit
"""

EPSILON = 1e-12   # series stopping tolerance; supports NFR-01
                  # (at least 6 significant digits, with margin)
MAX_ITER = 10000  # safety cap so a series can never loop forever


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


def _ln_series(m, eps, max_iter):
    """Series part of ln, for m in [1, 2): ln(m) = 2(t + t^3/3 + ...)
    with t = (m - 1)/(m + 1). For m in [1, 2), |t| <= 1/3, so every
    new term is at least 9 times smaller: fast, guaranteed progress.
    """
    t = (m - 1.0) / (m + 1.0)
    t2 = t * t
    term = t
    total = 0.0
    k = 0
    while absolute(term / (2 * k + 1)) >= eps:
        if k >= max_iter:
            raise ArithmeticError("ln series failed to converge.")
        total += term / (2 * k + 1)
        term *= t2
        k += 1
    return 2.0 * total


def ln(b, eps=EPSILON, max_iter=MAX_ITER):
    """Natural logarithm of b > 0, from scratch.

    D2 improvement over D1 (responds to flash feedback): RANGE
    REDUCTION. Write b = m * 2**p with m in [1, 2); then
        ln(b) = ln(m) + p * ln(2).
    The series runs only on m, where it converges fast, so extreme
    bases (b = 1e15 or b = 1e-15) no longer cause slow convergence.
    ln(2) is computed once by the same series, so nothing is copied
    from a table.
    """
    if b <= 0:
        raise ArithmeticError("ln is defined only for positive arguments.")
    p = 0
    m = b
    while m >= 2.0:      # too big: halve, and remember how often
        m /= 2.0
        p += 1
    while m < 1.0:       # too small: double, and remember how often
        m *= 2.0
        p -= 1
    return _ln_series(m, eps, max_iter) + p * _LN2



def exp(y, eps=EPSILON, max_iter=MAX_ITER):
    """Exponential of y via the Maclaurin series 1 + y + y^2/2! + ...

    Each term is the previous one times y/k, so no factorial is ever
    formed. Truncation when |term| < eps bounds the error by the first
    omitted term, meeting NFR-01.

    For y < 0 the raw series alternates between large terms that nearly
    cancel, destroying accuracy (catastrophic cancellation). D2 instead
    computes exp(y) = 1 / exp(-y): the positive-argument series has only
    positive terms and no cancellation. Defect found by testing the D1
    design against a reference; matters for decay bases such as b = 0.5,
    where f * ln b is negative (persona use case).
    """
    if y < 0:
        return 1.0 / exp(-y, eps, max_iter)
    term = 1.0
    total = 1.0
    k = 1
    while absolute(term) >= eps:
        if k >= max_iter:
            raise ArithmeticError("exp series failed to converge.")
        term *= y / k
        total += term
        k += 1
    return total


_LN2 = _ln_series(2.0, EPSILON, MAX_ITER)  # computed once, from scratch