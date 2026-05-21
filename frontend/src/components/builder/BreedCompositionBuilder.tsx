/*
 * Breed-composition builder for the Herd Simulation wizard.
 *
 * A herd is rarely one pure breed. This component lets the user describe
 * the real breed makeup of a group of animals (the cow herd or the bull
 * battery) as one or more composition CLASSES: each class is a fraction
 * of the group and itself a mix of breeds. A straight-Angus herd is one
 * class, {Angus: 100%}; a herd that is 70% Angus-Hereford F1 and 30%
 * straight Angus is two classes.
 *
 * The component validates that the class fractions sum to 100% and that
 * each class's breed fractions sum to 100%, and reports the herd-level
 * average breed composition so the user can see the overall makeup.
 */

import type { BreedCompositionIn } from "../../lib/api";

/* The breeds NexGenIQ has genetic parameters for. */
export const KNOWN_BREEDS = [
  "Angus",
  "Red Angus",
  "Hereford",
  "Simmental",
  "Charolais",
  "Gelbvieh",
  "Limousin",
  "Shorthorn",
  "Salers",
  "Maine-Anjou",
];

interface BreedCompositionBuilderProps {
  /** Heading for this group, e.g. "Cow herd" or "Bull battery". */
  label: string;
  /** A short plain-language explanation shown under the heading. */
  hint: string;
  /** The composition classes for this group. */
  classes: BreedCompositionIn[];
  /** Called with the updated class list on any edit. */
  onChange: (classes: BreedCompositionIn[]) => void;
}

/* Sum the values of a breed-fraction map. */
function sumBreeds(breeds: Record<string, number>): number {
  return Object.values(breeds).reduce((a, b) => a + b, 0);
}

/* Round to 3 dp for display without floating-point noise. */
function r3(x: number): number {
  return Math.round(x * 1000) / 1000;
}

/**
 * Return the herd-level average breed composition across all classes:
 * each class contributes its breeds weighted by its herd fraction.
 */
export function averageComposition(
  classes: BreedCompositionIn[],
): Record<string, number> {
  const avg: Record<string, number> = {};
  for (const cls of classes) {
    for (const [breed, frac] of Object.entries(cls.breeds)) {
      avg[breed] = (avg[breed] ?? 0) + cls.fraction * frac;
    }
  }
  return avg;
}

