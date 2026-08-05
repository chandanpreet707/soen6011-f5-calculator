"""Tests for the five subordinate functions (f5_math).

These are the from-scratch building blocks required by D2/Problem 5.
Two tests here are regressions pinning defects found in D3: the series
tolerance (which was 1e-12 and left 1e-12 of error in ln 2) and the
reciprocal form of exp for negative arguments (D2, catastrophic
cancellation).
"""

import unittest
from decimal import Decimal, getcontext

import f5_math
from f5_errors import ConvergenceError, DomainError
from f5_math import absolute, exp, floor_int, ln, pow_int

getcontext().prec = 60

# ln(2) and e to full double precision, used only as oracles.
LN2 = Decimal(2).ln()
EULER = Decimal(1).exp()


def relative_error(produced, exact):
    """Return |produced - exact| / |exact| at 60 digits."""
    return abs((Decimal(produced) - exact) / exact)


class TestAbsolute(unittest.TestCase):
    """absolute() replaces the abs() built-in under DC-03."""

    def test_positive_unchanged(self):
        """A positive value passes through."""
        self.assertEqual(absolute(3.5), 3.5)

    def test_negative_is_reflected(self):
        """A negative value returns its magnitude."""
        self.assertEqual(absolute(-3.5), 3.5)

    def test_zero(self):
        """Zero is its own magnitude."""
        self.assertEqual(absolute(0.0), 0.0)

    def test_negative_zero_gives_zero(self):
        """-0.0 must compare equal to 0.0, not become a special case."""
        self.assertEqual(absolute(-0.0), 0.0)


class TestFloorInt(unittest.TestCase):
    """floor_int() must round toward minus infinity, not toward zero.

    D2 improvement 3. Truncation would make f = x - n negative for a
    negative x, breaking the requirement that f lies in [0, 1).
    """

    def test_positive_non_integer(self):
        """Ordinary downward rounding."""
        self.assertEqual(floor_int(2.7), 2.0)

    def test_negative_non_integer_rounds_down_not_toward_zero(self):
        """floor(-2.5) is -3, not -2. This is the D2 defect."""
        self.assertEqual(floor_int(-2.5), -3.0)

    def test_exact_integers_are_fixed_points(self):
        """A whole value must not be moved."""
        for value in (-4.0, -1.0, 0.0, 1.0, 7.0):
            with self.subTest(value=value):
                self.assertEqual(floor_int(value), value)

    def test_fractional_part_stays_in_unit_interval(self):
        """The property Algorithm B depends on, checked directly."""
        for x in (-7.25, -2.5, -0.1, 0.0, 0.3, 5.75, 12.5):
            with self.subTest(x=x):
                fraction = x - floor_int(x)
                self.assertGreaterEqual(fraction, 0.0)
                self.assertLess(fraction, 1.0)


class TestPowInt(unittest.TestCase):
    """Exponentiation by squaring: the integer part must be exact."""

    def test_exponent_zero_is_one(self):
        """b**0 = 1 for any base."""
        self.assertEqual(pow_int(7.0, 0), 1.0)

    def test_exponent_one_returns_base(self):
        """b**1 = b."""
        self.assertEqual(pow_int(7.0, 1), 7.0)

    def test_small_powers_are_exact(self):
        """No series error may appear in the integer part."""
        self.assertEqual(pow_int(2.0, 10), 1024.0)
        self.assertEqual(pow_int(3.0, 4), 81.0)
        self.assertEqual(pow_int(10.0, 6), 1000000.0)

    def test_accepts_whole_valued_float_exponent(self):
        """floor_int returns a float; pow_int must accept one."""
        self.assertEqual(pow_int(2.0, 10.0), 1024.0)

    def test_agrees_with_repeated_multiplication(self):
        """Cross-check the squaring shortcut against the naive loop."""
        for base in (1.5, 2.0, 7.0):
            for n in range(0, 13):
                expected = 1.0
                for _ in range(n):
                    expected *= base
                with self.subTest(base=base, n=n):
                    self.assertEqual(pow_int(base, n), expected)


