# F5 Calculator — Updated Requirements (D2 / Problem 7)

SOEN 6011, Summer 2026. Student ID: 40324569. Function F5: f(x) = a·b^x.

This list updates the D1/Problem 2 requirements based on the D2/Problem 5
implementation and on the D1 marker feedback. Style is unchanged from D1:
ISO/IEC/IEEE 29148 construct **[Condition] [Subject] shall [Action]
[Object] [Constraint]**, active voice, one capability per requirement,
each with a unique identifier and a unique persona trace.

## Change summary

| Change | Reason |
|---|---|
| Persona elements given unique IDs (PP-, G-, N-, PL-) | D1 feedback: tags like "Goals" and "Pain Point 1" were not unique trace identifiers |
| FR-07, FR-08, FR-09 added (malformed, empty, non-finite input) | D1 feedback: no requirement for rejecting malformed / NaN / infinity / empty input |
| FR-10 added (quit) | D1 feedback: the quit operation was shown but never specified |
| DC-01 revised to Tkinter GUI | D2/Problem 5: GUI replaces the textual interface |
| DC-02, DC-03 added (install-free run; from-scratch) | Persona platform PL-01; project description |
| NFR-02 split into convergence vs range | D1 feedback: iteration-limit failure was conflated with numeric overflow |
| FR-05 trace corrected | D1 feedback: FR-05 traced to "Completeness," not the persona |

## Persona elements (now uniquely identified)

Goals: **G-01** evaluate a·b^x repeatedly for many (a,b,x); **G-02** obtain
at least 6 significant digits; **G-03** understand why an input is rejected.

Needs: **N-01** clear input prompts; **N-02** precise results; **N-03** fast
repeated evaluation; **N-04** guidance on valid input ranges.

Pain points: **PP-01** generic tools emit unhelpful errors for b<0 with
non-integer x; **PP-02** no indication of valid domains; **PP-03** overflow
terminates the tool without explanation.

Platform: **PL-01** university-managed Windows laptop, no admin rights,
must run without installing an IDE.

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
  decimal notation. [Trace: G-01]
- **FR-02** When b > 0, the F5 Calculator shall compute f(x) = a·b^x for any
  real x. [Trace: G-01]
- **FR-03** When b = 0 and x ≤ 0, the F5 Calculator shall reject the input
  and state the cause. [Trace: PP-02]
- **FR-04** When b < 0 and x is not an integer, the F5 Calculator shall
  reject the input and display the valid domain of x for a negative base.
  [Trace: PP-01]
- **FR-05** When b < 0 and x is an integer, the F5 Calculator shall compute
  a·b^x with the correct sign. [Trace: G-01; see note below on completeness]
- **FR-06** Upon displaying a result, the F5 Calculator shall prompt for a
  new evaluation without requiring a restart. [Trace: N-03]
- **FR-07** When an entry is not a number in decimal notation, the F5
  Calculator shall reject it and state the cause and a corrective action.
  [Trace: PP-02, N-04]  *(new)*
- **FR-08** When an entry is empty, the F5 Calculator shall reject it and
  request a value. [Trace: N-01]  *(new)*
- **FR-09** When an entry is a non-finite value (NaN or infinity), the F5
  Calculator shall reject it and state the cause. [Trace: PP-02]  *(new)*
- **FR-10** The F5 Calculator shall provide an explicit operation to exit
  the program. [Trace: N-01]  *(new; was shown but unspecified in D1)*

**Note on FR-05.** FR-05 exists to make the function total over its real
domain, so it traces to goal G-01 (evaluate a·b^x for the combinations the
persona uses) rather than to a specific pain point. Requirements that exist
for mathematical completeness rather than a persona need are marked as such
explicitly, correcting the D1 inconsistency.

## Non-functional requirements

- **NFR-01** The F5 Calculator shall compute results accurate to at least 6
  significant digits. [Trace: G-02, N-02]
- **NFR-02** When a series does not converge within its iteration limit, the
  F5 Calculator shall report a convergence error without terminating.
  [Trace: PP-03]  *(split from D1 NFR-02)*
- **NFR-03** When a result exceeds the representable numeric range
  (overflow or underflow), the F5 Calculator shall report a range error
  without terminating. [Trace: PP-03]  *(split from D1 NFR-02)*
- **NFR-04** Each error message shall state the cause of the error and a
  corrective action. [Trace: PP-01, G-03]

## Design constraints

- **DC-01** The F5 Calculator shall provide a graphical user interface
  implemented with Tkinter. [Trace: project description D2]
  *(revised from D1 textual interface)*
- **DC-02** The F5 Calculator shall run on a standard Python installation
  without administrative rights, an IDE, or third-party packages.
  [Trace: PL-01; project description D2]  *(new)*
- **DC-03** The implementation shall use no built-in or library functions
  beyond input, output, arithmetic, and user-interface design.
  [Trace: project description D2]  *(new)*

## Traceability check

Every requirement traces to a uniquely identified persona element or to a
stated project constraint. Every persona element induces at least one
requirement: G-01→FR-01,02,05; G-02→NFR-01; G-03→NFR-04; N-01→FR-08,10;
N-02→NFR-01; N-03→FR-06; N-04→FR-07; PP-01→FR-04,NFR-04; PP-02→FR-03,07,09;
PP-03→NFR-02,03; PL-01→DC-02.