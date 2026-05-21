/*
 * The Herd Simulation wizard — NexGenIQ Milestone 2.
 *
 * A guided flow that derives economic values from a description of the
 * user's production system, then hands them to the Index Builder as a
 * breeding goal. Implements the simulation side of the integrated
 * pipeline (Phase 3 Part 3A Section 1.3.2; Phase 3.5).
 *
 * Three steps share state: describe the herd, describe the economics,
 * then run and review the derived economic values.
 */

import { useState } from "react";
import {
  api,
  type GoalComponent,
  type SimulationResponse,
} from "../lib/api";
import { Button, Card, Field, Stepper } from "../components/UI";
import { ContextPanel } from "../components/Help";
import { InterpretationPanel } from "../components/InterpretationPanel";

/* Readable names for the trait codes the simulation can return, so the
   results table does not show bare codes. Matches the engine registry. */
const TRAIT_NAMES: Record<string, string> = {
  BW: "Birth weight",
  WW: "Weaning weight",
  YW: "Yearling weight",
  PWG: "Post-weaning gain",
  MILK: "Maternal milk",
  MW: "Mature cow weight",
  CED: "Calving ease direct",
  CEM: "Calving ease maternal",
  HP: "Heifer pregnancy",
  SC: "Scrotal circumference",
  STAY: "Stayability",
  CW: "Carcass weight",
  MARB: "Marbling",
  REA: "Ribeye area",
  FAT: "Backfat thickness",
  DMI: "Dry matter intake",
  RFI: "Residual feed intake",
  DOC: "Docility",
  PAP: "Pulmonary arterial pressure",
};

const STEPS = ["Your herd", "Economics", "Results"];

/*
 * The trait set is no longer hard-coded here. Sending an empty `traits`
 * list lets the engine derive an economic value for EVERY trait the
 * herd's breeds publish an EPD for — the full EPD set, including the
 * carcass and feed-efficiency traits that matter for terminal and
 * on-the-rail marketing, and PAP for Angus / Red Angus / Simmental herds.
 */

interface SimulationWizardProps {
  /** Called with the derived economic weights to start an index from. */
  onUseInIndex: (
    components: GoalComponent[],
    name: string,
  ) => void;
}

