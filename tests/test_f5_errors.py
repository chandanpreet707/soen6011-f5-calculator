"""Tests for the exception hierarchy (f5_errors).

Covers the design the D2 evaluation examined: five distinct failure
kinds under one base, so that one except clause can catch every
calculator error while a caller that cares can catch just one kind.
"""

import unittest

from f5_errors import (AlgorithmRangeError, ConvergenceError, DomainError,
                       F5Error, InputError, RangeError)

SUBCLASSES = (InputError, DomainError, ConvergenceError, RangeError,
              AlgorithmRangeError)


class TestHierarchy(unittest.TestCase):
    """Every calculator error is catchable as F5Error."""

    def test_every_subclass_derives_from_f5error(self):
        """One except F5Error clause must catch all five kinds."""
        for cls in SUBCLASSES:
            with self.subTest(cls=cls.__name__):
                self.assertTrue(issubclass(cls, F5Error))

    def test_f5error_derives_from_exception(self):
        """The base must be a normal exception, not a bare object."""
        self.assertTrue(issubclass(F5Error, Exception))

    def test_subclasses_are_distinct(self):
        """No kind may be an alias of another, or the split is fiction."""
        for cls in SUBCLASSES:
            for other in SUBCLASSES:
                if cls is not other:
                    with self.subTest(cls=cls.__name__, other=other.__name__):
                        self.assertFalse(issubclass(cls, other))

    def test_algorithm_range_error_is_not_a_range_error(self):
        """NFR-05: the two range failures must stay separable.

        RangeError means the exact result is unrepresentable.
        AlgorithmRangeError means the result IS representable but
        Algorithm B cannot form it. Reporting the second as the first
        would tell the user something untrue.
        """
        self.assertFalse(issubclass(AlgorithmRangeError, RangeError))
        self.assertFalse(issubclass(RangeError, AlgorithmRangeError))


class TestMessageComposition(unittest.TestCase):
    """NFR-03: every message states a cause and a corrective action."""

    def test_message_joins_cause_and_action(self):
        """Both halves must reach the user in one readable sentence."""
        error = DomainError("Cause sentence.", "do the other thing.")
        text = str(error)
        self.assertIn("Cause sentence.", text)
        self.assertIn("do the other thing.", text)
        self.assertIn("Corrective action:", text)

    def test_cause_and_action_are_kept_as_attributes(self):
        """The interface may want the halves separately, not just joined."""
        error = RangeError("Cause sentence.", "do the other thing.")
        self.assertEqual(error.cause, "Cause sentence.")
        self.assertEqual(error.action, "do the other thing.")

    def test_action_is_optional(self):
        """A cause alone must not produce a dangling 'Corrective action:'."""
        error = InputError("Cause only.")
        self.assertEqual(str(error), "Cause only.")
        self.assertIsNone(error.action)

    def test_every_subclass_composes_messages_the_same_way(self):
        """NFR-03 applies to all five kinds, not just the common ones."""
        for cls in SUBCLASSES:
            with self.subTest(cls=cls.__name__):
                error = cls("A cause.", "an action.")
                self.assertIn("A cause.", str(error))
                self.assertIn("an action.", str(error))


if __name__ == "__main__":
    unittest.main()
