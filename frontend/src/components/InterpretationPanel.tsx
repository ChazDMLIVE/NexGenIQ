/*
 * Plain-language result interpretation panel.
 *
 * Renders a layered, rule-based interpretation of a result (an index
 * ranking or an MEV derivation): a headline and short readout anyone can
 * act on, an expandable detail section, any cautions, and a standing
 * disclaimer that the interpretation is informational - not a
 * recommendation to take any action.
 *
 * The interpretation text comes from the engines, so it is consistent
 * everywhere and never invented in the UI.
 */

import { useState } from "react";
import type { Interpretation } from "../lib/api";

interface InterpretationPanelProps {
  interpretation: Interpretation;
}

export function InterpretationPanel({
  interpretation,
}: InterpretationPanelProps) {
  const [showDetail, setShowDetail] = useState(false);

  const { headline, readout, detail, cautions, disclaimer } =
    interpretation;

  /* Nothing to show if the engine returned an empty interpretation. */
  if (!headline && !readout) return null;

  return (
    <section className="interp-panel">
      {headline && <p className="interp-headline">{headline}</p>}
      {readout && <p className="interp-readout">{readout}</p>}

      {detail.length > 0 && (
        <>
          <button
            type="button"
            className="docs-toggle"
            onClick={() => setShowDetail((v) => !v)}
            aria-expanded={showDetail}
          >
            {showDetail
              ? "Hide the detailed explanation"
              : "Explain this in more detail"}
          </button>
          {showDetail && (
            <ul className="interp-detail">
              {detail.map((d, i) => (
                <li key={i}>{d}</li>
              ))}
            </ul>
          )}
        </>
      )}

      {cautions.length > 0 && (
        <div className="interp-cautions">
          <p className="interp-cautions-label">
            Worth weighing before you act:
          </p>
          <ul>
            {cautions.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}

      {disclaimer && (
        <p className="interp-disclaimer">{disclaimer}</p>
      )}
    </section>
  );
}
