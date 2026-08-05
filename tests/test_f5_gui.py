"""Tests for the interface layer (f5_gui).

Two concerns. First, parse_real, which enforces FR-07, FR-08 and FR-09
before any computation runs. Second, the exception policy the D2
evaluation required: on_compute must catch F5Error and nothing else,
so that a programming defect stays visible instead of being dressed up
as an ordinary error message.

Importing f5_gui imports tkinter but does not open a window, so these
tests run without a display. If tkinter is unavailable the module is
skipped rather than failing the suite.
"""

import inspect
import re
import unittest

try:
    import f5_gui
    from f5_gui import parse_real
    from f5_errors import F5Error, InputError
    TKINTER_AVAILABLE = True
except ImportError:                     # pragma: no cover
    TKINTER_AVAILABLE = False


@unittest.skipUnless(TKINTER_AVAILABLE, "tkinter is not installed")
class TestParseRealAccepts(unittest.TestCase):
    """Valid entries must pass through unchanged."""

    def test_plain_decimals(self):
        """Ordinary values the persona would type."""
        self.assertEqual(parse_real("2", "a"), 2.0)
        self.assertEqual(parse_real("-0.5", "b"), -0.5)
        self.assertEqual(parse_real("10.25", "x"), 10.25)

    def test_scientific_notation(self):
        """Growth models routinely need exponents."""
        self.assertEqual(parse_real("1e15", "b"), 1e15)
        self.assertEqual(parse_real("-2.5e-8", "a"), -2.5e-8)

    def test_surrounding_whitespace_is_tolerated(self):
        """A stray space must not be treated as malformed input."""
        self.assertEqual(parse_real("  3.5  ", "x"), 3.5)

    def test_zero(self):
        """Zero is a legitimate entry for every field."""
        self.assertEqual(parse_real("0", "a"), 0.0)


@unittest.skipUnless(TKINTER_AVAILABLE, "tkinter is not installed")
class TestParseRealRejects(unittest.TestCase):
    """FR-07, FR-08 and FR-09: reject before computing."""

    def test_empty_entry(self):
        """FR-08."""
        with self.assertRaises(InputError):
            parse_real("", "a")

    def test_whitespace_only_entry(self):
        """FR-08: a field of spaces is still empty."""
        with self.assertRaises(InputError):
            parse_real("   ", "a")

    def test_not_a_decimal_number(self):
        """FR-07."""
        for text in ("abc", "2..5", "1,5", "--3", "3x"):
            with self.subTest(text=text):
                with self.assertRaises(InputError):
                    parse_real(text, "b")

    def test_non_finite_values(self):
        """FR-09: float() accepts these strings, so parse_real must not."""
        for text in ("nan", "inf", "-inf", "Infinity", "1e400"):
            with self.subTest(text=text):
                with self.assertRaises(InputError):
                    parse_real(text, "x")

    def test_rejection_names_the_field(self):
        """The user must know WHICH entry was wrong."""
        with self.assertRaises(InputError) as caught:
            parse_real("abc", "b")
        self.assertIn("b", str(caught.exception))

    def test_rejection_states_cause_and_action(self):
        """NFR-03."""
        with self.assertRaises(InputError) as caught:
            parse_real("", "a")
        self.assertIn("Corrective action:", str(caught.exception))

    def test_input_error_is_catchable_as_f5error(self):
        """One except clause must cover input and mathematics alike."""
        with self.assertRaises(F5Error):
            parse_real("abc", "a")


@unittest.skipUnless(TKINTER_AVAILABLE, "tkinter is not installed")
class TestExceptionPolicy(unittest.TestCase):
    """REGRESSION (D3). The D2 evaluation finding.

    D2 wrapped on_compute in a bare `except Exception` that converted
    every fault into one generic sentence, so a programming defect was
    indistinguishable from a handled condition and left no trace. These
    tests pin the design that replaced it. They read the source rather
    than run the event loop, because the property being asserted is
    which exceptions the handler declines to catch, and an absence
    cannot be observed by calling the method.
    """

    def test_on_compute_does_not_catch_broad_exceptions(self):
        """Only F5Error may be caught in the compute handler."""
        source = inspect.getsource(f5_gui.F5App.on_compute)
        self.assertNotIn("except Exception", source)
        self.assertNotIn("except BaseException", source)
        self.assertNotIn("except:", source)

    def test_on_compute_still_catches_f5error(self):
        """Handled conditions must remain handled, not propagate."""
        source = inspect.getsource(f5_gui.F5App.on_compute)
        self.assertIn("except F5Error", source)

    def test_no_broad_except_suppression_remains(self):
        """The pylint disable that silenced the checker must be gone."""
        source = inspect.getsource(f5_gui)
        self.assertNotIn("disable=broad-except", source)

    def test_fault_handler_exists(self):
        """An escaped fault must reach a handler that reports it."""
        self.assertTrue(hasattr(f5_gui.F5App, "report_callback_exception"))
        self.assertTrue(callable(f5_gui.F5App.report_callback_exception))

    def test_fault_handler_is_wired_to_the_root_window(self):
        """Tkinter only calls the override if it is installed."""
        source = inspect.getsource(f5_gui.F5App.__init__)
        self.assertIn("report_callback_exception", source)

    def test_fault_handler_prints_a_traceback(self):
        """Visibility is the point: the defect must reach the terminal."""
        source = inspect.getsource(f5_gui.F5App.report_callback_exception)
        self.assertIn("traceback.print_exception", source)

    def test_every_method_called_on_self_exists(self):
        """REGRESSION (D3). A refactor deleted a method still in use.

        Splitting __init__ into builder methods removed add_button
        while three call sites remained, and the window raised
        AttributeError on launch. Nothing in this suite noticed,
        because instantiating F5App needs a display and none of the
        other tests construct it.

        This closes that gap without a display: it reads the class
        source for calls and callback references made through self,
        and checks each one resolves. It would have failed on that
        refactor, and it fails on any future one that repeats it.
        """
        source = inspect.getsource(f5_gui.F5App)
        called = set(re.findall(r"self\.(\w+)\(", source))
        referenced = set(re.findall(r"=\s*self\.(\w+)\s*[,)]", source))
        assigned = set(re.findall(r"self\.(\w+)\s*=", source))
        for name in sorted((called | referenced) - assigned):
            with self.subTest(name=name):
                self.assertTrue(
                    hasattr(f5_gui.F5App, name),
                    f"F5App calls self.{name} but no such attribute "
                    f"exists")

    def test_input_error_is_chained_from_value_error(self):
        """The original cause must not be discarded (W0707)."""
        source = inspect.getsource(f5_gui.parse_real)
        self.assertIn("from exc", source)


if __name__ == "__main__":
    unittest.main()
