# osit-sim

The NexGenIQ whole-herd bio-economic simulation engine.

`osit-sim` is the second computational engine of NexGenIQ. It simulates a
beef cow-calf enterprise stochastically — year by year and animal by
animal — and derives the **marginal economic value (MEV)** of each trait
by finite-difference perturbation of the simulated profit function.

The MEV vector it produces is exactly the economic-weight input the
`osit-index` engine consumes — that shared interface is the integration
seam of the two engines. A user can run the full pipeline (describe the
production system → derive economic values → build an index → rank
animals) or use either engine standalone.

## How it works

1. **Initialise** a cow herd with a breed-composition mix and an age
   distribution.
2. **Burn in** for a number of years so the cow age structure stabilises.
3. **Annual cycle**, repeated over the planning horizon: mate the cows,
   simulate conception (modulated by heifer-pregnancy genetics), calving
   (modulated by calving-ease genetics), grow each calf to the sale
   endpoint, account for revenue and cost, cull cows (modulated by
   stayability genetics) and rear replacements.
4. **Accumulate** discounted net return into a net-present profit.
5. **Derive MEVs**: perturb one trait's genetic mean up and down, re-run
   the simulation sharing the baseline's RNG seed (common random numbers),
   and take the central finite difference as the trait's economic value —
   averaged over replicate herds, with a Monte-Carlo standard error.

## Methodology

See NexGenIQ Phase 3 Part 3B Section 2.5. The approach follows the
documented bio-economic selection-index methodology: the economic value
of a trait is the partial derivative of profit with respect to its genetic
mean, estimated numerically from a whole-herd simulation.

The derived MEVs are economically sane by construction and are guarded by
explicit sign tests: weaning weight is positively valued at a realistic
per-pound figure, mature cow weight is negatively valued (bigger cows cost
more to maintain), and fertility and longevity traits — calving ease,
heifer pregnancy, stayability — are all positively valued.

## Running it

```bash
pip install -e .                  # install the engine
python -m pytest tests/           # 20 tests
```

## Layout

```
osit_sim/
  inputs.py      ProductionSystem, EconomicScenario, SimulationControls.
  genetics.py    Per-trait genetics, breed effects, F1 heterosis.
  herd.py        The stochastic whole-herd simulation core.
  economics.py   Revenue by sale endpoint; size-dependent herd costs.
  mev.py         Finite-difference MEV derivation with common random numbers.
tests/           20 tests, including economic-sign sanity checks.
```

## Licence

Apache License 2.0.
