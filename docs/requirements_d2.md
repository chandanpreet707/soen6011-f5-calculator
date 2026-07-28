# F5 Calculator — Updated Requirements (D2 / Problem 7)

SOEN 6011, Summer 2026. Student ID: 40324569. Function F5: f(x) = a·b^x.

This list supersedes the D1/Problem 2 requirements. It is updated from the
D2/Problem 5 implementation and from the D1 marker feedback. Style is
unchanged from D1: ISO/IEC/IEEE 29148 construct **[Condition] [Subject]
shall [Action] [Object] [Constraint]**, active voice, one capability per
requirement, each with a unique identifier and a uniquely identified
source.

**Identifiers are stable.** Every identifier that existed in D1 means in D2
exactly what it meant in D1. New behaviour receives a new identifier;
nothing is renumbered, so a D1 trace still resolves correctly against this
document.

## Change summary

| Change | Reason |
|---|---|
| Persona elements given unique IDs (G-, N-, PP-, PL-) | D1 feedback: tags like "Goals" and "Pain Point 1" were not unique trace identifiers |
| Project-description sources given unique IDs (PD-) | Same reason: "project description" is free text, not an identifier |
| FR-07, FR-08, FR-09 added (malformed, empty, non-finite input) | D1 feedback: no requirement for rejecting malformed / NaN / infinity / empty input |
| FR-10 added (quit) | D1 feedback: the quit operation was shown but never specified |
| NFR-04 added (convergence) | D1 feedback: an iteration-limit failure was reported as an overflow. Non-convergence and numeric overflow are now separate requirements (NFR-04 and NFR-02) served by separate exception classes |
| NFR-02 unchanged in wording, now enforced | D2 defect audit: results outside the representable range were returned as `inf` or `0.0` instead of reported, so NFR-02 was unmet in D1 |
| FR-05 trace corrected | D1 feedback: FR-05 traced to "Completeness", not to the persona |
| FR-06 rewording | The interface is now graphical; there are no prompts |
| DC-01 revised; DC-02, DC-03 added | D2/Problem 5: GUI replaces the textual interface; from-scratch and platform constraints made explicit |

## Sources

### Persona elements (D1/Problem 1, Élodie Tremblay)

Goals: **G-01** evaluate a·b^x repeatedly for many (a,b,x) in one session;
**G-02** obtain at least 6 significant digits; **G-03** understand why an
input is rejected.

Needs: **N-01** clearly labelled inputs; **N-02** precise results;
**N-03** fast repeated evaluation without restarting; **N-04** guidance on
valid input ranges.

Pain points: **PP-01** generic tools emit unhelpful errors for b<0 with
non-integer x; **PP-02** no indication of the valid domain of a, b, x;
**PP-03** overflow ends the tool with no explanation.

Platform: **PL-01** university-managed Windows laptop, no administrative
rights, must run without installing an IDE.

### Project description

**PD-01** implement from scratch; **PD-02** graphical user interface using
Tkinter; **PD-03** no dependence on an IDE; **PD-04** support for handling
exceptions; **PD-05** error messages helpful to users.

## Assumptions

- **A1** a, b, x are user-entered per evaluation, in decimal notation.
- **A2** Exponents are considered rational; to guarantee real results,
  non-integer exponents are rejected when b < 0 (confirmed with the
  instructor, D1).
- **A3** Only the principal real value of a·b^x is computed.
- **A4** Language of interaction is English.
- **A5** One user interacts at a time.

## Functional requirements

- **FR-01** The F5 Calculator shall accept real values of a, b, and x in
  decimal notation. [Trace: G-01, N-01]
- **FR-02** When b > 0, the F5 Calculator shall compute f(x) = a·b^x for any
  real x. [Trace: G-01]
- **FR-03** When b = 0 and x ≤ 0, the F5 Calculator shall reject the input
  and display the cause and a corrective action. [Trace: PP-02, G-03]
- **FR-04** When b < 0 and x is not an integer, the F5 Calculator shall
  reject the input and display the valid domain of x for a negative base.
  [Trace: PP-01, N-04, G-03]
- **FR-05** When b < 0 and x is an integer, the F5 Calculator shall compute
  f(x) = a·b^x with the correct sign. [Trace: PP-01, G-01 — see note 1]
- **FR-06** Upon displaying a result, the F5 Calculator shall accept new
  values of a, b, and x without requiring a restart. [Trace: N-03]
  *(D1 wording said "prompt"; a graphical interface has no prompts.)*
