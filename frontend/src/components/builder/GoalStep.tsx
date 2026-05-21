/*
 * Step 1 of the Index Builder — define the breeding goal.
 *
 * Lets the user start from a template, then edit the economic-weight grid:
 * one row per goal trait with an editable weight and a slider. Implements
 * Phase 3.5 Section 4.1.
 *
 * Each row also offers a guided economic-value estimator (the "Help me
 * price this" action), so a user who does not run the Herd Simulation can
 * still arrive at a defensible economic weight.
 */

import { useState } from "react";
import type { GoalComponent, Trait } from "../../lib/api";
import { Card, Field } from "../UI";
import { InfoTip } from "../Help";
import { EconEstimator } from "./EconEstimator";

interface GoalTemplate {
  id: string;
  name: string;
  desc: string;
  basis: string;
  components: GoalComponent[];
}

interface GoalStepProps {
  templates: GoalTemplate[];
  onApplyTemplate: (t: GoalTemplate) => void;
  traits: Trait[];
  goalName: string;
  onGoalName: (v: string) => void;
  basis: string;
  onBasis: (v: string) => void;
  components: GoalComponent[];
  onComponents: (c: GoalComponent[]) => void;
}

/* The trait codes the economic-value estimator has a recipe for. Kept in
   step with the osit-index econ_estimator module. */
const ESTIMATOR_TRAITS = new Set([
  "WW", "YW", "CW", "MARB", "REA", "FAT", "CED", "HP", "STAY",
  "MW", "MILK", "DOC", "DMI", "PAP", "PAP_L",
]);

export function GoalStep({
  templates,
  onApplyTemplate,
  traits,
  goalName,
  onGoalName,
  basis,
  onBasis,
  components,
  onComponents,
}: GoalStepProps) {
  const traitByCode = new Map(traits.map((t) => [t.code, t]));

  /* When set, the economic-value estimator modal is open for this trait. */
  const [estimatorTrait, setEstimatorTrait] = useState<string | null>(
    null,
  );

  function updateWeight(code: string, weight: number) {
    onComponents(
      components.map((c) =>
        c.trait_code === code ? { ...c, economic_weight: weight } : c,
      ),
    );
  }

  function removeTrait(code: string) {
    onComponents(components.filter((c) => c.trait_code !== code));
  }

  function addTrait(code: string) {
    if (!code || components.some((c) => c.trait_code === code)) return;
    onComponents([...components, { trait_code: code, economic_weight: 1 }]);
  }

  /* Traits not yet in the goal, for the "add trait" picker. */
  const available = traits.filter(
    (t) => !components.some((c) => c.trait_code === t.code),
  );

  return (
    <>
      {/* --- start-from cards --- */}
      <div className="start-cards">
        {templates.map((t) => (
          <button
            key={t.id}
            type="button"
            className="start-card"
            onClick={() => onApplyTemplate(t)}
          >
            <p className="start-card-title">{t.name}</p>
            <p className="start-card-desc">{t.desc}</p>
          </button>
        ))}
      </div>

      {/* --- the goal --- */}
      <Card title="Your breeding goal" helpId="goal">
        <Field label="Name this index">
          <input
            type="text"
            value={goalName}
            onChange={(e) => onGoalName(e.target.value)}
          />
        </Field>

        <Field
          label="Economic basis"
          helpId="basis"
          hint="The common yardstick for every economic weight. 'Per cow
                exposed' suits most cow-calf operations."
        >
          <select value={basis} onChange={(e) => onBasis(e.target.value)}>
            <option value="per_cow_exposed">Per cow exposed</option>
            <option value="per_calf">Per calf</option>
            <option value="per_unit">Per unit</option>
          </select>
        </Field>

        <p className="field-hint" style={{ marginBottom: 4 }}>
          Not sure what a trait is worth? Use “Help me price this” on any
          row for a guided estimate — or run the Herd Simulation for a
          full economic-value derivation.
        </p>

        <table className="goal-grid">
          <thead>
            <tr>
              <th>Trait</th>
              <th>
                Economic weight
                <InfoTip id="economic_weight" />
              </th>
              <th>What it is</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {components.map((c) => {
              const trait = traitByCode.get(c.trait_code);
              const canEstimate = ESTIMATOR_TRAITS.has(c.trait_code);
              return (
                <tr key={c.trait_code}>
                  <td>{trait?.name ?? c.trait_code}</td>
                  <td>
                    <div className="goal-grid-weight">
                      <input
                        type="number"
                        step="0.05"
                        value={c.economic_weight}
                        onChange={(e) =>
                          updateWeight(
                            c.trait_code,
                            Number(e.target.value),
                          )
                        }
                      />
                      <span className="goal-grid-units">
                        $/{trait?.units ?? "unit"}
                      </span>
                      <input
                        type="range"
                        min={-20}
                        max={60}
                        step="0.5"
                        value={c.economic_weight}
                        onChange={(e) =>
                          updateWeight(
                            c.trait_code,
                            Number(e.target.value),
                          )
                        }
                        aria-label={`Weight for ${trait?.name}`}
                      />
                    </div>
                    {canEstimate && (
                      <button
                        type="button"
                        className="goal-estimate-link"
                        onClick={() =>
                          setEstimatorTrait(c.trait_code)
                        }
                      >
                        Help me price this
                      </button>
                    )}
                  </td>
                  <td>
                    {trait?.description ?? ""}
                    {c.trait_code === "PAP_L" ? (
                      <p
                        className="goal-research-note"
                        style={{ marginTop: 4 }}
                      >
                        Research trait. Latent-scale PAP is a
                        boundary-aware research phenotype — no breed
                        association currently publishes a latent PAP EPD.
                        Use it only if you have latent-scale PAP values
                        from a research evaluation; for routine use,
                        choose the standard PAP trait instead.
                      </p>
                    ) : (
                      trait?.breeds &&
                      trait.breeds.length > 0 && (
                        <p
                          className="field-hint"
                          style={{
                            marginTop: 4,
                            fontStyle: "italic",
                          }}
                        >
                          EPD published only by:{" "}
                          {trait.breeds.join(", ")}. Make sure your
                          animals are of one of these breeds.
                        </p>
                      )
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="goal-remove"
                      aria-label={`Remove ${trait?.name}`}
                      onClick={() => removeTrait(c.trait_code)}
                    >
                      ×
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {available.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Field label="Add another trait">
              <select
                value=""
                onChange={(e) => addTrait(e.target.value)}
              >
                <option value="">Choose a trait to add…</option>
                {available.map((t) => (
                  <option key={t.code} value={t.code}>
                    {t.name} ({t.category})
                    {t.breeds && t.breeds.length > 0
                      ? ` — ${t.breeds.join("/")} only`
                      : ""}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        )}
      </Card>

      {estimatorTrait && (
        <EconEstimator
          traitCode={estimatorTrait}
          traitName={
            traitByCode.get(estimatorTrait)?.name ?? estimatorTrait
          }
          onApply={(value) => {
            updateWeight(estimatorTrait, Number(value.toFixed(3)));
            setEstimatorTrait(null);
          }}
          onClose={() => setEstimatorTrait(null)}
        />
      )}
    </>
  );
}
