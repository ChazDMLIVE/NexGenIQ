/*
 * The Index Builder — the centrepiece of NexGenIQ Milestone 1.
 *
 * A four-step wizard (define goal -> genetic parameters -> add animals ->
 * review) followed by the results workspace, implementing Phase 3.5
 * Part 4. The four steps share state, so they live in one component; each
 * step's body is a focused sub-component below.
 */

// The Index Builder — accepts a simulation-derived goal as a starting point.
import { useEffect, useState } from "react";
import {
  api,
  type Animal,
  type GoalComponent,
  type IndexBuildResponse,
  type Trait,
} from "../lib/api";
import type { DerivedGoal } from "../App";
import { Button, Card, Field, Stepper } from "../components/UI";
import { ContextPanel } from "../components/Help";
import { GoalStep } from "../components/builder/GoalStep";
import { AnimalsStep } from "../components/builder/AnimalsStep";
import { PhenotypeStep } from "../components/builder/PhenotypeStep";
import { ResultsWorkspace } from "./ResultsWorkspace";

const STEPS = ["Goal", "Parameters", "Animals", "Results"];

/* A goal template — a starting set of traits + economic weights, so a
 * first-time user is never faced with an empty grid (Phase 3.5 4.1). */
interface GoalTemplate {
  id: string;
  name: string;
  desc: string;
  basis: string;
  components: GoalComponent[];
}

/* The goal pre-loaded when a user first opens the Index Builder. It uses
 * exactly the traits in the downloadable CSV column template (WW, YW, BW,
 * CED, STAY, MILK, MARB, REA), so a first-time user who builds their file
 * from that template has a goal that matches it. The named TEMPLATES
 * below are advanced presets and may use other traits. */
const DEFAULT_GOAL: GoalComponent[] = [
  { trait_code: "WW", economic_weight: 1.8 },
  { trait_code: "YW", economic_weight: 0.4 },
  { trait_code: "BW", economic_weight: -3.0 },
  { trait_code: "CED", economic_weight: 8.0 },
  { trait_code: "STAY", economic_weight: 6.0 },
  { trait_code: "MILK", economic_weight: 0.3 },
  { trait_code: "MARB", economic_weight: 25.0 },
  { trait_code: "REA", economic_weight: 11.0 },
];

const TEMPLATES: GoalTemplate[] = [
  {
    id: "maternal",
    name: "Self-replacing herd",
    desc: "You keep your own replacement heifers and sell the rest at " +
      "weaning. Rewards fertility, calving ease, longevity and moderate " +
      "growth.",
    basis: "per_cow_exposed",
    components: [
      { trait_code: "WW", economic_weight: 0.85 },
      { trait_code: "CED", economic_weight: 12.0 },
      { trait_code: "STAY", economic_weight: 6.4 },
      { trait_code: "HP", economic_weight: 7.0 },
      { trait_code: "MILK", economic_weight: 0.3 },
      { trait_code: "MW", economic_weight: -0.25 },
    ],
  },
  {
    id: "terminal",
    name: "Terminal — sell all calves",
    desc: "Every calf is fed and marketed; no females are kept. Rewards " +
      "growth and carcass merit, with calving ease to protect the calf.",
    basis: "per_calf",
    components: [
      { trait_code: "CW", economic_weight: 1.2 },
      { trait_code: "MARB", economic_weight: 26.0 },
      { trait_code: "REA", economic_weight: 11.0 },
      { trait_code: "FAT", economic_weight: -200.0 },
      { trait_code: "YW", economic_weight: 0.35 },
      { trait_code: "CED", economic_weight: 8.0 },
    ],
  },
  {
    id: "feedlot",
    name: "Retained ownership / feedlot",
    desc: "Calves are retained through the feedlot and sold on liveweight. " +
      "Rewards post-weaning growth and feed efficiency.",
    basis: "per_calf",
    components: [
      { trait_code: "YW", economic_weight: 0.40 },
      { trait_code: "PWG", economic_weight: 0.35 },
      { trait_code: "DMI", economic_weight: -2.9 },
      { trait_code: "RFI", economic_weight: -3.0 },
      { trait_code: "DOC", economic_weight: 7.0 },
    ],
  },
  {
    id: "high_altitude",
    name: "High-altitude / brisket disease",
    desc: "For herds grazing at elevation, where high-altitude (brisket) " +
      "disease is a real cost. Pairs PAP selection with a sound maternal " +
      "and growth base. An official PAP EPD is published only by the " +
      "American Angus and American Simmental associations.",
    basis: "per_cow_exposed",
    components: [
      { trait_code: "PAP", economic_weight: -8.9 },
      { trait_code: "WW", economic_weight: 0.85 },
      { trait_code: "CED", economic_weight: 12.0 },
      { trait_code: "STAY", economic_weight: 6.4 },
      { trait_code: "MW", economic_weight: -0.25 },
    ],
  },
];

