# Changelog

All notable changes to the F5 Calculator. This project adheres to
Semantic Versioning (https://semver.org): MAJOR for incompatible
changes to the public behaviour, MINOR for backwards-compatible
additions, PATCH for backwards-compatible fixes.

## [3.0.0] - 2026-08 - Deliverable 3

### Changed (breaking)
- The graphical interface no longer converts unexpected faults into a
  generic message. Only F5Error is caught; anything else is reported
  with a full traceback. Callers that relied on every fault producing
  a handled message must change.
- The series tolerance moved from 1e-12 to 1e-17, which changes the
  value returned for extreme bases. Worst sampled relative error over
  200,000 log-uniform samples: 8.98e-10 -> 2.05e-13.

### Added
- A PyUnit suite of 84 tests, one module per source module. 21 of them
  fail against 2.0.0.
- tools/fuzz_accuracy.py, a seeded sampler measured against a 60-digit
  decimal oracle.
- tools/defect_probe.py, which stages the tolerance defect for pdb.
- InputError is now chained from the underlying ValueError.

### Fixed
- ln(2) carried 1.03e-12 of absolute error, which range reduction
  multiplied by p (up to 934) and exp converted into relative error.
- Two stale iteration counts reported by verify_f5.py.
- All Flake8 violations and all Pylint messages.

## [2.0.0] - 2026-07 - Deliverable 2

### Changed (breaking)
- Textual interface replaced by a Tkinter graphical interface.
- Custom exception hierarchy replaces built-in OverflowError.

### Added
- Range reduction in ln, supporting bases to 1e+/-15 and beyond.
- Reciprocal form of exp, removing catastrophic cancellation.
- Range-safe ordering of the four multiplicative factors.
- AlgorithmRangeError, distinguishing an unformable intermediate from
  a genuinely unrepresentable result.

## [1.0.0] - 2026-06 - Deliverable 1

### Added
- First implementation of f(x) = a * b^x by Algorithm B, with a
  textual interface.
