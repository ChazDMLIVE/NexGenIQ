/*
 * Economic-value estimator modal.
 *
 * For users who do not run the herd simulation, this walks them through a
 * short set of plain-language questions for one trait and computes a
 * starting economic value from an explicit, documented formula. The
 * computed value can be applied directly to the breeding-goal grid.
 *
 * The recipes, formulas, and the estimate itself come from the backend
 * (osit-index econ_estimator), so the UI never hard-codes economics.
 */

import { useEffect, useState } from "react";
import {
  api,
  type EstimateResult,
  type EstimatorRecipe,
} from "../../lib/api";
import { Button } from "../UI";

interface EconEstimatorProps {
  /** The trait code to estimate a value for. */
  traitCode: string;
  /** Human-readable trait name, for the heading. */
  traitName: string;
  /** Called with the estimated value when the user accepts it. */
  onApply: (value: number) => void;
  /** Called to dismiss the estimator without applying. */
  onClose: () => void;
}

export function EconEstimator({
  traitCode,
  traitName,
  onApply,
  onClose,
}: EconEstimatorProps) {
  const [recipe, setRecipe] = useState<EstimatorRecipe | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [result, setResult] = useState<EstimateResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  /* Load this trait's recipe and seed the answers with its defaults. */
  useEffect(() => {
    let cancelled = false;
    api
      .econEstimatorRecipes()
      .then((recipes) => {
        if (cancelled) return;
        const r = recipes.find((x) => x.trait_code === traitCode) ?? null;
        setRecipe(r);
        if (r) {
          const seed: Record<string, number> = {};
          for (const q of r.questions) seed[q.key] = q.default;
          setAnswers(seed);
        }
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError(
          "Could not load the estimator. You can still type an " +
            "economic value in by hand.",
        );
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [traitCode]);

  /* Re-estimate whenever the answers change. */
  useEffect(() => {
    if (!recipe) return;
    let cancelled = false;
    api
      .estimateEconValue(traitCode, answers)
      .then((r) => {
        if (!cancelled) setResult(r);
      })
      .catch(() => {
        if (!cancelled) setError("Could not compute the estimate.");
      });
    return () => {
      cancelled = true;
    };
  }, [recipe, answers, traitCode]);

  function setAnswer(key: string, value: number) {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="estimator-overlay" role="dialog" aria-modal="true">
      <div className="estimator-modal">
        <div className="estimator-header">
          <h2 className="estimator-title">
            What is {traitName} worth to you?
          </h2>
          <button
            type="button"
            className="goal-remove"
            aria-label="Close"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <p className="estimator-intro">
          Answer a few questions about your operation and NexGenIQ will
          work out a starting economic value for this trait. Every number
          is based on a formula you can see — adjust the answers and the
          estimate updates. For a fuller, joint analysis, use the Herd
          Simulation instead.
        </p>

        {loading && <p className="field-hint">Loading the estimator…</p>}

        {error && (
          <p className="auth-error" style={{ marginTop: 8 }}>
            {error}
          </p>
        )}

        {recipe && (
          <>
            <div className="estimator-questions">
              {recipe.questions.map((q) => (
                <div key={q.key} className="estimator-question">
                  <label className="estimator-q-label">
                    {q.prompt}
                  </label>
                  <p className="field-hint">{q.help_text}</p>
                  <div className="estimator-q-input">
                    <input
                      type="number"
                      step="0.01"
                      value={answers[q.key] ?? q.default}
                      min={q.minimum}
                      max={q.maximum}
                      onChange={(e) =>
                        setAnswer(q.key, Number(e.target.value))
                      }
                    />
                    <span className="goal-grid-units">{q.units}</span>
                  </div>
                </div>
              ))}
            </div>

            {result && (
              <div className="estimator-result">
                <p className="estimator-result-label">
                  Estimated economic value
                </p>
                <p className="estimator-result-value tnum">
                  {result.economic_value >= 0 ? "+" : ""}
                  {result.economic_value.toFixed(2)}
                </p>
                <p className="field-hint">
                  Formula: {result.formula_text}
                </p>
                <p className="field-hint">{result.basis_note}</p>
              </div>
            )}

            <div className="estimator-actions">
              <Button variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button
                variant="primary"
                disabled={!result}
                onClick={() => {
                  if (result) onApply(result.economic_value);
                }}
              >
                Use this value →
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
