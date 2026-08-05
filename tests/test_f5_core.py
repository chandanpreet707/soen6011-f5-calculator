"""Tests for compute_f5 (f5_core), the function itself.

Organised by requirement: the four domain rules, the accuracy target,
and the three range outcomes. Two classes are regressions pinning
defects: the zero-multiplier shortcut past the domain rules (found in
D2) and the series tolerance (found in D3).
"""

import unittest
from decimal import Decimal, getcontext

from f5_core import compute_f5
from f5_errors import AlgorithmRangeError, DomainError, RangeError

getcontext().prec = 60


def exact(a, b, x):
    """Return a * b**x at 60 digits, signed for a negative base."""
    whole = x // 1.0
    value = Decimal(a) * (Decimal(abs(b)) ** Decimal(x))
    if b < 0 and whole % 2.0 != 0.0:
        value = -value
    return value


def relative_error(produced, a, b, x):
    """Return the relative error of produced against the oracle."""
    reference = exact(a, b, x)
    return abs((Decimal(produced) - reference) / reference)


class TestPositiveBase(unittest.TestCase):
    """FR-02: for b > 0 the function is defined for every real x."""

    def test_persona_growth_case(self):
        """Elodie's scenario: a culture growing by 40 percent per step."""
        self.assertLess(relative_error(compute_f5(100.0, 1.4, 3.5),
                                       100.0, 1.4, 3.5), Decimal("1e-12"))

    def test_integer_exponent_is_exact(self):
        """The integer part comes from pow_int, so no series error."""
        self.assertEqual(compute_f5(1.0, 2.0, 10.0), 1024.0)
        self.assertEqual(compute_f5(3.0, 10.0, 2.0), 300.0)

    def test_exponent_zero_returns_the_multiplier(self):
        """b**0 = 1, so the answer is a."""
        for base in (0.5, 1.0, 2.0, 1e100):
            with self.subTest(base=base):
                self.assertEqual(compute_f5(7.0, base, 0.0), 7.0)

    def test_decay_base(self):
        """b < 1 makes f * ln b negative: the exp cancellation path."""
        self.assertLess(relative_error(compute_f5(1.0, 0.5, 3.5),
                                       1.0, 0.5, 3.5), Decimal("1e-12"))

    def test_negative_exponent(self):
        """A negative x inverts the integer power."""
        self.assertLess(relative_error(compute_f5(2.0, 3.0, -2.5),
                                       2.0, 3.0, -2.5), Decimal("1e-12"))

    def test_extreme_base_now_supported(self):
        """Range reduction: D1 rejected bases beyond about 1e5."""
        self.assertLess(relative_error(compute_f5(1.0, 1e15, 0.9),
                                       1.0, 1e15, 0.9), Decimal("1e-12"))


class TestZeroBase(unittest.TestCase):
    """FR-03: b = 0 is defined only for x > 0."""

    def test_positive_exponent_gives_zero(self):
        """0**x = 0 for x > 0."""
        self.assertEqual(compute_f5(5.0, 0.0, 2.0), 0.0)

    def test_zero_exponent_is_rejected(self):
        """0**0 is undefined."""
        with self.assertRaises(DomainError):
            compute_f5(1.0, 0.0, 0.0)

    def test_negative_exponent_is_rejected(self):
        """0**negative is undefined."""
        with self.assertRaises(DomainError):
            compute_f5(1.0, 0.0, -1.0)

    def test_rejection_states_cause_and_action(self):
        """NFR-03 applies to domain rejections too."""
        with self.assertRaises(DomainError) as caught:
            compute_f5(1.0, 0.0, -1.0)
        self.assertIsNotNone(caught.exception.action)
        self.assertIn("Corrective action:", str(caught.exception))


class TestNegativeBase(unittest.TestCase):
    """FR-04 and FR-05: negative bases need a whole exponent."""

    def test_non_integer_exponent_is_rejected(self):
        """FR-04: no real value exists."""
        for x in (0.5, -0.5, 2.25, -3.75):
            with self.subTest(x=x):
                with self.assertRaises(DomainError):
                    compute_f5(1.0, -2.0, x)

    def test_even_exponent_gives_positive_result(self):
        """FR-05: sign tracking, even case."""
        self.assertEqual(compute_f5(3.0, -2.0, 4.0), 48.0)

    def test_odd_exponent_gives_negative_result(self):
        """FR-05: sign tracking, odd case."""
        self.assertEqual(compute_f5(1.0, -2.0, 3.0), -8.0)

    def test_negative_odd_exponent_keeps_the_sign(self):
        """The sign rule must survive exponent inversion."""
        self.assertAlmostEqual(compute_f5(1.0, -2.0, -3.0), -0.125, places=15)

    def test_exponent_zero_on_negative_base(self):
        """b**0 = 1 even when b < 0."""
        self.assertEqual(compute_f5(1.0, -2.0, 0.0), 1.0)


class TestZeroMultiplier(unittest.TestCase):
    """REGRESSION (D2). a = 0 must not bypass the domain rules.

    In D2 a zero multiplier short-circuited ahead of the domain tests,
    so a = 0, b = -2, x = 0.5 returned 0.0 instead of being rejected
    under FR-04. An input outside the real domain is outside it
    whatever a happens to be.
    """

    def test_zero_multiplier_still_rejects_negative_base(self):
        """FR-04 must fire even when the answer would be zero."""
        with self.assertRaises(DomainError):
            compute_f5(0.0, -2.0, 0.5)

    def test_zero_multiplier_still_rejects_zero_base(self):
        """FR-03 must fire even when the answer would be zero."""
        with self.assertRaises(DomainError):
            compute_f5(0.0, 0.0, -1.0)

    def test_zero_multiplier_returns_zero_when_input_is_valid(self):
        """Inside the domain, a = 0 does give zero."""
        self.assertEqual(compute_f5(0.0, 3.0, 2.5), 0.0)


