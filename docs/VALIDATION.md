# NexGenIQ Engine Validation

This document records how the NexGenIQ selection-index engine
(`osit-index`) is validated — that is, how it is shown to compute the
*correct* result, not merely a self-consistent one. It is intended to be
citable in published work that uses NexGenIQ.

Validation here means checking the engine's output against an
independently derived reference. The references used are exact published
equations, so agreement to numerical tolerance demonstrates that the
engine implements the published method correctly — for any inputs, not a
single example.

The checks described below are also implemented as automated tests
(`engine/tests/test_validation_reference.py`) that run with every build,
so the engine cannot regress away from these reference results unnoticed.

---

## 1. The selection-index weight solver

### Method under test

NexGenIQ constructs an economic selection index by solving the
Smith (1936) / Hazel (1943) selection-index equations

> **P b = G a**

for the index weights **b**, where **P** is the variance–covariance
matrix of the information sources (the EPDs), **G** is the covariance
matrix between the information sources and the breeding-goal traits, and
**a** is the vector of economic values. The engine solves this system by
Cholesky factorisation of **P**.

### Reference

For two traits the selection-index equations are a 2×2 linear system with
an exact algebraic (closed-form) solution. Writing
**P** = [[p₁₁, p₁₂], [p₁₂, p₂₂]] and **w** = **G a** = [w₁, w₂],
Cramer's rule gives

> det = p₁₁p₂₂ − p₁₂²
> b₁ = (w₁p₂₂ − w₂p₁₂) / det
> b₂ = (w₂p₁₁ − w₁p₁₂) / det

This closed form is the algebraic solution of Hazel's (1943) index
equations and is used as the independent reference.

### Result

The engine's general solver was run on a set of two-trait scenarios
spanning uncorrelated traits, positively and negatively correlated
traits, a negative economic weight, and strongly asymmetric trait scales.
In every case the engine's index weights matched the closed-form solution
to a relative tolerance of 1×10⁻¹⁰ (effectively machine precision).

Worked illustration — with **P** = diag(100, 400), **G** = diag(40, 160),
**a** = (1, 1), the equations decouple and each weight is
bₖ = Gₖₖaₖ / Pₖₖ:

| | by hand | NexGenIQ |
|---|---|---|
| b₁ | 40 × 1 / 100 = 0.400000 | 0.400000 |
| b₂ | 160 × 1 / 400 = 0.400000 | 0.400000 |

A representative correlated case — **P** = [[100, 30], [30, 400]],
**G** = [[40, 12], [18, 160]], **a** = (2, 1):

| | closed form | NexGenIQ |
|---|---|---|
| b₁ | 0.790793 | 0.790793 |
| b₂ | 0.430691 | 0.430691 |

In addition, the returned **b** was confirmed to satisfy **P b = G a**
exactly for every case (the defining property of the solution), and a
three-trait case was checked against an independent linear solve, again
agreeing to machine tolerance.

**Conclusion.** The selection-index solver correctly implements the
published selection-index equations.

---

## 2. BIF accuracy / reliability conversions

### Method under test

NexGenIQ converts between Beef Improvement Federation (BIF) accuracy and
reliability when propagating EPD uncertainty into index confidence
intervals.

### Reference

The BIF defines accuracy as

> BIF accuracy = 1 − √(1 − reliability)

equivalently reliability = 1 − (1 − BIF accuracy)². The engine's
conversions were checked against eleven exact points on this definition,
from 0.00 to 1.00.

### Result

`bif_accuracy_to_reliability` and `reliability_to_bif_accuracy` reproduced
every published table point to a tolerance of 1×10⁻¹⁰, and a
round-trip (accuracy → reliability → accuracy) returned the original
value across the full 0–1 range.

| BIF accuracy | reliability (published) | NexGenIQ |
|---|---|---|
| 0.30 | 0.51 | 0.51 |
| 0.50 | 0.75 | 0.75 |
| 0.70 | 0.91 | 0.91 |
| 0.90 | 0.99 | 0.99 |

**Conclusion.** The accuracy conversions correctly implement the
published BIF definition.

---

## 3. Scope and limitations

This document validates the **selection-index engine** (`osit-index`):
the index-weight solver and the accuracy conversions. These are the
deterministic, analytically-grounded parts of NexGenIQ, and they are
validated against exact published equations.

The **herd-simulation engine** (`osit-sim`) is a stochastic bio-economic
model. Unlike the index equations it has no single published "correct
answer" — different bio-economic models legitimately produce different
economic values because they encode different production assumptions.
The simulation is therefore *not* validated against a single reference.
Instead it is checked for **face validity**: its economic-sign sanity
tests confirm every derived economic value carries the sign breeding
economics predicts (e.g. mature cow weight negative in a cow-calf
system; calving ease, stayability and heifer pregnancy positive; carcass
traits positive on a grid endpoint), and its outputs respond sensibly to
its inputs. Users should treat the simulation's economic values as a
modelled estimate for the operation described, calibrated to the
producer's own prices and rates, rather than as a validated constant.

---

## References

Beef Improvement Federation. 2021. Guidelines for Uniform Beef
Improvement Programs. 10th ed. Beef Improvement Federation.

Hazel, L. N. 1943. The genetic basis for constructing selection indexes.
Genetics 28:476–490.

Smith, H. F. 1936. A discriminant function for plant selection.
Annals of Eugenics 7:240–250.

---

*Validation tests: `engine/tests/test_validation_reference.py`. This
document is regenerated when the engine's validated behaviour changes.*
