/*
 * Step 1 of the Index Builder — define the breeding goal.
 *
 * Lets the user start from a template, then edit the economic-weight grid:
 * one row per goal trait with an editable weight and a slider. Implements
 * Phase 3.5 Section 4.1.
 */

import type { GoalComponent, Trait } from "../../lib/api";
import { Card, Field } from "../UI";
import { InfoTip } from "../Help";

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
                  </td>
                  <td>{trait?.description ?? ""}</td>
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
                  </option>
                ))}
              </select>
            </Field>
          </div>
        )}
      </Card>
    </>
  );
}