interface IndexBuilderProps {
  /** A breeding goal handed in from the Herd Simulation wizard, or null. */
  derivedGoal?: DerivedGoal | null;
  /** Called once the derived goal has been loaded, to clear it. */
  onDerivedGoalConsumed?: () => void;
}

export function IndexBuilder({
  derivedGoal = null,
  onDerivedGoalConsumed,
}: IndexBuilderProps) {
  /* --- wizard state --------------------------------------------------- */
  const [step, setStep] = useState(1);

  /* Step 1: the breeding goal. */
  const [goalName, setGoalName] = useState("My selection index");
  const [basis, setBasis] = useState("per_cow_exposed");
  const [components, setComponents] = useState<GoalComponent[]>(
    DEFAULT_GOAL.map((c) => ({ ...c })),
  );

  /* Step 2: index mode (the parameter set is the built-in library in M1). */
  const [mode, setMode] = useState("economic_weight");

  /* Step 3: the candidate animals.
   * inputMode is how the producer supplies them: published EPDs, or raw
   * performance records (phenotypes) that the backend converts to
   * estimated breeding values by mass selection. */
  const [inputMode, setInputMode] = useState<"epd" | "phenotype">("epd");
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [phenotypeRecords, setPhenotypeRecords] = useState<
    import("../lib/api").PhenotypeRecordIn[]
  >([]);

  /* Step 4: the result. */
  const [result, setResult] = useState<IndexBuildResponse | null>(null);
  const [building, setBuilding] = useState(false);
  const [buildError, setBuildError] = useState("");

  /* The trait registry, loaded once for the pickers and labels. */
  const [traits, setTraits] = useState<Trait[]>([]);
  useEffect(() => {
    api.traits().then(setTraits).catch(() => setTraits([]));
  }, []);

  /* When the Herd Simulation wizard hands in a derived goal, load its
   * economic weights and jump the user past step 1 — the simulation has
   * already done the work of defining the goal. */
  useEffect(() => {
    if (!derivedGoal) return;
    setGoalName(derivedGoal.name);
    setComponents(derivedGoal.components.map((c) => ({ ...c })));
    setStep(2);
    onDerivedGoalConsumed?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [derivedGoal]);

  function applyTemplate(t: GoalTemplate) {
    setGoalName(`${t.name} index`);
    setBasis(t.basis);
    setComponents(t.components.map((c) => ({ ...c })));
  }

  /* --- step gating: a step's Continue is enabled only when valid ------ */
  const goalValid = components.length > 0;
  const animalsValid = animals.length > 0;

  async function runBuild(animalsOverride?: Animal[]) {
    const animalsToBuild = animalsOverride ?? animals;
    setBuilding(true);
    setBuildError("");
    try {
      const res = await api.buildIndex({
        goal: { name: goalName, basis, components, source: "manual" },
        animals: animalsToBuild,
        mode,
        missing_policy: "exclude",
      });
      setResult(res);
      setStep(4);
    } catch (err) {
      setBuildError(
        err instanceof Error ? err.message : "The build failed.",
      );
    } finally {
      setBuilding(false);
    }
  }

  /* Build the index from phenotype records instead of EPDs. The backend
   * converts the records to estimated breeding values (mass selection)
   * before ranking; the result shape is identical to an EPD build. */
  async function runPhenotypeBuild(
    recordsOverride?: import("../lib/api").PhenotypeRecordIn[],
  ) {
    const recordsToBuild = recordsOverride ?? phenotypeRecords;
    setBuilding(true);
    setBuildError("");
    try {
      const res = await api.buildFromPhenotypes({
        goal: { name: goalName, basis, components, source: "manual" },
        records: recordsToBuild,
        mode,
        missing_policy: "exclude",
      });
      setResult(res);
      setStep(4);
    } catch (err) {
      setBuildError(
        err instanceof Error ? err.message : "The build failed.",
      );
    } finally {
      setBuilding(false);
    }
  }

  return (
    <main className="main-area">
      <div className="main-content with-panel">
        <div className="panel-main">
          <Stepper
            steps={STEPS}
            current={step}
            onStepClick={(s) => setStep(s)}
          />

          {/* ---- Step 1: Goal ---- */}
          {step === 1 && (
            <>
              <h1 className="page-title">What are you breeding for?</h1>
              <p className="page-intro">
                Tell NexGenIQ which traits matter and what each is worth.
                Not sure? Start from a template — the defaults come from
                published research and you can just continue. The traits
                you pick here must match the EPD columns in the animal
                file you upload later.
              </p>
              <GoalStep
                templates={TEMPLATES}
                onApplyTemplate={applyTemplate}
                traits={traits}
                goalName={goalName}
                onGoalName={setGoalName}
                basis={basis}
                onBasis={setBasis}
                components={components}
                onComponents={setComponents}
              />
              <div className="wizard-actions">
                <span />
                <Button
                  variant="primary"
                  disabled={!goalValid}
                  onClick={() => setStep(2)}
                >
                  Continue →
                </Button>
              </div>
            </>
          )}

          {/* ---- Step 2: Parameters ---- */}
          {step === 2 && (
            <>
              <h1 className="page-title">How are these traits related?</h1>
              <p className="page-intro">
                NexGenIQ needs to know how the traits connect genetically.
                Most people use the built-in research library — selected
                for you below.
              </p>
              <Card>
                <div className="start-card start-card-selected">
                  <p className="start-card-title">
                    Use the built-in research library
                  </p>
                  <p className="start-card-desc">
                    Beef-cattle consensus set · v1 · 2026 — every value is
                    drawn from published research and cited.
                  </p>
                </div>
              </Card>
              <Card title="Index mode" helpId="index_mode">
                <Field
                  label="How should the index combine your traits?"
                  helpId="index_mode"
                  hint="Most users should keep Standard. Choose
                        Accuracy-adjusted only if your animals' EPDs vary a
                        lot in accuracy."
                >
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                  >
                    <option value="economic_weight">
                      Standard — weight by economic value
                    </option>
                    <option value="blup_index">
                      Accuracy-adjusted — also account for EPD reliability
                    </option>
                  </select>
                </Field>
              </Card>
              <div className="wizard-actions">
                <Button variant="secondary" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button variant="primary" onClick={() => setStep(3)}>
                  Continue →
                </Button>
              </div>
            </>
          )}

          {/* ---- Step 3: Animals ---- */}
          {step === 3 && (
            <>
              <h1 className="page-title">
                Which animals do you want to compare?
              </h1>
              <p className="page-intro">
                Upload a sale catalogue or data file — NexGenIQ will match
                the columns for you — or add a few animals by hand.
              </p>
              {new Set(
                animals.map((a) => a.breed).filter(Boolean),
              ).size > 1 && (
                <div className="across-breed-note">
                  <p className="across-breed-note-title">
                    Your animals span more than one breed
                  </p>
                  <p>
                    EPDs from different breeds sit on different scales and
                    cannot be compared directly. When you build the index,
                    NexGenIQ places every animal's EPDs on a common base
                    first (an across-breed adjustment) so animals of
                    different breeds can be ranked together fairly.
                  </p>
                </div>
              )}
              <Card title="What data do you have for your animals?">
                <div className="input-mode-choice">
                  <label className="input-mode-option">
                    <input
                      type="radio"
                      name="input-mode"
                      checked={inputMode === "epd"}
                      onChange={() => setInputMode("epd")}
                    />
                    <span>
                      <strong>I have EPDs</strong> — published expected
                      progeny differences from a breed association or
                      genetic evaluation.
                    </span>
                  </label>
                  <label className="input-mode-option">
                    <input
                      type="radio"
                      name="input-mode"
                      checked={inputMode === "phenotype"}
                      onChange={() => setInputMode("phenotype")}
                    />
                    <span>
                      <strong>I have phenotypic data</strong> — my own
                      measured performance records (weights, scans, PAP,
                      feed-test data). NexGenIQ will rank the animals on
                      their own performance.
                    </span>
                  </label>
                </div>
              </Card>

              {inputMode === "epd" ? (
                <AnimalsStep
                  traits={traits}
                  animals={animals}
                  onAnimals={setAnimals}
                  onRunExample={(exampleAnimals) => {
                    /* Load the example animals into state AND build the
                       index immediately, passing them explicitly so the
                       build does not wait for the state update. */
                    setAnimals(exampleAnimals);
                    runBuild(exampleAnimals);
                  }}
                />
              ) : (
                <PhenotypeStep
                  records={phenotypeRecords}
                  onRecords={setPhenotypeRecords}
                  onRunExample={(exampleRecords) => {
                    setPhenotypeRecords(exampleRecords);
                    runPhenotypeBuild(exampleRecords);
                  }}
                />
              )}
              <div className="wizard-actions">
                <Button variant="secondary" onClick={() => setStep(2)}>
                  Back
                </Button>
                {inputMode === "epd" ? (
                  <Button
                    variant="primary"
                    busy={building}
                    disabled={!animalsValid}
                    onClick={() => runBuild()}
                  >
                    Build my index →
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    busy={building}
                    disabled={phenotypeRecords.length === 0}
                    onClick={() => runPhenotypeBuild()}
                  >
                    Build my index →
                  </Button>
                )}
              </div>
              {buildError && (
                <p className="auth-error" style={{ marginTop: 12 }}>
                  {buildError}
                </p>
              )}
            </>
          )}

          {/* ---- Step 4: Results ---- */}
          {step === 4 && result && (
            <ResultsWorkspace
              result={result}
              traits={traits}
              goal={{ name: goalName, basis, components }}
              animals={animals}
              mode={mode}
              onEdit={() => setStep(1)}
            />
          )}
        </div>

        <ContextPanel />
      </div>
    </main>
  );
}
