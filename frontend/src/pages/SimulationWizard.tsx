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
  type BreedCompositionIn,
  type GoalComponent,
  type PriceBandIn,
  type SimulationResponse,
} from "../lib/api";
import { Button, Card, Field, Stepper } from "../components/UI";
import { ContextPanel } from "../components/Help";
import { InterpretationPanel } from "../components/InterpretationPanel";
import {
  BreedCompositionBuilder,
  averageComposition,
} from "../components/builder/BreedCompositionBuilder";
import {
  PriceBandEditor,
  defaultPriceBands,
} from "../components/builder/PriceBandEditor";

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

/* Breeds that publish a PAP EPD - used to tell the user whether PAP will
   be evaluated for the herd they have described. Matches the engine's
   BREED_RESTRICTED_TRAITS. */
const PAP_BREEDS = new Set(["Angus", "Simmental"]);

const STEPS = ["Your herd", "Economics", "Results"];

/*
 * The trait set is not hard-coded. Sending an empty `traits` list lets
 * the engine derive an economic value for EVERY trait the herd's breeds
 * publish an EPD for - the full EPD set, including the carcass and
 * feed-efficiency traits that matter for terminal and on-the-rail
 * marketing, and PAP for Angus and Simmental herds.
 */

interface SimulationWizardProps {
  /** Called with the derived economic weights to start an index from. */
  onUseInIndex: (
    components: GoalComponent[],
    name: string,
  ) => void;
}

/* Round a fraction to a whole percent for display. */
function pct(x: number): number {
  return Math.round(x * 100);
}

