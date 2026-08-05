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

D3 revision, user interface design principles. The mind map selected
Nielsen's ten usability heuristics. Seven apply, two apply in part, and
"help and documentation" is rejected: three labelled fields with the
domain stated inline need no help system, and adding one would work
against "aesthetic and minimalist design".

D3 revision, accessibility. Measured against WCAG 2.2 Level AA:
  1.4.1 Use of Colour   an error is marked by the word "Error", not by
                        red text alone
  1.4.3 Contrast        every foreground meets 4.5:1 against the actual
                        window background, chosen at start-up for the
                        light or dark system appearance
  1.4.4 Resize Text     the window resizes and the text scales to 200%
                        by keyboard, where D2 fixed both
  2.1.1 Keyboard        every control is reachable and operable by
                        keyboard alone
  2.4.7 Focus Visible   the focused control carries a visible ring

Known limitation: Tk exposes no accessible-name API, and screen-reader
support for Tk widgets on macOS is unreliable. No claim of screen-reader
compatibility is made, because none could be verified.
"""

import tkinter as tk
import traceback
from tkinter import font as tkfont

from f5_core import __version__, compute_f5
from f5_errors import F5Error, InputError


# The infinity sentinel, formed by arithmetic rather than by float("inf"),
# so that the only built-in conversion in the program is the float() call
# that reads user input, which DC-03 permits as an input function.
_INF = 1e308 * 10.0

# Foreground colours, one set per system appearance. Every entry was
# measured against the corresponding window background: the worst ratio
# in either set is 5.87:1, against the 4.5:1 that WCAG 2.2 Level AA
# requires for body text (1.4.3). D2 used one fixed set chosen for a
# light window, where the result colour fell to 1.41:1 on a dark one.
LIGHT_PALETTE = {"body": "#1A1A1A", "hint": "#454545", "domain": "#454545",
                 "result": "#0B4F1C", "error": "#A31515",
                 "focus": "#0A5AA6"}
DARK_PALETTE = {"body": "#F0F0F0", "hint": "#B9B9B9", "domain": "#B9B9B9",
                "result": "#77D68D", "error": "#FF9C94",
                "focus": "#6FB6FF"}

# Point sizes at 100%. The keyboard zoom multiplies these (WCAG 1.4.4).
BASE_SIZES = {"heading": 16, "body": 11, "mono": 14, "small": 10}
BUTTON_WIDTH = 10

# How often to re-check the system appearance, in milliseconds. Tk has no
# event for a light/dark switch on macOS, so the background is re-read on
# a timer. One second is imperceptible to a reader and costs one colour
# lookup, which is far cheaper than leaving the window unreadable.
POLL_MS = 1000
MAX_SCALE = 2.0
MIN_SCALE = 1.0
SCALE_STEP = 0.25


def choose_palette(widget):
    """Return the palette that contrasts with the actual window colour.

    The system appearance is not known until run time, and on macOS the
    background is a named system colour rather than a literal one, so it
    is resolved to red/green/blue and its relative luminance computed.
    Anything at or above the midpoint is a light window.

    Falls back to the light palette if the colour cannot be resolved,
    which is the safe default: a light-window colour on an unexpectedly
    dark background is still legible, having been the D2 behaviour.
    """
    try:
        red, green, blue = widget.winfo_rgb(widget.cget("bg"))
    except tk.TclError:
        # Raised when the background is a name Tk cannot resolve.
        return LIGHT_PALETTE
    # winfo_rgb returns 16-bit channels; weights are the sRGB luma
    # coefficients used by WCAG for relative luminance.
    luma = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 65535.0
    return LIGHT_PALETTE if luma >= 0.5 else DARK_PALETTE


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
    # value != value is true only for NaN. math.isnan is a library
    # function, which DC-03 does not permit, so the idiom stays and
    # Pylint's objection to it is suppressed here deliberately.
    # pylint: disable=comparison-with-itself
    if value != value or value == _INF or value == -_INF:
        raise InputError("The value for " + name + " is not finite.",
                         "enter an ordinary decimal number.")
    return value


class F5App:
    """The calculator window: three inputs, a result line, and controls."""

    def __init__(self, root):
        self.root = root
        root.title("F5 Calculator  f(x) = a \u00b7 b^x  v" + __version__)
        root.configure(padx=20, pady=16)

        # WCAG 1.4.4. D2 called resizable(False, False) and fixed every
        # point size, so a reader who needed larger text had no way to
        # get it. The window now resizes and the fields grow with it.
        root.resizable(True, True)
        root.grid_columnconfigure(1, weight=1)

        self.palette = choose_palette(root)
        self.scale = MIN_SCALE
        # Every widget whose foreground depends on the appearance, with
        # the palette role it takes. refresh_palette walks this list.
        self.themed = []

        # Named fonts, kept so the keyboard zoom can reconfigure them:
        # every widget using a named font follows automatically.
        self.fonts = {
            "heading": tkfont.nametofont("TkDefaultFont").copy(),
            "body": tkfont.nametofont("TkDefaultFont").copy(),
            "mono": tkfont.nametofont("TkFixedFont").copy(),
            "small": tkfont.nametofont("TkDefaultFont").copy(),
        }
        self.fonts["heading"].configure(weight="bold")
        self.fonts["mono"].configure(weight="bold")
        self.apply_scale()

        self.entries = {}
        self.output = {}
        self.build_inputs(root)
        self.build_output(root)
        self.build_controls(root)
        self.bind_keys(root)

        self.entries["a"].focus_set()
        self.refresh_palette()

        # Any fault that escapes a callback is routed to this app's own
        # handler rather than to Tkinter's default. See the method for
        # why the handler exists and what it deliberately does not do.
        root.report_callback_exception = self.report_callback_exception

    def themed_label(self, parent, text, style, role, **grid):
        """Create a label, register it for re-colouring, and place it."""
        label = tk.Label(parent, text=text, font=self.fonts[style],
                         fg=self.palette[role], anchor="w")
        label.grid(**grid)
        self.themed.append((label, role))
        return label

    def build_inputs(self, root):
        """Heading, the three labelled entries, and the domain note."""
        self.themed_label(root, "f(x) = a \u00b7 b\u02e3", "heading",
                          "body", row=0, column=0, columnspan=3,
                          pady=(0, 12), sticky="w")

        background = root.cget("bg")
        for i, (name, hint) in enumerate(
                [("a", "any real number"),
                 ("b", "any real (see domain)"),
                 ("x", "whole number when b < 0")]):
            self.themed_label(root, name + " =", "body", "body",
                              row=1 + i, column=0, sticky="e",
                              padx=(0, 6), pady=3)
            entry = tk.Entry(root, width=22, font=self.fonts["body"],
                             justify="right", highlightthickness=2,
                             highlightbackground=background,
                             highlightcolor=self.palette["focus"])
            entry.grid(row=1 + i, column=1, pady=3, sticky="we")
            entry.bind("<Return>", lambda event: self.on_compute())
            self.themed_label(root, hint, "small", "hint",
                              row=1 + i, column=2, sticky="w", padx=(8, 0))
            self.entries[name] = entry

        # The persona's complaint was that tools give no indication of
        # the valid domain (PP-02) and no guidance on valid ranges
        # (N-04), so it is stated before an error occurs, not only
        # after one. Nielsen heuristic 5, error prevention.
        self.themed_label(
            root,
            "Domain:   b > 0 \u2192 any x      "
            "b < 0 \u2192 whole x only      b = 0 \u2192 x > 0",
            "small", "domain",
            row=4, column=0, columnspan=3, sticky="we", pady=(10, 0))

    def build_output(self, root):
        """The result line and the error line."""
        # Monospace: the result is data, not prose.
        self.output["result"] = self.themed_label(
            root, "", "mono", "result",
            row=5, column=0, columnspan=3, sticky="we", pady=(10, 2))

        # The error text is prefixed with the word "Error", so the
        # distinction from a result does not rest on colour (WCAG
        # 1.4.1).
        message = self.themed_label(
            root, "", "small", "error",
            row=6, column=0, columnspan=3, sticky="we")
        message.config(wraplength=340, justify="left")
        self.output["message"] = message

    def build_controls(self, root):
        """The three buttons and the text-size hint."""
        controls = tk.Frame(root, bg=root.cget("bg"))
        controls.grid(row=7, column=0, columnspan=3, pady=(12, 0),
                      sticky="we")
        self.add_button(controls, "Compute", self.on_compute, side="left")
        self.add_button(controls, "Clear", self.on_clear, side="left",
                        padx=8)
        self.add_button(controls, "Quit", root.destroy,
                        side="right")  # FR-10

        # The zoom is announced rather than left to be discovered, so it
        # does not depend on the reader recalling a shortcut (Nielsen
        # heuristic 6, recognition rather than recall).
        self.themed_label(
            root,
            "Text size:   Command +      Command -      Command 0 to reset",
            "small", "hint",
            row=8, column=0, columnspan=3, sticky="we", pady=(10, 0))

    def bind_keys(self, root):
        """Window-level keyboard bindings (WCAG 2.1.1)."""
        root.bind("<Escape>", lambda event: root.destroy())  # FR-10
        for sequence in ("<Control-equal>", "<Control-plus>",
                         "<Command-equal>", "<Command-plus>"):
            root.bind(sequence, lambda event: self.zoom(SCALE_STEP))
        for sequence in ("<Control-minus>", "<Command-minus>"):
            root.bind(sequence, lambda event: self.zoom(-SCALE_STEP))
        for sequence in ("<Control-Key-0>", "<Command-Key-0>"):
            root.bind(sequence, lambda event: self.zoom(0.0))
        root.bind("<Configure>", self.on_resize)

    def add_button(self, parent, text, command, *, side, padx=0):
        """Add one control that shows a visible ring when focused.

        WCAG 2.4.7. A Tk button on macOS is drawn by the platform and
        ignores highlightthickness, so the ring is drawn by the frame
        around it, which is recoloured on focus. Without this a
        keyboard user cannot tell which control is selected.
        """
        background = self.root.cget("bg")
        holder = tk.Frame(parent, bg=background, padx=2, pady=2)
        holder.pack(side=side, padx=padx)
        # The button carries a named font too, so its label scales with
        # everything else. WCAG 1.4.4 asks that TEXT reach 200%, not
        # most of it: a default-font button stays at 100% while the
        # rest of the window grows, which is how this was found.
        button = tk.Button(holder, text=text, width=BUTTON_WIDTH,
                           command=command, highlightthickness=0,
                           font=self.fonts["body"])
        button.pack()
        button.bind("<FocusIn>",
                    lambda event, f=holder: f.config(
                        bg=self.palette["focus"]))
        button.bind("<FocusOut>",
                    lambda event, f=holder, c=background: f.config(bg=c))
        # Return and space must both activate a focused control, so
        # that the interface is fully operable from the keyboard
        # (WCAG 2.1.1). Return is bound per control rather than on the
        # window, so it activates whichever control is focused.
        button.bind("<Return>", lambda event, b=button: b.invoke())
        button.bind("<space>", lambda event, b=button: b.invoke())
        return button

    def refresh_palette(self):
        """Re-colour the window if the system appearance has changed.

        D3 defect, found by switching macOS to Light while the window
        was open. choose_palette ran once at start-up, so the dark
        foregrounds stayed on a now-light background and the labels
        became nearly invisible: a worse contrast failure than the one
        the palette was introduced to fix.

        Only the literal colours need replacing. The background is a
        named system colour, which Tk re-resolves on its own, so the
        entry borders and button frames follow the appearance already.

        Tk raises no event for this switch on macOS, hence the timer.
        """
        palette = choose_palette(self.root)
        if palette is not self.palette:
            self.palette = palette
            for widget, role in self.themed:
                widget.config(fg=palette[role])
            for entry in self.entries.values():
                entry.config(highlightcolor=palette["focus"])
        self.root.after(POLL_MS, self.refresh_palette)

    def apply_scale(self):
        """Resize every named font to the current zoom level."""
        for name, font in self.fonts.items():
            size = int(round(BASE_SIZES[name] * self.scale))
            font.configure(size=max(8, size))

    def zoom(self, delta):
        """Change the text size, or reset it when delta is zero.

        WCAG 1.4.4 asks that text reach 200% without loss of content.
        Control or Command with plus, minus and zero are the bindings a
        reader will already expect from a browser (Nielsen heuristic 4,
        consistency and standards).
        """
        if delta == 0.0:
            self.scale = MIN_SCALE
        else:
            self.scale = min(MAX_SCALE, max(MIN_SCALE, self.scale + delta))
        self.apply_scale()

    def on_resize(self, event):
        """Keep the message line wrapping to the window's actual width."""
        if event.widget is self.root:
            self.output["message"].config(
                wraplength=max(240, event.width - 60))

    def on_compute(self):
        """Validate all three inputs, compute, and show result or error."""
        self.output["result"].config(text="")
        self.output["message"].config(text="")
        try:
            a = parse_real(self.entries["a"].get(), "a")
            b = parse_real(self.entries["b"].get(), "b")
            x = parse_real(self.entries["x"].get(), "x")
            value = compute_f5(a, b, x)
        except F5Error as error:
            # The word "Error" carries the distinction from a result, so
            # it does not rest on the red colour alone (WCAG 1.4.1).
            self.output["message"].config(text="Error:  " + str(error))
            return
        self.output["result"].config(text="f(x) = " + repr(value))

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
        self.output["result"].config(text="")
        self.output["message"].config(
            text="Internal fault: a defect in the calculator, not a "
                 "problem with your input. Details have been written to "
                 "the terminal. Corrective action: press Clear and "
                 "continue; report the traceback if it recurs.")

    def on_clear(self):
        """Empty every field and both output lines."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.output["result"].config(text="")
        self.output["message"].config(text="")
        self.entries["a"].focus_set()


def main():
    """Open the calculator window and run the Tkinter event loop."""
    root = tk.Tk()
    F5App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