class TestLn(unittest.TestCase):
    """Natural logarithm with range reduction."""

    def test_ln_one_is_zero(self):
        """The one exact value the series must reproduce."""
        self.assertEqual(ln(1.0), 0.0)

    def test_ln_two_matches_the_oracle(self):
        """Accuracy at the range-reduction boundary."""
        self.assertLess(relative_error(ln(2.0), LN2), Decimal("1e-15"))

    def test_ln_of_e_is_one(self):
        """Round trip against the exponential constant."""
        self.assertAlmostEqual(ln(float(EULER)), 1.0, places=12)

    def test_extreme_bases_converge(self):
        """Range reduction: D1 failed beyond about 1e5."""
        for exponent in (-300, -15, -1, 1, 15, 300):
            base = 10.0 ** exponent
            exact = Decimal(base).ln()
            with self.subTest(base=base):
                self.assertLess(relative_error(ln(base), exact),
                                Decimal("1e-12"))

    def test_is_monotonic(self):
        """A logarithm that is not increasing is simply wrong."""
        previous = ln(1e-300)
        for exponent in range(-299, 301, 20):
            current = ln(10.0 ** exponent)
            with self.subTest(exponent=exponent):
                self.assertGreater(current, previous)
            previous = current

    def test_rejects_zero_and_negative(self):
        """The logarithm has no real value there."""
        for bad in (0.0, -1.0, -1e300):
            with self.subTest(bad=bad):
                with self.assertRaises(DomainError):
                    ln(bad)

    def test_iteration_cap_raises_convergence_error(self):
        """NFR-04: a series that will not settle must say so, not hang."""
        with self.assertRaises(ConvergenceError):
            ln(1.5, eps=0.0, max_iter=5)


class TestLn2Constant(unittest.TestCase):
    """REGRESSION (D3). The tolerance defect found by tools/.

    _LN2 is computed by the same series the tolerance governs. At
    EPSILON = 1e-12 it carried 1.03e-12 of ABSOLUTE error, which range
    reduction multiplied by p (up to 934) and exp then converted into
    roughly 1e-9 of relative error in the answer. These two tests fail
    on the D2 code and pass on D3.
    """

    def test_tolerance_reaches_the_double_precision_floor(self):
        """A tolerance above 1e-15 cannot bound _LN2 tightly enough."""
        self.assertLessEqual(f5_math.EPSILON, 1e-15)

    def test_ln2_constant_is_accurate_to_double_precision(self):
        """The constant every extreme base depends on.

        _LN2 is private to f5_math, but it is the exact quantity the
        defect lived in, so the test reaches for it deliberately
        rather than inferring it from a public result.
        """
        # pylint: disable=protected-access
        error = abs(Decimal(f5_math._LN2) - LN2)
        self.assertLess(error, Decimal("1e-15"))

    def test_error_does_not_amplify_through_range_reduction(self):
        """The propagation path itself, measured end to end."""
        base = 1.5759100997500323e+281
        exact = Decimal(base).ln()
        self.assertLess(relative_error(ln(base), exact), Decimal("1e-15"))


class TestExp(unittest.TestCase):
    """Exponential via the Maclaurin series."""

    def test_exp_zero_is_one(self):
        """The series must start from the right constant."""
        self.assertEqual(exp(0.0), 1.0)

    def test_exp_one_matches_the_oracle(self):
        """Accuracy at a small positive argument."""
        self.assertLess(relative_error(exp(1.0), EULER), Decimal("1e-15"))

    def test_negative_argument_avoids_cancellation(self):
        """REGRESSION (D2). The raw alternating series was wrong here.

        At y = -30 the D1 implementation was off by a factor of 6e7.
        The reciprocal form must hold accuracy instead.
        """
        exact = Decimal(-30).exp()
        self.assertLess(relative_error(exp(-30.0), exact), Decimal("1e-14"))

    def test_reciprocal_identity_holds(self):
        """exp(-y) must equal 1/exp(y) to within rounding."""
        for y in (0.5, 5.0, 30.0, 200.0):
            with self.subTest(y=y):
                product = exp(y) * exp(-y)
                self.assertAlmostEqual(product, 1.0, places=10)

    def test_large_argument_stays_accurate(self):
        """The largest argument a valid input can produce."""
        exact = Decimal(700).exp()
        self.assertLess(relative_error(exp(700.0), exact), Decimal("1e-13"))

    def test_iteration_cap_raises_convergence_error(self):
        """NFR-04: report non-convergence rather than looping forever."""
        with self.assertRaises(ConvergenceError):
            exp(50.0, eps=0.0, max_iter=5)


if __name__ == "__main__":
    unittest.main()
