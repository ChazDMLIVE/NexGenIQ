/*
 * The Index Builder results workspace — the payoff screen.
 *
 * Implements Phase 3.5 Section 4.5: headline metrics, the ranking table
 * with per-animal contribution bars, a detail drawer with the
 * plain-language explanation, the validation panel, and a sensitivity tab.
 */

import { useState } from "react";
import {
  api,
  type Animal,
  type AnimalScore,
  type GoalComponent,
  type IndexBuildResponse,
  type SensitivityResponse,
  type Trait,
} from "../lib/api";
import { Alert, Badge, Button, Card } from "../components/UI";
import { InterpretationPanel } from "../components/InterpretationPanel";
import { BarChart, ContributionChart } from "../components/Charts";
import type { BarDatum, ContributionSlice } from "../components/Charts";
import { toCsv, downloadTextFile, dateStamp } from "../lib/exportCsv";

/* A fixed sage-to-grey ramp for the contribution-bar segments. The order
 * is the index trait order, so a segment's colour is stable across rows. */
const SEGMENT_COLOURS = [
  "#3d6b4e",
  "#5a7e63",
  "#7d9a82",
  "#a6b8a8",
  "#cbd4c9",
  "#dfe4dd",
];

interface ResultsProps {
  result: IndexBuildResponse;
  traits: Trait[];
  goal: { name: string; basis: string; components: GoalComponent[] };
  animals: Animal[];
  mode: string;
  onEdit: () => void;
}

