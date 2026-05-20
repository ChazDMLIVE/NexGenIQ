# Contributing to NexGenIQ

NexGenIQ is open-source software for beef-cattle selection-index and
herd-simulation analysis. Contributions — from quantitative geneticists,
breeders, and developers alike — are welcome.

## Project layout

```
engine/    osit-index — the selection-index numerical engine (Python)
sim/       osit-sim   — the herd-simulation engine (Python)
backend/   the FastAPI backend and REST API (Python)
frontend/  the React + TypeScript web application
docs/      the planning documents (Phases 1-3.5)
```

## Setting up for development

Requires Python 3.10+ and Node 18+.

```bash
# Install both engines (editable, so changes are picked up live).
cd engine && pip install -e . && cd ..
cd sim    && pip install -e . && cd ..

# Backend.
cd backend
pip install -r requirements.txt
cp .env.example .env          # then edit .env if needed
uvicorn app.main:app --reload

# Frontend (in a second terminal).
cd frontend
npm install
npm run dev
```

## Running the tests

Every change should keep the test suites green:

```bash
cd engine   && python -m pytest tests/    # selection-index engine
cd sim      && python -m pytest tests/    # herd-simulation engine
cd backend  && python -m pytest tests/    # API integration tests
cd frontend && npm run build              # type-check + bundle
```

## Standards

- **Correctness first.** NexGenIQ informs real breeding decisions. Any
  change to a calculation must be accompanied by a test, ideally one that
  checks the result against a hand-worked value or a published figure.
- **Document as you go.** Functions and modules carry docstrings; the
  reasoning behind a non-obvious choice belongs in a comment.
- **Reference data is versioned.** Genetic parameters and across-breed
  factors live as versioned data files (`engine/osit_index/data/`), never
  as hard-coded constants. Cite the source of any value you add.
- **Keep the engines web-free.** `osit-index` and `osit-sim` must not
  import anything web-related; they are standalone, testable libraries.

## Submitting a change

1. Fork the repository and create a branch for your change.
2. Make the change, with tests, keeping all suites green.
3. Open a pull request describing what changed and why.

By contributing you agree your contribution is licensed under the
project's Apache License 2.0.

## Reporting issues

Bug reports and feature requests are welcome via the GitHub issue tracker.
For a calculation that looks wrong, please include the inputs and the
result you expected — that makes it far easier to verify and fix.