export function SimulationWizard({
  onUseInIndex,
}: SimulationWizardProps) {
  const [step, setStep] = useState(1);

  /* Step 1 - the production system. */
  const [systemName, setSystemName] = useState("My cow-calf operation");
  const [herdSize, setHerdSize] = useState(200);
  const [conception, setConception] = useState(0.92);
  const [calvingLoss, setCalvingLoss] = useState(0.06);
  const [replacement, setReplacement] = useState(0.18);
  const [heiferRetention, setHeiferRetention] = useState(true);

  /* Step 1 - breed composition of the cow herd and the bull battery.
     Each is a list of composition classes; a class is a fraction of the
     group and itself a breed mix. The calf crop's composition is derived
     (not entered) as the dam/sire average. */
  const [cowComposition, setCowComposition] = useState<
    BreedCompositionIn[]
  >([{ fraction: 1.0, breeds: { Angus: 1.0 } }]);
  const [bullComposition, setBullComposition] = useState<
    BreedCompositionIn[]
  >([{ fraction: 1.0, breeds: { Angus: 1.0 } }]);

  /* Step 2 - the economic scenario. */
  const [endpoint, setEndpoint] = useState("weaning");
  const [priceBands, setPriceBands] = useState<PriceBandIn[]>(
    defaultPriceBands(),
  );
  const [aumCost, setAumCost] = useState(38);
  const [fixedCost, setFixedCost] = useState(185);
  /* Elevation drives the economic weight of PAP (brisket disease). */
  const [elevationFt, setElevationFt] = useState(4000);
  /* Carcass / feedlot inputs - used when calves are sold past weaning. */
  const [carcassBasePrice, setCarcassBasePrice] = useState(300);
  const [backgroundDays, setBackgroundDays] = useState(60);
  const [daysOnFeed, setDaysOnFeed] = useState(160);
  /* Replacement-female and death-loss costs (model defaults shown;
     the user can set them to their own operation). */
  const [replacementDevCost, setReplacementDevCost] = useState(900);
  const [purchasedReplCost, setPurchasedReplCost] = useState(1800);
  const [lostAnimalCost, setLostAnimalCost] = useState(1400);
  /* High-altitude (PAP / brisket) disease economics. Only relevant when
     the herd grazes at altitude and contains a PAP-evaluated breed. */
  const [papDeathLossPct, setPapDeathLossPct] = useState(2);
  const [papProactiveCull, setPapProactiveCull] = useState(true);
  /* Simulation precision - a named preset the producer chooses. More
     replicate herds give a more precise economic value, especially for
     the noisier traits (PAP, stayability, fertility), but take longer. */
  const [precision, setPrecision] = useState<
    "quick" | "standard" | "high"
  >("standard");

  /* Whether the chosen endpoint involves a feedlot / carcass phase. */
  const isTerminalEndpoint = endpoint !== "weaning";
  const isCarcassEndpoint = endpoint === "carcass";

  /* Precision presets: replicate count and an approximate run time.
     The replicate count is the number of independent simulated herds the
     economic values are averaged over. */
  const PRECISION_PRESETS = {
    quick: {
      replicates: 8,
      label: "Quick",
      time: "about 30-40 seconds",
      note: "Fastest. Good for exploring. The noisier traits may come " +
        "back marked imprecise.",
    },
    standard: {
      replicates: 14,
      label: "Standard",
      time: "about 1 minute",
      note: "A balanced choice for most runs.",
    },
    high: {
      replicates: 26,
      label: "High precision",
      time: "about 2-3 minutes",
      note: "For when you need a reliable value on the noisier traits " +
        "(PAP, stayability, fertility). Takes noticeably longer.",
    },
  } as const;
  const chosenPreset = PRECISION_PRESETS[precision];

  /* Step 3 - the result. */
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  /* --- derived breed information ------------------------------------- */
  /* The calf crop's breed composition is the average of the dam side and
     the sire side - half the cow herd's average, half the bull battery's
     average. The user never enters this; it is shown so they can see it. */
  const cowAvg = averageComposition(cowComposition);
  const bullAvg = averageComposition(bullComposition);
  const calfAvg: Record<string, number> = {};
  for (const [b, f] of Object.entries(cowAvg)) {
    calfAvg[b] = (calfAvg[b] ?? 0) + f / 2;
  }
  for (const [b, f] of Object.entries(bullAvg)) {
    calfAvg[b] = (calfAvg[b] ?? 0) + f / 2;
  }
  /* Every breed anywhere in the herd, for the PAP-availability note. */
  const herdBreeds = new Set<string>([
    ...Object.keys(cowAvg),
    ...Object.keys(bullAvg),
  ]);
  const papAvailable = [...herdBreeds].some((b) => PAP_BREEDS.has(b));

  /* --- validation ---------------------------------------------------- */
  function compositionValid(classes: BreedCompositionIn[]): boolean {
    const classTotal = classes.reduce((a, c) => a + c.fraction, 0);
    if (Math.abs(classTotal - 1.0) > 1e-6) return false;
    return classes.every((c) => {
      const breedTotal = Object.values(c.breeds).reduce(
        (a, b) => a + b,
        0,
      );
      return Math.abs(breedTotal - 1.0) < 1e-6;
    });
  }
  const breedInputsValid =
    compositionValid(cowComposition) &&
    compositionValid(bullComposition);

  async function runSimulation() {
    if (!breedInputsValid) {
      setError(
        "Please make the breed fractions add up correctly before " +
          "running - each group and each breed mix must total 100%.",
      );
      setStep(1);
      return;
    }
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
          cow_breed_composition: cowComposition,
          bull_breed_composition: bullComposition,
        },
        economic_scenario: {
          name: "My economics",
          sale_endpoint: endpoint,
          price_bands: priceBands,
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
          pap_death_loss_rate: papDeathLossPct / 100,
          pap_proactive_culling: papProactiveCull,
        },
        controls: {
          burn_in_years: 6,
          planning_horizon_years: 12,
          replicates: chosenPreset.replicates,
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

              <Card title="Breed composition">
                <p className="field-hint" style={{ marginBottom: 14 }}>
                  Describe the real breed makeup of your cow herd and the
                  bulls you mate them to. Most herds are one breed, but
                  you can describe crosses and mixed herds. Breed makeup
                  drives heterosis, breed differences, and which EPDs
                  apply — NexGenIQ works out the calf crop for you.
                </p>

                <BreedCompositionBuilder
                  label="Cow herd"
                  hint="The breed makeup of your breeding females."
                  classes={cowComposition}
                  onChange={setCowComposition}
                />

                <div style={{ height: 18 }} />

                <BreedCompositionBuilder
                  label="Bull battery"
                  hint="The breed makeup of the bulls your cows are mated
                        to."
                  classes={bullComposition}
                  onChange={setBullComposition}
                />

                {/* Derived calf-crop composition - never entered. */}
                <div className="calf-derived">
                  <p className="calf-derived-label">
                    Resulting calf crop
                  </p>
                  <p className="field-hint">
                    Half from the cow herd, half from the bulls — this is
                    the breed makeup of the calves NexGenIQ will simulate.
                  </p>
                  <div className="calf-derived-breeds">
                    {Object.entries(calfAvg)
                      .filter(([, f]) => f > 0.0005)
                      .sort((a, b) => b[1] - a[1])
                      .map(([breed, f]) => (
                        <span key={breed} className="calf-breed-chip">
                          {breed} {pct(f)}%
                        </span>
                      ))}
                  </div>
                </div>

                {/* Plain-language note on PAP availability. */}
                <p
                  className="field-hint"
                  style={{ marginTop: 12, fontStyle: "italic" }}
                >
                  {papAvailable
                    ? "Your herd contains a breed that publishes a PAP " +
                      "(brisket disease) EPD, so PAP will be included " +
                      "in the economic-value analysis."
                    : "None of your herd's breeds publish a PAP " +
                      "(brisket disease) EPD, so PAP will not be " +
                      "included. An official PAP EPD is published only " +
                      "by the American Angus Association and the " +
                      "American Simmental Association."}
                </p>
              </Card>

              {!breedInputsValid && (
                <p className="auth-error" style={{ marginTop: 4 }}>
                  Each group's share and each breed mix must total 100%
                  before you continue.
                </p>
              )}

              <div className="wizard-actions">
                <span />
                <Button
                  variant="primary"
                  disabled={!breedInputsValid}
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
              <Card title="Marketing and prices">
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

                <PriceBandEditor
                  bands={priceBands}
                  onChange={setPriceBands}
                />
              </Card>

              <Card title="Herd costs">
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

              {/* High-altitude disease economics - only shown when the
                  herd grazes at altitude with a PAP-evaluated breed. */}
              {papAvailable && elevationFt >= 5000 && (
                <Card title="High-altitude disease (PAP)">
                  <p className="field-hint" style={{ marginBottom: 12 }}>
                    Your herd grazes at altitude and includes a
                    PAP-evaluated breed, so high-altitude (brisket)
                    disease is a real cost. Tell NexGenIQ what that
                    disease costs you and it will value the PAP trait
                    accordingly. If you do not lose cattle to it, set the
                    death loss to zero.
                  </p>
                  <Field
                    label="Annual death loss to brisket disease (%)"
                    hint="The share of your herd you lose to high-altitude
                          heart failure in a typical year. Enter what you
                          actually observe — the simulation calibrates to
                          this figure. 2 means 2%."
                  >
                    <input
                      type="number"
                      step="0.5"
                      min={0}
                      max={50}
                      value={papDeathLossPct}
                      onChange={(e) =>
                        setPapDeathLossPct(Number(e.target.value))
                      }
                    />
                  </Field>
                  <Field
                    label="Loss when an animal dies of brisket disease ($)"
                    hint="The economic loss of one productive animal lost
                          to the disease. This is the same figure as the
                          'loss when a productive cow dies' below."
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
                  <Field
                    label="Do you cull high-PAP animals before they die?"
                    hint="If you PAP-test and cull high-reading animals
                          rather than risk losing them, choose Yes. This
                          adds the cost of those extra replacements."
                  >
                    <select
                      value={papProactiveCull ? "yes" : "no"}
                      onChange={(e) =>
                        setPapProactiveCull(e.target.value === "yes")
                      }
                    >
                      <option value="yes">
                        Yes — I cull high-PAP animals
                      </option>
                      <option value="no">
                        No — I do not test or cull on PAP
                      </option>
                    </select>
                  </Field>
                </Card>
              )}

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
                  hint="The economic loss when a cow dies rather than
                        being culled for salvage value."
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

              {/* Feedlot / carcass inputs - only relevant when calves
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
              <Card title="Simulation precision">
                <p className="field-hint" style={{ marginBottom: 12 }}>
                  The simulation works out each trait's value by running
                  many independent virtual herds and averaging the
                  result. More herds give a more precise value, especially
                  for the noisier traits, but take longer to run.
                </p>
                {papAvailable && elevationFt >= 5000 && (
                  <p className="precision-nudge">
                    Your herd grazes at altitude and includes a
                    PAP-evaluated breed. PAP is one of the noisier traits
                    to estimate &mdash; <strong>High precision</strong> is
                    recommended so its economic value comes back
                    reliable.
                  </p>
                )}
                <div className="precision-options">
                  {(["quick", "standard", "high"] as const).map((key) => {
                    const preset = PRECISION_PRESETS[key];
                    return (
                      <button
                        key={key}
                        type="button"
                        className={
                          precision === key
                            ? "precision-card precision-card-active"
                            : "precision-card"
                        }
                        onClick={() => setPrecision(key)}
                      >
                        <span className="precision-card-label">
                          {preset.label}
                        </span>
                        <span className="precision-card-time">
                          {preset.time}
                        </span>
                        <span className="precision-card-note">
                          {preset.note}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </Card>

              {running && (
                <div className="sim-running-banner">
                  <span className="sim-running-spinner" aria-hidden />
                  <div>
                    <p className="sim-running-title">
                      Running the simulation…
                    </p>
                    <p className="sim-running-detail">
                      {chosenPreset.label} precision &mdash; this takes{" "}
                      {chosenPreset.time}. NexGenIQ is building and running
                      many virtual herds. You can leave this screen open;
                      it will not time out.
                    </p>
                  </div>
                </div>
              )}

              <div className="wizard-actions">
                <Button
                  variant="secondary"
                  disabled={running}
                  onClick={() => setStep(1)}
                >
                  Back
                </Button>
                <Button
                  variant="primary"
                  busy={running}
                  onClick={runSimulation}
                >
                  {running
                    ? "Running…"
                    : "Run the simulation →"}
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

              <div className="profit-note">
                <p className="profit-note-label">
                  What &ldquo;simulated herd profit&rdquo; means
                </p>
                <p>
                  This is the modelled whole-herd net return for one
                  year &mdash; total revenue (calves sold, surplus
                  heifers, cull-cow salvage) minus total cost (pasture,
                  fixed costs, replacement females, feed, death loss),
                  run over the full planning horizon, discounted, and
                  averaged across the {result.replicates} simulated
                  herds. It is the baseline the economic values are
                  measured against: each value below is how much this
                  profit moves when a trait is improved.
                </p>
                <p>
                  Read it as a <strong>comparison figure for the
                  operation you described, not a forecast of your actual
                  income</strong>. It is only as accurate as the prices
                  and costs you entered, and a real operation carries
                  costs this model does not (machinery, land, taxes). Use
                  it to compare scenarios &mdash; not as an accounting
                  number.
                </p>
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
