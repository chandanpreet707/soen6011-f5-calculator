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
from tkinter import font as tkfont

from f5_core import compute_f5
from f5_errors import F5Error, InputError


_INF = float("inf")


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
    except ValueError:
        raise InputError("'" + text + "' is not a number in decimal notation "
                         "for " + name + ".",
                         "enter a value such as 2, -0.5, or 10.")
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
        # indication of the valid domain (P-PAIN-02) and no guidance on
        # valid ranges (P-NEED-04), so it is stated before an error occurs,
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
        except Exception as error:  # pylint: disable=broad-except
            # The persona's pain point is a tool that dies without warning.
            # Any unforeseen fault is reported in the window instead.
            self.message.config(
                text="Unexpected internal error: " + str(error)
                     + " Corrective action: press Clear and try other values.")
            return
        self.result.config(text="f(x) = " + repr(value))

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