export function ResultsWorkspace({
  result,
  traits,
  goal,
  animals,
  mode,
  onEdit,
}: ResultsProps) {
  const [tab, setTab] = useState<"ranking" | "sensitivity">("ranking");
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [showChecks, setShowChecks] = useState(false);
  const [sensitivity, setSensitivity] =
    useState<SensitivityResponse | null>(null);
  const [sensBusy, setSensBusy] = useState(false);

  const traitName = (code: string) =>
    traits.find((t) => t.code === code)?.name ?? code;

  /* The trait order used for the contribution bars. */
  const indexTraits = goal.components.map((c) => c.trait_code);

  /* --- headline metrics ---------------------------------------------- */
  const scores = result.scores;
  /* The distinct EPD source evaluations the animals came from - shown
     for provenance so the ranking is traceable. */
  const epdEvaluations = [
    ...new Set(
      animals.map((a) => a.evaluation_id).filter((e) => e),
    ),
  ];
  const topValue = scores.length ? scores[0].index_value : 0;
  const spread = scores.length
    ? scores[0].index_value - scores[scores.length - 1].index_value
    : 0;
  const flagged = scores.filter((s) => s.is_partial).length;
  const errorCount = result.validation.filter(
    (v) => v.severity === "error",
  ).length;
  const warnCount = result.validation.filter(
    (v) => v.severity === "warn",
  ).length;
  const infoCount = result.validation.filter(
    (v) => v.severity === "info",
  ).length;

  /* --- validation ERROR: the build did not produce a ranking --------- */
  if (!result.ok) {
    return (
      <>
        <h1 className="page-title">We could not build the index</h1>
        <p className="page-intro">
          NexGenIQ found a problem it could not safely work around. Fix the
          item below and try again — nothing you entered is lost.
        </p>
        {result.validation
          .filter((v) => v.severity === "error")
          .map((v, i) => (
            <Alert key={i} issue={v} />
          ))}
        <div className="wizard-actions">
          <Button variant="secondary" onClick={onEdit}>
            Back to the start
          </Button>
          <span />
        </div>
      </>
    );
  }

  /* --- run sensitivity on demand ------------------------------------- */
  async function runSensitivity() {
    setSensBusy(true);
    try {
      const res = await api.sensitivity({
        goal: { ...goal, source: "manual" },
        animals,
        mode,
        missing_policy: "exclude",
        variation: 0.2,
      });
      setSensitivity(res);
    } finally {
      setSensBusy(false);
    }
  }

  /* Build and download a CSV of the ranked animals: rank, identity,
     index value, confidence bounds, and each trait's contribution. */
  function exportRankingCsv() {
    const header = [
      "Rank",
      "Animal ID",
      "Breed",
      "Index value",
      "CI low",
      "CI high",
      ...indexTraits.map((c) => `${traitName(c)} contribution`),
    ];
    const rows = scores.map((s) => [
      s.rank,
      s.animal_id,
      s.breed,
      s.index_value.toFixed(2),
      s.ci_low != null ? s.ci_low.toFixed(2) : "",
      s.ci_high != null ? s.ci_high.toFixed(2) : "",
      ...indexTraits.map((c) =>
        (s.contributions[c] ?? 0).toFixed(3),
      ),
    ]);
    downloadTextFile(
      `nexgeniq-index-ranking-${dateStamp()}.csv`,
      toCsv(header, rows),
    );
  }

  /* Save this index result so the user can re-open the ranking later.
     The payload carries the goal, animals and mode - enough to rebuild
     the result without re-running the engine. */
  async function saveResult() {
    const name = window.prompt(
      "Name this saved index result:",
      goal.name,
    );
    if (!name) return;
    try {
      await api.saveItem("index_result", name, {
        goal,
        animals,
        mode,
        result,
      });
      window.alert("Saved. You can re-open it from My Saved Work.");
    } catch (err) {
      window.alert(
        err instanceof Error
          ? err.message
          : "Could not save this result.",
      );
    }
  }

  return (
    <>
      {/* Print-only report header - hidden on screen, shown in the PDF. */}
      <div className="print-header">
        <p className="print-header-brand">NexGenIQ</p>
        <p className="print-header-title">
          Selection Index Report &mdash; {goal.name}
        </p>
        <p className="print-header-meta">
          Generated {new Date().toLocaleDateString()} &middot;{" "}
          Index mode: {mode === "blup_index"
            ? "accuracy-adjusted"
            : "standard"}
        </p>
      </div>

      <h1 className="page-title">Your ranked animals</h1>
      <p className="page-intro">
        {scores.length} animals ranked for “{goal.name}”. Click any animal
        to see why it ranks where it does.
      </p>

      <InterpretationPanel interpretation={result.interpretation} />

      {/* ---- headline metrics ---- */}
      <div className="metric-row">
        <div className="metric-card">
          <p className="metric-label">Animals ranked</p>
          <p className="metric-value tnum">{scores.length}</p>
        </div>
        <div className="metric-card">
          <p className="metric-label">Top index value</p>
          <p className="metric-value metric-value-sage tnum">
            {topValue.toFixed(1)}
          </p>
        </div>
        <div className="metric-card">
          <p className="metric-label">Spread (top to bottom)</p>
          <p className="metric-value tnum">{spread.toFixed(1)}</p>
        </div>
        <div className="metric-card">
          <p className="metric-label">Flagged</p>
          <p
            className={
              flagged > 0
                ? "metric-value metric-value-warn tnum"
                : "metric-value tnum"
            }
          >
            {flagged}
          </p>
        </div>
      </div>

      {epdEvaluations.length > 0 && (
        <p className="field-hint" style={{ marginTop: -8 }}>
          {epdEvaluations.length === 1
            ? `EPD source: ${epdEvaluations[0]}.`
            : `EPD sources: ${epdEvaluations.join("; ")}. ` +
              "Animals from different evaluations were placed on a " +
              "common base before ranking."}
        </p>
      )}

      {/* ---- tabs ---- */}
      <div className="tabs">
        <button
          className={`tab ${tab === "ranking" ? "tab-active" : ""}`}
          onClick={() => setTab("ranking")}
        >
          Ranking
        </button>
        <button
          className={`tab ${tab === "sensitivity" ? "tab-active" : ""}`}
          onClick={() => {
            setTab("sensitivity");
            if (!sensitivity) runSensitivity();
          }}
        >
          Sensitivity
        </button>
      </div>

      {/* ---- ranking tab ---- */}
      {tab === "ranking" && (
        <>
        <Card>
          <p className="chart-card-title">Animals ranked by index value</p>
          <BarChart
            title="Index value by animal, best to worst"
            decimals={1}
            data={scores.map(
              (s): BarDatum => ({
                label: s.animal_id,
                value: s.index_value,
                error:
                  s.std_error != null ? s.std_error * 2 : undefined,
              }),
            )}
          />
          <p className="field-hint" style={{ marginTop: 8 }}>
            Bars show each animal's index value; the whiskers show the
            95% confidence range. Animals whose ranges overlap are close
            in estimated merit.
          </p>
        </Card>
        <Card>
          <table className="rank-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Animal</th>
                <th>Breed</th>
                <th>Index value (95% CI)</th>
                <th>Contributions</th>
              </tr>
            </thead>
            <tbody>
              {scores.map((s) => (
                <RankRow
                  key={s.animal_id}
                  score={s}
                  indexTraits={indexTraits}
                  isOpen={openRow === s.animal_id}
                  onToggle={() =>
                    setOpenRow(
                      openRow === s.animal_id ? null : s.animal_id,
                    )
                  }
                  traitName={traitName}
                />
              ))}
            </tbody>
          </table>

          {/* ---- validation / checks panel ---- */}
          <div style={{ marginTop: 16 }}>
            <button
              className="btn btn-quiet"
              onClick={() => setShowChecks(!showChecks)}
            >
              {showChecks ? "▾" : "▸"} Checks: {errorCount} errors ·{" "}
              {warnCount} warnings · {infoCount} notes
            </button>
            {showChecks && (
              <div style={{ marginTop: 8 }}>
                {result.validation.length === 0 ? (
                  <p className="field-hint">
                    No issues — every animal scored cleanly.
                  </p>
                ) : (
                  result.validation.map((v, i) => (
                    <Alert key={i} issue={v} />
                  ))
                )}
              </div>
            )}
          </div>
        </Card>
        </>
      )}

      {/* ---- sensitivity tab ---- */}
      {tab === "sensitivity" && (
        <Card title="How robust is this ranking?">
          {sensBusy && <p className="field-hint">Running sensitivity…</p>}
          {sensitivity && (
            <>
              <p className="sens-summary">{sensitivity.summary}</p>
              <table className="rank-table">
                <thead>
                  <tr>
                    <th>Economic weight varied</th>
                    <th>Ranking stability (±20%)</th>
                    <th>Top animal changes?</th>
                  </tr>
                </thead>
                <tbody>
                  {sensitivity.entries.map((e) => (
                    <tr key={e.trait_code}>
                      <td>{traitName(e.trait_code)}</td>
                      <td className="tnum">
                        {(
                          ((e.rank_corr_low + e.rank_corr_high) / 2) *
                          100
                        ).toFixed(0)}
                        % stable
                      </td>
                      <td>
                        {e.top_changed ? (
                          <Badge tone="warn">Yes</Badge>
                        ) : (
                          <Badge tone="sage">No</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </Card>
      )}

      {/* ---- actions ---- */}
      <div className="wizard-actions no-print">
        <Button variant="secondary" onClick={onEdit}>
          Adjust and rebuild
        </Button>
        <div className="export-actions">
          <Button variant="secondary" onClick={saveResult}>
            Save result
          </Button>
          <Button variant="secondary" onClick={exportRankingCsv}>
            Export CSV
          </Button>
          <Button
            variant="secondary"
            onClick={() => window.print()}
          >
            Export PDF
          </Button>
        </div>
      </div>
    </>
  );
}

/* --------------------------------------------------------------------- *
 * One ranking-table row, plus its expandable detail drawer.
 * ------------------------------------------------------------------- */
function RankRow({
  score,
  indexTraits,
  isOpen,
  onToggle,
  traitName,
}: {
  score: AnimalScore;
  indexTraits: string[];
  isOpen: boolean;
  onToggle: () => void;
  traitName: (code: string) => string;
}) {
  /* Build the contribution bar from the absolute contribution sizes. */
  const absTotal =
    indexTraits.reduce(
      (sum, code) => sum + Math.abs(score.contributions[code] ?? 0),
      0,
    ) || 1;

  const rowClass = score.is_partial
    ? "rank-row rank-row-flag"
    : score.rank === 1
      ? "rank-row rank-row-top"
      : "rank-row";

  return (
    <>
      <tr className={rowClass} onClick={onToggle}>
        <td className="rank-num">{score.rank}</td>
        <td>
          <strong>{score.animal_id}</strong>
          {score.is_partial && (
            <span style={{ marginLeft: 6 }}>
              <Badge tone="warn">partial</Badge>
            </span>
          )}
        </td>
        <td>
          <Badge tone="neutral">{score.breed}</Badge>
        </td>
        <td>
          <span className="rank-index tnum">
            {score.index_value.toFixed(1)}
          </span>
          {score.ci_low != null && score.ci_high != null && (
            <span className="rank-ci tnum">
              {" "}
              [{score.ci_low.toFixed(0)}, {score.ci_high.toFixed(0)}]
            </span>
          )}
        </td>
        <td>
          <div className="contrib-bar">
            {indexTraits.map((code, i) => {
              const pct =
                (Math.abs(score.contributions[code] ?? 0) / absTotal) *
                100;
              return (
                <span
                  key={code}
                  className="contrib-seg"
                  style={{
                    width: `${pct}%`,
                    background:
                      SEGMENT_COLOURS[i % SEGMENT_COLOURS.length],
                  }}
                  title={`${traitName(code)}: ${(
                    score.contributions[code] ?? 0
                  ).toFixed(1)}`}
                />
              );
            })}
          </div>
        </td>
      </tr>

      {isOpen && (
        <tr>
          <td colSpan={5}>
            <div className="drawer">
              <p className="drawer-explain">{score.explanation}</p>
              <p className="chart-card-title" style={{ marginTop: 4 }}>
                What drove this animal's index value
              </p>
              <ContributionChart
                title={`Trait contributions for ${score.animal_id}`}
                slices={indexTraits.map(
                  (code): ContributionSlice => ({
                    label: traitName(code),
                    value: score.contributions[code] ?? 0,
                  }),
                )}
              />
              {indexTraits.map((code) => {
                const value = score.contributions[code] ?? 0;
                const max =
                  Math.max(
                    ...indexTraits.map((c) =>
                      Math.abs(score.contributions[c] ?? 0),
                    ),
                  ) || 1;
                return (
                  <div key={code} className="contrib-detail-row">
                    <span className="contrib-detail-label">
                      {traitName(code)}
                    </span>
                    <span className="contrib-detail-track">
                      <span
                        className="contrib-detail-fill"
                        style={{
                          width: `${(Math.abs(value) / max) * 100}%`,
                        }}
                      />
                    </span>
                    <span className="contrib-detail-value tnum">
                      {value.toFixed(1)}
                    </span>
                  </div>
                );
              })}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}