- **FR-07** When an entry is not a number in decimal notation, the F5
  Calculator shall reject the input and display the cause and a corrective
  action. [Trace: G-03, PP-02, N-04]  *(new)*
- **FR-08** When an entry field is empty, the F5 Calculator shall reject the
  input and display the cause and a corrective action.
  [Trace: G-03, N-01]  *(new)*
- **FR-09** When an entry is an infinite or not-a-number value, the F5
  Calculator shall reject the input and display the cause and a corrective
  action. [Trace: G-03, PP-03]  *(new)*
- **FR-10** When the user activates the Quit control, the F5 Calculator
  shall close the application window and end the session.
  [Trace: N-03 — see note 2]  *(new; demonstrated in D1, previously
  unspecified)*

## Non-functional requirements

- **NFR-01** The F5 Calculator shall compute results accurate to at least 6
  significant digits. [Trace: G-02, N-02]
- **NFR-02** When a computation exceeds the representable numeric range, the
  F5 Calculator shall display a message stating the cause, without
  terminating. [Trace: PP-03]  *(D1 wording unchanged; now enforced by
  `RangeError` for overflow and underflow alike)*
- **NFR-03** Each error message shall state the cause of the error and a
  corrective action. [Trace: PP-01, G-03, PD-05]  *(D1, unchanged)*
- **NFR-04** When a series fails to converge within its iteration limit, the
  F5 Calculator shall report a convergence error without terminating.
  [Trace: PP-03, PD-04]  *(new)*

## Design constraints

- **DC-01** The F5 Calculator shall provide a graphical user interface
  implemented with Tkinter. [Trace: PD-02]  *(revised from the D1 textual
  interface)*
- **DC-02** The F5 Calculator shall run on a standard Python installation
  without administrative rights, an IDE, or third-party packages.
  [Trace: PL-01, PD-03]  *(new)*
- **DC-03** The implementation shall use no built-in or library functions
  beyond those for input, output, arithmetic, and user-interface design.
  [Trace: PD-01]  *(new)*

## Notes on traces without a direct persona need

**Note 1 — FR-05.** FR-05 makes the function total over its real domain. It
is induced by PP-01 (the persona meets unhelpful errors around negative
bases) and serves G-01, but it exists primarily for mathematical
completeness. It is recorded as such rather than being attached to an
invented persona need. This corrects the D1 trace, which read
"Completeness" and cited no source at all.

**Note 2 — FR-10.** An explicit exit is a usability requirement rather than
a stated persona need. It is traced to N-03, since the persona works in
time-boxed sessions and repeats evaluations, and is flagged here so the
weaker link is visible rather than disguised.

## Traceability check

Every requirement cites at least one uniquely identified source, and every
source induces at least one requirement.

| Source | Requirements |
|---|---|
| G-01 | FR-01, FR-02, FR-05 |
| G-02 | NFR-01 |
| G-03 | FR-03, FR-04, FR-07, FR-08, FR-09, NFR-03 |
| N-01 | FR-01, FR-08 |
| N-02 | NFR-01 |
| N-03 | FR-06, FR-10 |
| N-04 | FR-04, FR-07 |
| PP-01 | FR-04, FR-05, NFR-03 |
| PP-02 | FR-03, FR-07 |
| PP-03 | FR-09, NFR-02, NFR-04 |
| PL-01 | DC-02 |
| PD-01 | DC-03 |
| PD-02 | DC-01 |
| PD-03 | DC-02 |
| PD-04 | NFR-04 |
| PD-05 | NFR-03 |

No requirement is left without a source, and no source is left without a
requirement.

## Where each requirement is realised in the code

| Requirement | Location |
|---|---|
| FR-01, FR-07, FR-08, FR-09 | `f5_gui.parse_real` |
| FR-02, FR-03, FR-04, FR-05 | `f5_core.compute_f5` |
| FR-06, FR-10 | `f5_gui.F5App` |
| NFR-01 | `f5_math.EPSILON`; evidenced by `verify_f5.py` |
| NFR-02 | `f5_core.compute_f5` range check, `f5_errors.RangeError` |
| NFR-03 | `f5_errors.F5Error.__init__` |
| NFR-04 | `f5_math.MAX_ITER`, `f5_errors.ConvergenceError` |
| DC-01, DC-02 | `f5_gui` |
| DC-03 | `f5_math` |