"""f5_gui: Tkinter graphical interface for the F5 calculator.

SOEN 6011, Summer 2026, Deliverable 2, Problem 5. Student ID: 40324569.

Provides the GUI required by the project description (DC-01). Uses only
the standard-library tkinter module (a user-interface toolkit, which the
"from scratch" rule permits) together with the from-scratch computation
in f5_core. Runs on a standard Python installation with no third-party
package and no IDE (DC-02).

Input validation implements FR-07 (malformed), FR-08 (empty), and FR-09
(non-finite); FR-10 provides an explicit quit control. Every error states
its cause and a corrective action (NFR-03).
"""

import tkinter as tk
import traceback
from tkinter import font as tkfont

from f5_core import compute_f5
from f5_errors import F5Error, InputError


# The infinity sentinel, formed by arithmetic rather than by float("inf"),
# so that the only built-in conversion in the program is the float() call
# that reads user input, which DC-03 permits as an input function.
_INF = 1e308 * 10.0


def parse_real(text, name):
    """Return text as a finite float, or raise F5Error explaining why not.

    Implements the input rules the GUI enforces before computing:
      FR-08 empty entry
      FR-07 not a decimal number
      FR-09 non-finite value (NaN or infinity)
    """
    stripped = text.strip()
    if stripped == "":
        raise InputError("The value for " + name + " is empty.",
                         "enter a number such as 2, -0.5, or 10.")
    try:
        value = float(stripped)
    except ValueError as exc:
        raise InputError("'" + text + "' is not a number in decimal notation "
                         "for " + name + ".",
                         "enter a value such as 2, -0.5, or 10.") from exc
    # Reject NaN and +/- infinity. float() accepts the strings "nan", "inf"
    # and "1e400", so this test is what actually enforces FR-09.
    # value != value is true only for NaN.
    if value != value or value == _INF or value == -_INF:
        raise InputError("The value for " + name + " is not finite.",
                         "enter an ordinary decimal number.")
    return value


class F5App:
    """The calculator window: three inputs, a result line, and controls."""

    def __init__(self, root):
        self.root = root
        root.title("F5 Calculator  f(x) = a \u00b7 b^x")
        root.configure(padx=20, pady=16)
        root.resizable(False, False)

        body = tkfont.nametofont("TkDefaultFont").copy()
        body.configure(size=11)
        mono = tkfont.Font(family="Courier", size=14, weight="bold")
        small = body.copy()
        small.configure(size=9)

        # Heading.
        tk.Label(root, text="f(x) = a \u00b7 b\u02e3", font=("Georgia", 16)) \
            .grid(row=0, column=0, columnspan=3, pady=(0, 12), sticky="w")

        # Input grid: a label and an entry per variable.
        self.entries = {}
        for i, (name, hint) in enumerate(
                [("a", "any real number"),
                 ("b", "any real (see domain)"),
                 ("x", "whole number when b < 0")]):
            tk.Label(root, text=name + " =", font=body) \
                .grid(row=1 + i, column=0, sticky="e", padx=(0, 6), pady=3)
            entry = tk.Entry(root, width=22, font=body, justify="right")
            entry.grid(row=1 + i, column=1, pady=3)
            tk.Label(root, text=hint, font=small, fg="#777") \
                .grid(row=1 + i, column=2, sticky="w", padx=(8, 0))
            self.entries[name] = entry

        # Domain note. The persona's complaint was that tools give no
        # indication of the valid domain (PP-02) and no guidance on
        # valid ranges (N-04), so it is stated before an error occurs,
        # not only after one.
        tk.Label(root,
                 text="Domain:   b > 0 \u2192 any x      "
                      "b < 0 \u2192 whole x only      b = 0 \u2192 x > 0",
                 font=small, fg="#555", anchor="w") \
            .grid(row=4, column=0, columnspan=3, sticky="we", pady=(10, 0))

        # Result line (monospace: it is data, not prose).
        self.result = tk.Label(root, text="", font=mono, fg="#14401b",
                               anchor="w")
        self.result.grid(row=5, column=0, columnspan=3, sticky="we",
                         pady=(10, 2))

        # Message line for errors (cause + corrective action).
        self.message = tk.Label(root, text="", font=small, fg="#8c1010",
                                anchor="w", wraplength=340, justify="left")
        self.message.grid(row=6, column=0, columnspan=3, sticky="we")

        # Controls.
        controls = tk.Frame(root)
        controls.grid(row=7, column=0, columnspan=3, pady=(12, 0), sticky="we")
        compute = tk.Button(controls, text="Compute", width=12,
                            command=self.on_compute)
        compute.pack(side="left")
        tk.Button(controls, text="Clear", width=8, command=self.on_clear) \
            .pack(side="left", padx=8)
        tk.Button(controls, text="Quit", width=8, command=root.destroy) \
            .pack(side="right")  # FR-10

        # Enter key triggers a computation from any entry.
        root.bind("<Return>", lambda event: self.on_compute())
        root.bind("<Escape>", lambda event: root.destroy())  # FR-10
        self.entries["a"].focus_set()

        # Any fault that escapes a callback is routed to this app's own
        # handler rather than to Tkinter's default. See the method for
        # why the handler exists and what it deliberately does not do.
        root.report_callback_exception = self.report_callback_exception

    def on_compute(self):
        """Validate all three inputs, compute, and show result or error."""
        self.result.config(text="")
        self.message.config(text="")
        try:
            a = parse_real(self.entries["a"].get(), "a")
            b = parse_real(self.entries["b"].get(), "b")
            x = parse_real(self.entries["x"].get(), "x")
            value = compute_f5(a, b, x)
        except F5Error as error:
            self.message.config(text=str(error))
            return
        self.result.config(text="f(x) = " + repr(value))

    def report_callback_exception(self, exc_type, exc_value, exc_tb):
        """Surface a fault that escaped a callback, without hiding it.

        D3 revision. D2 wrapped on_compute in a bare `except Exception`
        that turned every fault into one generic sentence. The window
        survived, but a programming defect became indistinguishable
        from a handled condition and left no trace anywhere, so neither
        testing nor the developer could see it. on_compute now catches
        F5Error and nothing else.

        Removing that block does not reintroduce PP-03. Tkinter's
        CallWrapper already intercepts an exception raised inside a
        callback, hands it to this method, and continues the event
        loop, so the window does not close either way. What this
        override adds is honesty: the full traceback goes to the
        terminal for the developer, and the window says plainly that
        the fault is internal rather than dressing it up as an ordinary
        input error the user could act on.

        DC-03 note. traceback is used here for diagnostic OUTPUT, in
        the same category as print, and performs no part of computing
        ab^x. The mathematics remains from scratch in f5_math and
        f5_core.
        """
        traceback.print_exception(exc_type, exc_value, exc_tb)
        self.result.config(text="")
        self.message.config(
            text="Internal fault: a defect in the calculator, not a "
                 "problem with your input. Details have been written to "
                 "the terminal. Corrective action: press Clear and "
                 "continue; report the traceback if it recurs.")

    def on_clear(self):
        """Empty every field and both output lines."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.result.config(text="")
        self.message.config(text="")
        self.entries["a"].focus_set()


def main():
    root = tk.Tk()
    F5App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
