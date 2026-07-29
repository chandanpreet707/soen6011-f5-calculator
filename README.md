# F5 Calculator — f(x) = a · b^x

A scientific calculator for the function f(x) = a·b^x over the real
numbers, implemented from first principles for SOEN 6011 (Software
Engineering Processes), Summer 2026.

Student ID: 40324569. Function: F5.

Repository: https://github.com/chandanpreet707/soen6011-f5-calculator

## What it does

Evaluates a·b^x for real a, b, and x, including negative and fractional
exponents, with input validation and helpful error messages. The
computation uses no mathematics library: the exponential, logarithm, and
integer power are all implemented from scratch (Deliverable 2 constraint).

## Requirements

- Python 3 (any recent 3.x). No third-party packages.
- Tkinter, which ships with the standard CPython installer. On some Linux
  distributions it is a separate system package (for example
  `sudo apt install python3-tk`).

No IDE and no build step are needed.

## Running

Graphical interface:

    python3 f5_gui.py

Enter values for a, b, and x, then press Compute (or the Return key).
Use Quit to exit.

Reproduce the accuracy evidence from the command line:

    python3 verify_f5.py

## Example

    a = 100, b = 1.4, x = 3.5   ->   f(x) = 324.67445849645827
    a = 1,   b = -2,  x = 3     ->   f(x) = -8.0
    a = 1,   b = -2,  x = 0.5   ->   rejected: a negative base with a
                                     non-integer exponent has no real value

## How it works

For b > 0, b^x is computed through the identity b^x = e^(x·ln b). The
exponent is split as x = n + f with n whole and f in [0, 1); the whole
part is computed exactly and only the small fractional part goes through
a series, which keeps the error low (Algorithm B).

Subordinate functions, all from scratch:

| Function | Method |
|---|---|
| `absolute`  | sign test |
| `floor_int` | floor division, which rounds toward minus infinity |
| `pow_int`   | exponentiation by squaring, exact for integer powers |
| `ln`        | atanh series with range reduction b = m·2^p, m in [1,2) |
| `exp`       | Maclaurin series; negative arguments via e^y = 1/e^(-y) |

The four factors of the answer (`a`, the two halves of the integer power,
and the fractional factor) are multiplied in an order that keeps the
running product near 1. Multiplication is associative in mathematics but
not in floating point: computing `b**x` first and multiplying by `a`
afterwards can overflow on the way to an answer that is perfectly
representable, and passing through the subnormal range destroys most of
the significant digits. Ordering the multiplications removes both
failures, and on some inputs makes this implementation more accurate than
the expression `a * b**x`, which loses the digits in the intermediate
before `a` is ever applied.

Accuracy: worst relative error 4.6 × 10⁻¹¹ over the ten verification
cases, and 5.2 × 10⁻¹¹ over 120,000 randomly sampled inputs, against a
six-significant-digit target. `verify_f5.py` also checks six inputs that
must be *rejected*, four compensated-scale results that are reachable only
through a range-safe order of multiplication, and a forced convergence
failure, so every requirement is evidenced rather than asserted.

## Project layout

    f5_math.py     five from-scratch subordinate functions
    f5_errors.py   custom exception hierarchy (F5Error and children)
    f5_core.py     compute_f5, Algorithm B with the domain rules
    f5_gui.py      Tkinter interface with input validation
    verify_f5.py   accuracy, rejection, range-safety and convergence checks
    docs/          requirements and per-function flowcharts

## Error handling

Errors use a small custom hierarchy so the interface can show a cause and
a corrective action rather than crashing:

- `InputError` — an entry is empty, not a decimal number, or not finite
- `DomainError` — input outside the real domain of a·b^x
- `ConvergenceError` — a series exceeded its iteration limit
- `RangeError` — a result too large or small to represent
- `AlgorithmRangeError` — the result is representable, but an
  intermediate value of the algorithm is not

`F5Error` is the common base and is never raised directly, so a single
`except F5Error` catches every calculator error.

## Accuracy scope

The six-significant-digit guarantee applies to every finite, nonzero
result in the normal representable range, of magnitude at least
2.2 × 10⁻³⁰⁸. Subnormal results are excluded because no uniform
six-digit bound is guaranteed across that whole range: precision degrades
gradually, so a subnormal near the normal boundary still carries well over
six digits while one near zero carries almost none.

Where even half of the integer power `|b|^(n/2)` leaves the representable
range, no ordering of the factors can recover it. The exact result may
still be representable, so the calculator raises `AlgorithmRangeError`
rather than claiming an overflow or underflow that did not occur. It
returns no value in that corner, but it never returns a wrong one, and it
never misdescribes why.

## Domain rules

- b > 0: any real x.
- b = 0: valid only for x > 0 (result 0); x ≤ 0 is undefined.
- b < 0: valid only when x is an integer; the sign follows the parity of x.

## License

Coursework for SOEN 6011; not licensed for reuse.