class TestAccuracy(unittest.TestCase):
    """NFR-01: at least six significant digits in the normal range.

    The bound asserted here is 1e-11, far tighter than the six digits
    NFR-01 requires, because a regression to the D2 tolerance produced
    8.98e-10 and must be caught rather than tolerated.
    """

    CASES = (
        (2.0, 3.0, 2.5),
        (100.0, 1.4, 3.5),
        (5.0, 10.0, 0.5),
        (1.0, 0.5, 3.5),
        (2.0, 7.0, 3.25),
        (1.0, 1e15, 0.9),
        (6.7e248, -6.73, -390.0),
    )

    def test_published_cases_meet_the_bound(self):
        """The verification cases carried forward from D2."""
        for a, b, x in self.CASES:
            with self.subTest(a=a, b=b, x=x):
                self.assertLess(relative_error(compute_f5(a, b, x), a, b, x),
                                Decimal("1e-11"))

    def test_worst_sampled_case_meets_the_bound(self):
        """REGRESSION (D3). The worst input found by tools/.

        This triple produced 8.98e-10 under the D2 tolerance, which is
        17 times the figure D2 published. It fails on D2 code.
        """
        a, b, x = (-7.579783552227228e-285, 4.280783297655058e+238,
                   -0.013955014588702852)
        self.assertLess(relative_error(compute_f5(a, b, x), a, b, x),
                        Decimal("1e-11"))

    def test_second_worst_sampled_case(self):
        """A different scale combination from the same search."""
        a, b, x = (-5.555867607763996e+109, 1.5759100997500323e+281,
                   -0.06588007342617175)
        self.assertLess(relative_error(compute_f5(a, b, x), a, b, x),
                        Decimal("1e-11"))


class TestRangeSafeOrdering(unittest.TestCase):
    """The factor ordering that keeps intermediates representable."""

    def test_opposing_scales_do_not_overflow(self):
        """b**x alone overflows; the ordering never forms it."""
        self.assertLess(relative_error(compute_f5(1e-300, 1e300, 2.0),
                                       1e-300, 1e300, 2.0),
                        Decimal("1e-11"))

    def test_subnormal_intermediate_is_avoided(self):
        """Writing a*b**x here loses 15 percent; ordering does not."""
        a, b, x = 6.7e248, -6.73, -390.0
        self.assertLess(relative_error(compute_f5(a, b, x), a, b, x),
                        Decimal("1e-11"))


class TestRangeFailures(unittest.TestCase):
    """NFR-02 and NFR-05: report range failures under the right name."""

    def test_overflow_raises_range_error(self):
        """NFR-02: never return inf."""
        with self.assertRaises(RangeError):
            compute_f5(1e300, 10.0, 300.0)

    def test_underflow_raises_range_error(self):
        """NFR-02: never silently flush to zero."""
        with self.assertRaises(RangeError):
            compute_f5(1e-300, 0.1, 300.0)

    def test_range_error_states_cause_and_action(self):
        """NFR-03 applies to range failures too."""
        with self.assertRaises(RangeError) as caught:
            compute_f5(1e300, 10.0, 300.0)
        self.assertIn("Corrective action:", str(caught.exception))

    def test_algorithm_range_error_is_distinct(self):
        """NFR-05: an unformable intermediate is not an overflow.

        A RangeError here would claim the result is unrepresentable
        when it is not, which is the untruth DC-04 exists to prevent.
        """
        a, b, x = (3.5953268659865946e+252, 4.279798940129467e+179, -3.0)
        # The exact answer, 4.59e-287, is an ordinary representable
        # double. Only the intermediate half of the integer power is
        # not, so an overflow report would be false.
        with self.assertRaises(AlgorithmRangeError) as caught:
            compute_f5(a, b, x)
        self.assertNotIsInstance(caught.exception, RangeError)

    def test_algorithm_range_error_states_cause_and_action(self):
        """NFR-03 and NFR-05 together: name the condition honestly."""
        a, b, x = (-1.5006458204315662e-166, 7.842989904105228e-190,
                   -2.1037990762764025)
        with self.assertRaises(AlgorithmRangeError) as caught:
            compute_f5(a, b, x)
        self.assertIn("Corrective action:", str(caught.exception))

    def test_no_result_is_ever_infinite_or_nan(self):
        """Whatever happens, a returned value must be usable."""
        cases = ((1e300, 10.0, 300.0), (1e-300, 0.1, 300.0),
                 (1e-300, 1e300, 2.0), (2.0, 3.0, 2.5))
        for a, b, x in cases:
            with self.subTest(a=a, b=b, x=x):
                try:
                    value = compute_f5(a, b, x)
                except (RangeError, AlgorithmRangeError, DomainError):
                    continue
                self.assertEqual(value, value)
                self.assertNotEqual(value, 1e308 * 10.0)
                self.assertNotEqual(value, -(1e308 * 10.0))


if __name__ == "__main__":
    unittest.main()
