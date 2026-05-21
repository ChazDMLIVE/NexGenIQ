# NexGenIQ

An open-source selection-index and herd-simulation platform for beef cattle.

NexGenIQ helps academic researchers, quantitative geneticists, commercial
cattle producers, seedstock breeders, and breed associations build
economically optimal selection indexes and rank breeding animals — with an
interface designed to be usable by anyone, regardless of background.

It is built on established bio-economic selection-index methodology as a genuinely open,
modern, multi-breed alternative. See the `docs/` planning documents for the
full background (genetics theory, comparable-software analysis, technical
specification, and UI/UX design).

## Project status

NexGenIQ is under active development. **Milestone 1 — the Index Builder —**
is in progress:

| Component | Status |
|-----------|--------|
| `osit-index` numerical engine | Complete — 57 passing tests |
| `osit-sim` herd-simulation engine | Complete — 20 passing tests |
| FastAPI backend + REST API | Complete — 18 passing tests |
| React frontend (Index Builder + Simulation) | Complete — builds clean, verified end-to-end |

Both milestones are complete. NexGenIQ is a runnable, integrated web
application: a user can describe their production system, have NexGenIQ
**simulate the herd and derive the economic value of each trait**, carry
those values straight into the **Index Builder**, import or enter animals,
and get a ranked, explained, stress-tested result. Either engine can also
be used standalone. 95 automated tests pass across the project.

## Repository layout

```
NextGenIQ/
  engine/         The osit-index selection-index engine (Python package).
    osit_index/   Selection-index math: P/G matrices, the b = P^-1 G a
                  solver, across-breed adjustment, scoring, sensitivity.
    tests/        57 tests, including numerical-validation tests.
  sim/            The osit-sim herd-simulation engine (Python package).
    osit_sim/     Stochastic whole-herd simulation; MEV derivation by
                  finite difference with common random numbers.
    tests/        20 tests, including economic-sign sanity checks.
  backend/        The FastAPI backend.
    app/          API, data model, services, the engine bridges.
    tests/        18 API integration tests.
  frontend/       The React + TypeScript web application.
    src/          Index Builder + Herd Simulation wizards, results,
                  the layered help system, troubleshooting.
  docs/           Phase 1-3.5 planning documents.
```

## Running it locally

Requires Python 3.10+ and Node 18+.

```bash
# 1. Install both engines (editable).
cd engine && pip install -e . && cd ..
cd sim    && pip install -e . && cd ..

# 2. Install and run the backend.
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload          # API at http://localhost:8000

# 3. In a second terminal, install and run the frontend.
cd frontend
npm install
npm run dev                            # app at http://localhost:5173
```

Open `http://localhost:5173` and create an account. Interactive API
documentation is at `http://localhost:8000/docs`.

## Running the tests

```bash
cd engine   && python -m pytest tests/     # 57 index-engine tests
cd sim      && python -m pytest tests/     # 20 simulation-engine tests
cd backend  && python -m pytest tests/     # 18 API integration tests
cd frontend && npm run build               # type-check + bundle
```

## Reference data

NexGenIQ ships authoritative reference data as versioned files
(`engine/osit_index/data/`). The across-breed adjustment factors are the
**official USDA/USMARC January 2026 table** — all eighteen breeds, the
current release; the previous (2024) table is retained for reproducibility.
The genetic parameters are a cited literature-consensus set; researchers
can override them with population-specific estimates. Every run records
which data version it used, and the API exposes the versions at
`GET /api/v1/library/data-versions`. See `engine/osit_index/data/README.md`.

## What the engine does

Given a breeding goal (traits + economic weights), genetic parameters, and
a set of candidate animals with EPDs, NexGenIQ:

1. puts multi-breed EPDs on a common base via USMARC/BIF across-breed
   adjustment factors;
2. constructs the selection index — either the transparent economic-weight
   index or the full BLUP index that solves `b = P^-1 G a`;
3. ranks the animals, with an accuracy-aware confidence interval on every
   index value;
4. explains, in plain language, *why* each animal ranks where it does;
5. runs sensitivity analysis to show how robust the ranking is.

Every run is recorded in a reproducibility ledger.

## Licence

Licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file. The
[NOTICE](NOTICE) file records the copyright holder (Chase Markel) and a
suggested citation for use in published research. Built for an open,
reproducible, community-contributable public repository.
