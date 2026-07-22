"""f5_errors: exception hierarchy for the F5 calculator.

SOEN 6011, Summer 2026, Deliverable 2, Problem 5. Student ID: 40324569.

The project description permits "writing your own exception classes";
this module does so. Every exception carries a human-readable cause and,
where useful, a corrective action, supporting the requirement that error
messages state both (NFR-03) and the persona's need for guidance rather
than opaque failures.

Hierarchy:
    F5Error                 base for every calculator-specific error
      DomainError           input outside the real domain of a*b**x
      ConvergenceError      a series exceeded its iteration limit
      RangeError            result too large or small to represent

Catching F5Error handles any calculator error at once; catching a
specific subclass handles one kind with a tailored response.
"""


class F5Error(Exception):
    """Base class for all F5 calculator errors.

    Carries an optional corrective action so the user interface can show
    the cause and the fix together.
    """

    def __init__(self, cause, action=None):
        self.cause = cause
        self.action = action
        if action:
            message = cause + " Corrective action: " + action
        else:
            message = cause
        super().__init__(message)


class DomainError(F5Error):
    """Raised when the input lies outside the real domain of a*b**x.

    Examples: a negative base with a non-integer exponent (no real
    value), or a zero base with a non-positive exponent (undefined).
    """


class ConvergenceError(F5Error):
    """Raised when a series does not settle within the iteration limit.

    Signals that the input pushed a series beyond its safety cap rather
    than that the answer is wrong; the user interface can suggest a
    smaller magnitude of input.
    """


class RangeError(F5Error):
    """Raised when a result is too large or too small to represent.

    Distinguishes overflow and underflow from a genuine domain error, so
    the user interface can advise reducing the magnitude of x or b rather
    than implying the input was illegal.
    """