export function SimulationWizard({
  onUseInIndex,
}: SimulationWizardProps) {
  const [step, setStep] = useState(1);

  /* Step 1 — the production system. */
  const [systemName, setSystemName] = useState("My cow-calf operation");
  const [herdSize, setHerdSize] = useState(200);
  const [conception, setConception] = useState(0.92);
  const [calvingLoss, setCalvingLoss] = useState(0.06);
  const [replacement, setReplacement] = useState(0.18);
  const [heiferRetention, setHeiferRetention] = useState(true);

  /* Step 1 — the herd's breed. Determines which EPDs apply (e.g. PAP is
     published only by Angus, Red Angus and Simmental). */
  const [breed, setBreed] = useState("Angus");

  /* Step 2 — the economic scenario. */
  const [endpoint, setEndpoint] = useState("weaning");
  const [steerPrice, setSteerPrice] = useState(195);
  const [heiferPrice, setHeiferPrice] = useState(178);
  const [aumCost, setAumCost] = useState(38);
  const [fixedCost, setFixedCost] = useState(185);
  /* Elevation drives the economic weight of PAP (brisket disease). */
  const [elevationFt, setElevationFt] = useState(4000);
  /* Carcass / feedlot inputs — used when calves are sold past weaning. */
  const [carcassBasePrice, setCarcassBasePrice] = useState(300);
  const [backgroundDays, setBackgroundDays] = useState(60);
  const [daysOnFeed, setDaysOnFeed] = useState(160);
  /* Replacement-female and death-loss costs (model defaults shown;
     the user can set them to their own operation). */
  const [replacementDevCost, setReplacementDevCost] = useState(900);
  const [purchasedReplCost, setPurchasedReplCost] = useState(1800);
  const [lostAnimalCost, setLostAnimalCost] = useState(1400);

  /* Whether the chosen endpoint involves a feedlot / carcass phase. */
  const isTerminalEndpoint = endpoint !== "weaning";
  const isCarcassEndpoint = endpoint === "carcass";

  /* Step 3 — the result. */
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  async function runSimulation() {
    setRunning(true);
    setError("");
    try {
      const res = await api.deriveMevs({
        production_system: {
          name: systemName,
          herd_size: herdSize,
          conception_rate: conception,
          calving_loss_rate: calvingLoss,
          replacement_rate: replacement,
          heifer_retention: heiferRetention,
          cow_breed_composition: [
            { fraction: 1.0, breeds: { [breed]: 1.0 } },
          ],
          bull_breed_composition: [
            { fraction: 1.0, breeds: { [breed]: 1.0 } },
          ],
        },
        economic_scenario: {
          name: "My economics",
          sale_endpoint: endpoint,
          price_bands: [
            { sex: "S", low: 0, high: 9999,
              price_per_cwt: steerPrice },
            { sex: "F", low: 0, high: 9999,
              price_per_cwt: heiferPrice },
            { sex: "C", low: 0, high: 9999, price_per_cwt: 110 },
          ],
          carcass_base_price: carcassBasePrice,
          /* A standard USDA quality x yield grade grid. Premiums and
             discounts in $/cwt of carcass relative to the base price. */
          grid: isCarcassEndpoint
            ? [
                { quality_grade: "Prime", yield_grade: 2, premium: 24 },
                { quality_grade: "Prime", yield_grade: 3, premium: 18 },
                { quality_grade: "Choice", yield_grade: 2, premium: 6 },
                { quality_grade: "Choice", yield_grade: 3, premium: 2 },
                { quality_grade: "Choice", yield_grade: 4, premium: -8 },
                { quality_grade: "Select", yield_grade: 3, premium: -14 },
                { quality_grade: "Select", yield_grade: 4, premium: -22 },
                { quality_grade: "Standard", yield_grade: 3,
                  premium: -30 },
              ]
            : [],
          cull_cow_price_per_cwt: 110,
          aum_cost: aumCost,
          fixed_cost_per_cow: fixedCost,
          background_days: isTerminalEndpoint ? backgroundDays : 0,
          days_on_feed:
            endpoint === "fed" || endpoint === "carcass"
              ? daysOnFeed
              : 0,
          discount_rate: 0.06,
          elevation_ft: elevationFt,
          replacement_development_cost: replacementDevCost,
          purchased_replacement_cost: purchasedReplCost,
          value_of_lost_animal: lostAnimalCost,
        },
        controls: {
          burn_in_years: 6,
          planning_horizon_years: 12,
          replicates: 12,
          seed: 20260520,
        },
        /* Empty list -> the engine derives an MEV for every trait the
           herd's breeds publish (the full EPD set, PAP included for the
           breeds that evaluate it). */
        traits: [],
      });
      setResult(res);
      setStep(3);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "The simulation failed.",
      );
    } finally {
      setRunning(false);
    }
  }

  function useDerivedValues() {
    if (!result) return;
    const components: GoalComponent[] = result.mevs.map((m) => ({
      trait_code: m.trait_code,
      economic_weight: Number(m.mev.toFixed(3)),
    }));
    onUseInIndex(components, `${systemName} — derived index`);
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

          {/* ---- Step 1: the herd ---- */}
          {step === 1 && (
            <>
              <h1 className="page-title">Describe your operation</h1>
              <p className="page-intro">
                NexGenIQ will simulate a herd like yours to work out what
                each trait is actually worth to you. Not sure of a number?
                The defaults are sensible starting points.
              </p>
              <Card title="Your herd" helpId="goal">
                <Field label="Name this operation">
                  <input
                    type="text"
                    value={systemName}
                    onChange={(e) => setSystemName(e.target.value)}
                  />
                </Field>
                <Field
                  label="Number of breeding cows"
                  hint="The size of your cow herd."
                >
                  <input
                    type="number"
                    value={herdSize}
                    onChange={(e) =>
                      setHerdSize(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Predominant breed"
                  hint="The main breed of your cow herd. This decides which
                        EPDs apply — for example, a PAP (brisket disease)
                        EPD is published only for Angus, Red Angus and
                        Simmental."
                >
                  <select
                    value={breed}
                    onChange={(e) => setBreed(e.target.value)}
                  >
                    <option value="Angus">Angus</option>
                    <option value="Red Angus">Red Angus</option>
                    <option value="Hereford">Hereford</option>
                    <option value="Simmental">Simmental</option>
                    <option value="Charolais">Charolais</option>
                  </select>
                </Field>
                <Field
                  label="Conception rate"
                  hint="The fraction of cows that conceive each season.
                        0.92 means 92%."
                >
                  <input
                    type="number"
                    step="0.01"
                    value={conception}
                    onChange={(e) =>
                      setConception(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Calving loss rate"
                  hint="The fraction of pregnancies lost before weaning."
                >
                  <input
                    type="number"
                    step="0.01"
                    value={calvingLoss}
                    onChange={(e) =>
                      setCalvingLoss(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Replacement rate"
                  hint="The fraction of cows replaced each year."
                >
                  <input
                    type="number"
                    step="0.01"
                    value={replacement}
                    onChange={(e) =>
                      setReplacement(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Do you keep your own replacement heifers?"
                  hint="Self-replacing herds value fertility and longevity
                        more highly."
                >
                  <select
                    value={heiferRetention ? "yes" : "no"}
                    onChange={(e) =>
                      setHeiferRetention(e.target.value === "yes")
                    }
                  >
                    <option value="yes">
                      Yes — I keep my own heifers
                    </option>
                    <option value="no">
                      No — terminal, I sell all calves
                    </option>
                  </select>
                </Field>
              </Card>
              <div className="wizard-actions">
                <span />
                <Button
                  variant="primary"
                  onClick={() => setStep(2)}
                >
                  Continue →
                </Button>
              </div>
            </>
          )}

          {/* ---- Step 2: economics ---- */}
          {step === 2 && (
            <>
              <h1 className="page-title">
                Your prices and costs
              </h1>
              <p className="page-intro">
                How and when you sell your calves, and what it costs to run
                a cow. These determine what each trait is worth.
              </p>
              <Card title="Economics">
                <Field
                  label="When do you sell your calves?"
                  hint="Where in the production chain you market the calf
                        crop. Selling past weaning makes growth, feed
                        efficiency and carcass traits economically real."
                >
                  <select
                    value={endpoint}
                    onChange={(e) => setEndpoint(e.target.value)}
                  >
                    <option value="weaning">At weaning</option>
                    <option value="background">
                      After backgrounding
                    </option>
                    <option value="fed">Finished, off the feedlot</option>
                    <option value="carcass">On the rail (carcass)</option>
                  </select>
                </Field>
                <Field
                  label="Steer calf price ($/cwt)"
                  hint="Sale price per hundredweight for steer calves."
                >
                  <input
                    type="number"
                    value={steerPrice}
                    onChange={(e) =>
                      setSteerPrice(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Heifer calf price ($/cwt)"
                  hint="Sale price per hundredweight for heifer calves."
                >
                  <input
                    type="number"
                    value={heiferPrice}
                    onChange={(e) =>
                      setHeiferPrice(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Pasture cost ($/AUM)"
                  hint="Cost of one animal-unit-month — the monthly cost of
                        carrying a 1,000 lb cow."
                >
                  <input
                    type="number"
                    value={aumCost}
                    onChange={(e) =>
                      setAumCost(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Fixed cost per cow ($/year)"
                  hint="Annual non-feed cost per cow — labour, health,
                        overhead."
                >
                  <input
                    type="number"
                    value={fixedCost}
                    onChange={(e) =>
                      setFixedCost(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Ranch elevation (ft above sea level)"
                  hint="Elevation of your range. High-altitude (brisket)
                        disease becomes a real cost above ~5,000 ft — this
                        is what gives the PAP EPD economic weight. Set it
                        to your highest summer pasture."
                >
                  <input
                    type="number"
                    step="100"
                    value={elevationFt}
                    onChange={(e) =>
                      setElevationFt(Number(e.target.value))
                    }
                  />
                </Field>
              </Card>

              <Card title="Replacement and herd costs">
                <p className="field-hint" style={{ marginBottom: 12 }}>
                  These costs determine what fertility and longevity are
                  worth. The defaults are representative figures &mdash;
                  set them to your own operation for a result specific to
                  you.
                </p>
                <Field
                  label="Cost to develop a replacement heifer ($)"
                  hint="What it costs to rear one of your own heifers from
                        weaning to her first calving."
                >
                  <input
                    type="number"
                    step="25"
                    value={replacementDevCost}
                    onChange={(e) =>
                      setReplacementDevCost(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Cost to buy a bred replacement female ($)"
                  hint="The market price of a bred replacement female,
                        used when your own heifers do not fill every
                        opening."
                >
                  <input
                    type="number"
                    step="25"
                    value={purchasedReplCost}
                    onChange={(e) =>
                      setPurchasedReplCost(Number(e.target.value))
                    }
                  />
                </Field>
                <Field
                  label="Loss when a productive cow dies ($)"
                  hint="The economic loss when a cow dies (for example to
                        high-altitude disease) rather than being culled
                        for salvage value."
                >
                  <input
                    type="number"
                    step="25"
                    value={lostAnimalCost}
                    onChange={(e) =>
                      setLostAnimalCost(Number(e.target.value))
                    }
                  />
                </Field>
              </Card>

              {/* Feedlot / carcass inputs — only relevant when calves
                  are marketed past weaning. */}
              {isTerminalEndpoint && (
                <Card title="Feedlot and carcass">
                  <p className="field-hint" style={{ marginBottom: 12 }}>
                    Because you sell past weaning, growth, feed efficiency
                    {isCarcassEndpoint
                      ? " and carcass merit (marbling, ribeye, backfat)"
                      : ""}{" "}
                    now carry economic value. NexGenIQ values every one of
                    those traits for you.
                  </p>
                  <Field
                    label="Days backgrounded"
                    hint="Days calves spend backgrounding after weaning
                          before the feedlot."
                  >
                    <input
                      type="number"
                      step="10"
                      value={backgroundDays}
                      onChange={(e) =>
                        setBackgroundDays(Number(e.target.value))
                      }
                    />
                  </Field>
                  {(endpoint === "fed" ||
                    endpoint === "carcass") && (
                    <Field
                      label="Days on feed"
                      hint="Days in the feedlot to a finished weight."
                    >
                      <input
                        type="number"
                        step="10"
                        value={daysOnFeed}
                        onChange={(e) =>
                          setDaysOnFeed(Number(e.target.value))
                        }
                      />
                    </Field>
                  )}
                  {isCarcassEndpoint && (
                    <Field
                      label="Carcass base price ($/cwt)"
                      hint="Base price per hundredweight of carcass, before
                            grid premiums and discounts."
                    >
                      <input
                        type="number"
                        value={carcassBasePrice}
                        onChange={(e) =>
                          setCarcassBasePrice(Number(e.target.value))
                        }
                      />
                    </Field>
                  )}
                </Card>
              )}
              <div className="wizard-actions">
                <Button
                  variant="secondary"
                  onClick={() => setStep(1)}
                >
                  Back
                </Button>
                <Button
                  variant="primary"
                  busy={running}
                  onClick={runSimulation}
                >
                  Run the simulation →
                </Button>
              </div>
              {error && (
                <p className="auth-error" style={{ marginTop: 12 }}>
                  {error}
                </p>
              )}
            </>
          )}

          {/* ---- Step 3: results ---- */}
          {step === 3 && result && (
            <>
              <h1 className="page-title">
                What your traits are worth
              </h1>
              <p className="page-intro">
                NexGenIQ simulated your operation and worked out the
                economic value of each trait. Carry these straight into
                the Index Builder to rank animals for your operation.
              </p>

              <InterpretationPanel
                interpretation={result.interpretation}
              />

              <div className="metric-row">
                <div className="metric-card">
                  <p className="metric-label">
                    Simulated herd profit
                  </p>
                  <p className="metric-value metric-value-sage tnum">
                    $
                    {Math.round(
                      result.baseline_profit,
                    ).toLocaleString()}
                  </p>
                </div>
                <div className="metric-card">
                  <p className="metric-label">Traits valued</p>
                  <p className="metric-value tnum">
                    {result.mevs.length}
                  </p>
                </div>
                <div className="metric-card">
                  <p className="metric-label">Replicate herds</p>
                  <p className="metric-value tnum">
                    {result.replicates}
                  </p>
                </div>
                <div className="metric-card">
                  <p className="metric-label">Sale endpoint</p>
                  <p
                    className="metric-value"
                    style={{ fontSize: 16 }}
                  >
                    {endpoint}
                  </p>
                </div>
              </div>

              <Card title="Derived economic values">
                <table className="rank-table">
                  <thead>
                    <tr>
                      <th>Trait</th>
                      <th>Economic value</th>
                      <th>Precision</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.mevs.map((m) => (
                      <tr key={m.trait_code}>
                        <td>
                          <strong>{m.trait_code}</strong>
                          <span
                            className="field-hint"
                            style={{ marginLeft: 6 }}
                          >
                            {TRAIT_NAMES[m.trait_code] ?? ""}
                          </span>
                        </td>
                        <td className="rank-index tnum">
                          {m.mev >= 0 ? "+" : ""}
                          {m.mev.toFixed(2)} $/{m.units}
                          <span className="rank-ci tnum">
                            {" "}
                            ± {m.mc_std_error.toFixed(2)}
                          </span>
                        </td>
                        <td>
                          {m.is_precise ? (
                            <span style={{ color: "#3D6B4E" }}>
                              precise
                            </span>
                          ) : (
                            <span style={{ color: "#7A4F0B" }}>
                              imprecise — add replicates
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {result.warnings.map((w) => (
                  <p
                    key={w}
                    className="field-hint"
                    style={{ marginTop: 8 }}
                  >
                    {w}
                  </p>
                ))}
              </Card>

              <div className="sens-summary">
                These economic values are specific to the operation you
                described. Use them in the Index Builder and your animal
                ranking will reflect your herd, your market, and your
                costs.
              </div>

              <div className="wizard-actions">
                <Button
                  variant="secondary"
                  onClick={() => setStep(2)}
                >
                  Adjust and re-run
                </Button>
                <Button
                  variant="primary"
                  onClick={useDerivedValues}
                >
                  Use these in the Index Builder →
                </Button>
              </div>
            </>
          )}
        </div>

        <ContextPanel />
      </div>
    </main>
  );
}
