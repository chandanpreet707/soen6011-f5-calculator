"""Unit tests for the F5 calculator.

SOEN 6011, Summer 2026, Deliverable 3, Problem 8. Student ID: 40324569.

One test module per source module. Run from the repository root:

    python3 -m unittest discover -v

The suite uses unittest (PyUnit) from the standard library, and the
decimal module as a high-precision oracle in the accuracy tests. Both
are test infrastructure, not calculator code: DC-03 constrains the
implementation of ab^x, which remains from scratch in f5_math and
f5_core, exactly as it constrains verify_f5.py and tools/.
"""
