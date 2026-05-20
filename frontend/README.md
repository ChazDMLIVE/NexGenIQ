# NexGenIQ frontend

The NexGenIQ web application — the Index Builder, in the Graphite + Sage
design system of the Phase 3.5 UI/UX specification.

Built with React + TypeScript + Vite.

## Running it

The frontend talks to the FastAPI backend, so start the backend first
(see `../backend/README` or the project README).

```bash
npm install
npm run dev
```

The app is then at `http://localhost:5173`. The Vite dev server proxies
`/api` to the backend on port 8000, so no CORS configuration is needed in
development.

## Building for production

```bash
npm run build      # type-checks, then bundles into dist/
npm run preview    # serve the production build locally
```

## Layout

```
src/
  main.tsx              Entry point.
  App.tsx               App shell — auth state, top bar, routing.
  lib/
    api.ts              Typed client for the backend REST API.
    help.ts             Help content for the three-layer help system.
  components/
    Help.tsx            InfoTip + ContextPanel (the explanation system).
    UI.tsx              Shared primitives — Button, Card, Field, Stepper…
    builder/
      GoalStep.tsx      Index Builder step 1 — the breeding goal.
      AnimalsStep.tsx   Index Builder step 3 — CSV import + manual entry.
  pages/
    AuthScreen.tsx      Sign in / register.
    IndexBuilder.tsx    The four-step Index Builder wizard.
    ResultsWorkspace.tsx  The ranked-results payoff screen.
    Troubleshooting.tsx The dedicated troubleshooting page.
  styles/
    tokens.css          The Graphite + Sage design tokens.
    app.css             All component styles.
```

## Design system

Every screen is built from the design tokens in `styles/tokens.css` —
the Graphite + Sage palette, the type scale, the 8px spacing scale. The
three-layer help system (tooltip → context panel → glossary) is in
`components/Help.tsx`; every control carries an `InfoTip`.