export function BreedCompositionBuilder({
  label,
  hint,
  classes,
  onChange,
}: BreedCompositionBuilderProps) {
  const classTotal = classes.reduce((a, c) => a + c.fraction, 0);
  const classesValid = Math.abs(classTotal - 1.0) < 1e-6;

  /* --- class-level edits --------------------------------------------- */
  function updateClassFraction(idx: number, fraction: number) {
    onChange(
      classes.map((c, i) => (i === idx ? { ...c, fraction } : c)),
    );
  }

  function addClass() {
    onChange([...classes, { fraction: 0, breeds: { Angus: 1.0 } }]);
  }

  function removeClass(idx: number) {
    if (classes.length <= 1) return;
    onChange(classes.filter((_, i) => i !== idx));
  }

  /* --- breed-level edits within a class ------------------------------ */
  function updateBreedFraction(
    classIdx: number,
    breed: string,
    fraction: number,
  ) {
    onChange(
      classes.map((c, i) =>
        i === classIdx
          ? { ...c, breeds: { ...c.breeds, [breed]: fraction } }
          : c,
      ),
    );
  }

  function changeBreedName(
    classIdx: number,
    oldBreed: string,
    newBreed: string,
  ) {
    onChange(
      classes.map((c, i) => {
        if (i !== classIdx) return c;
        const breeds: Record<string, number> = {};
        for (const [b, f] of Object.entries(c.breeds)) {
          breeds[b === oldBreed ? newBreed : b] = f;
        }
        return { ...c, breeds };
      }),
    );
  }

  function addBreedToClass(classIdx: number) {
    onChange(
      classes.map((c, i) => {
        if (i !== classIdx) return c;
        /* Pick the first known breed not already in this class. */
        const used = new Set(Object.keys(c.breeds));
        const next = KNOWN_BREEDS.find((b) => !used.has(b));
        if (!next) return c;
        return { ...c, breeds: { ...c.breeds, [next]: 0 } };
      }),
    );
  }

  function removeBreedFromClass(classIdx: number, breed: string) {
    onChange(
      classes.map((c, i) => {
        if (i !== classIdx) return c;
        if (Object.keys(c.breeds).length <= 1) return c;
        const breeds = { ...c.breeds };
        delete breeds[breed];
        return { ...c, breeds };
      }),
    );
  }

  return (
    <div className="breed-builder">
      <p className="breed-builder-label">{label}</p>
      <p className="field-hint">{hint}</p>

      {classes.map((cls, ci) => {
        const breedTotal = sumBreeds(cls.breeds);
        const breedValid = Math.abs(breedTotal - 1.0) < 1e-6;
        const usedBreeds = new Set(Object.keys(cls.breeds));
        const canAddBreed = KNOWN_BREEDS.some(
          (b) => !usedBreeds.has(b),
        );
        return (
          <div key={ci} className="breed-class">
            <div className="breed-class-head">
              <span className="breed-class-title">
                {classes.length > 1
                  ? `Group ${ci + 1}`
                  : "Breed makeup"}
              </span>
              {classes.length > 1 && (
                <label className="breed-class-frac">
                  Share of {label.toLowerCase()}:
                  <input
                    type="number"
                    step="0.05"
                    min={0}
                    max={1}
                    value={cls.fraction}
                    onChange={(e) =>
                      updateClassFraction(
                        ci,
                        Number(e.target.value),
                      )
                    }
                  />
                </label>
              )}
              {classes.length > 1 && (
                <button
                  type="button"
                  className="goal-remove"
                  aria-label={`Remove group ${ci + 1}`}
                  onClick={() => removeClass(ci)}
                >
                  ×
                </button>
              )}
            </div>

            <table className="breed-table">
              <thead>
                <tr>
                  <th>Breed</th>
                  <th>Fraction of this animal</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {Object.entries(cls.breeds).map(([breed, frac]) => (
                  <tr key={breed}>
                    <td>
                      <select
                        value={breed}
                        onChange={(e) =>
                          changeBreedName(
                            ci,
                            breed,
                            e.target.value,
                          )
                        }
                      >
                        {KNOWN_BREEDS.filter(
                          (b) => b === breed || !usedBreeds.has(b),
                        ).map((b) => (
                          <option key={b} value={b}>
                            {b}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <input
                        type="number"
                        step="0.05"
                        min={0}
                        max={1}
                        value={frac}
                        onChange={(e) =>
                          updateBreedFraction(
                            ci,
                            breed,
                            Number(e.target.value),
                          )
                        }
                      />
                    </td>
                    <td>
                      {Object.keys(cls.breeds).length > 1 && (
                        <button
                          type="button"
                          className="goal-remove"
                          aria-label={`Remove ${breed}`}
                          onClick={() =>
                            removeBreedFromClass(ci, breed)
                          }
                        >
                          ×
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {canAddBreed && (
              <button
                type="button"
                className="goal-estimate-link"
                onClick={() => addBreedToClass(ci)}
              >
                + Add a breed to this group (for a cross)
              </button>
            )}

            {!breedValid && (
              <p className="breed-warn">
                The breed fractions in this group add up to{" "}
                {r3(breedTotal)}, not 1.0. They must sum to 1.0 (100%)
                for a single animal.
              </p>
            )}
          </div>
        );
      })}

      <button
        type="button"
        className="goal-estimate-link"
        onClick={addClass}
      >
        + Add another group (a different breed makeup)
      </button>

      {!classesValid && classes.length > 1 && (
        <p className="breed-warn">
          The group shares add up to {r3(classTotal)}, not 1.0. They
          must sum to 1.0 (100%) of the {label.toLowerCase()}.
        </p>
      )}
    </div>
  );
}
