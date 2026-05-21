/*
 * Multi-band weight x sex pricing editor for the Herd Simulation wizard.
 *
 * Feeder cattle are not priced at a single number: lighter calves bring
 * more per hundredweight than heavy ones, and steers and heifers price
 * differently. This component lets the user enter a realistic price grid
 * - one or more weight ranges per sex - which the simulation uses to
 * value each calf by its actual weight and sex.
 *
 * The osit-sim engine's PriceBand already supports exactly this; the
 * editor simply exposes it.
 */

import type { PriceBandIn } from "../../lib/api";

interface PriceBandEditorProps {
  /** All price bands across every sex class. */
  bands: PriceBandIn[];
  /** Called with the updated band list on any edit. */
  onChange: (bands: PriceBandIn[]) => void;
}

/* The sex classes priced separately, with display labels. */
const SEX_CLASSES: { code: string; label: string }[] = [
  { code: "S", label: "Steer calves" },
  { code: "F", label: "Heifer calves" },
  { code: "C", label: "Cull cows" },
];

export function PriceBandEditor({
  bands,
  onChange,
}: PriceBandEditorProps) {
  function bandsForSex(sex: string): PriceBandIn[] {
    return bands.filter((b) => b.sex === sex);
  }

  function updateBand(
    target: PriceBandIn,
    patch: Partial<PriceBandIn>,
  ) {
    onChange(
      bands.map((b) => (b === target ? { ...b, ...patch } : b)),
    );
  }

  function addBand(sex: string) {
    const existing = bandsForSex(sex);
    /* New band starts where the last one ended. */
    const low = existing.length
      ? existing[existing.length - 1].high
      : 0;
    onChange([
      ...bands,
      { sex, low, high: low + 100, price_per_cwt: 180 },
    ]);
  }

  function removeBand(target: PriceBandIn) {
    onChange(bands.filter((b) => b !== target));
  }

  return (
    <div className="price-editor">
      <p className="field-hint" style={{ marginBottom: 12 }}>
        Enter your sale prices per hundredweight (cwt) by weight range.
        Lighter calves usually bring more per cwt than heavy ones, so
        more than one band per sex gives the simulation a realistic
        price for every calf. The simulation prices each calf from the
        band its weight and sex fall into.
      </p>

      {SEX_CLASSES.map(({ code, label }) => {
        const sexBands = bandsForSex(code);
        return (
          <div key={code} className="price-sex-block">
            <p className="price-sex-label">{label}</p>
            <table className="breed-table">
              <thead>
                <tr>
                  <th>Weight from (lb)</th>
                  <th>Weight to (lb)</th>
                  <th>Price ($/cwt)</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {sexBands.map((band, i) => (
                  <tr key={i}>
                    <td>
                      <input
                        type="number"
                        step="50"
                        min={0}
                        value={band.low}
                        onChange={(e) =>
                          updateBand(band, {
                            low: Number(e.target.value),
                          })
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="50"
                        min={0}
                        value={band.high}
                        onChange={(e) =>
                          updateBand(band, {
                            high: Number(e.target.value),
                          })
                        }
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        step="1"
                        min={0}
                        value={band.price_per_cwt}
                        onChange={(e) =>
                          updateBand(band, {
                            price_per_cwt: Number(
                              e.target.value,
                            ),
                          })
                        }
                      />
                    </td>
                    <td>
                      {sexBands.length > 1 && (
                        <button
                          type="button"
                          className="goal-remove"
                          aria-label="Remove this price band"
                          onClick={() => removeBand(band)}
                        >
                          ×
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button
              type="button"
              className="goal-estimate-link"
              onClick={() => addBand(code)}
            >
              + Add a weight band for {label.toLowerCase()}
            </button>
          </div>
        );
      })}
    </div>
  );
}

/* A sensible default price grid used to seed the editor. */
export function defaultPriceBands(): PriceBandIn[] {
  return [
    { sex: "S", low: 0, high: 500, price_per_cwt: 200 },
    { sex: "S", low: 500, high: 600, price_per_cwt: 192 },
    { sex: "S", low: 600, high: 9999, price_per_cwt: 178 },
    { sex: "F", low: 0, high: 500, price_per_cwt: 185 },
    { sex: "F", low: 500, high: 600, price_per_cwt: 176 },
    { sex: "F", low: 600, high: 9999, price_per_cwt: 162 },
    { sex: "C", low: 0, high: 9999, price_per_cwt: 110 },
  ];
}
