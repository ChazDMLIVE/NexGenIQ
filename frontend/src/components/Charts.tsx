/*
 * Lightweight SVG charts for NexGenIQ results.
 *
 * Hand-built with no charting library: a horizontal bar chart (for
 * rankings and economic values, with optional error bars) and a
 * single-stacked-bar contribution chart (for showing how each trait
 * drove one animal's index value). Both are themed with the app's
 * Graphite / Sage CSS variables and scale to their container width.
 */

import { useId } from "react";

/* One row of a bar chart. */
export interface BarDatum {
  label: string;
  value: number;
  /** Optional +/- error magnitude, drawn as an error bar. */
  error?: number;
  /** Optional secondary caption shown after the value. */
  caption?: string;
}

interface BarChartProps {
  data: BarDatum[];
  /** Unit label appended to each value, e.g. "$/lb". */
  unit?: string;
  /** Accessible title for the chart. */
  title: string;
  /** Number of decimal places for the value labels. */
  decimals?: number;
}

/* Layout constants for the bar chart. */
const ROW_H = 30;
const LABEL_W = 130;
const VALUE_W = 120;
const PAD = 8;

/**
 * A horizontal bar chart. Bars extend right for positive values and left
 * for negative values from a zero line; an optional error bar is drawn on
 * each. Sized to the data; the SVG scales to its container width.
 */
export function BarChart({
  data,
  unit = "",
  title,
  decimals = 1,
}: BarChartProps) {
  const titleId = useId();

  if (data.length === 0) return null;

  /* Plot area sits between the label gutter and the value gutter. */
  const width = 720;
  const plotX = LABEL_W + PAD;
  const plotW = width - LABEL_W - VALUE_W - 2 * PAD;
  const height = data.length * ROW_H + PAD * 2;

  /* Scale: cover the largest magnitude (value or value+error). */
  const maxMag = Math.max(
    ...data.map((d) => Math.abs(d.value) + (d.error ?? 0)),
    1e-9,
  );
  const hasNegative = data.some((d) => d.value < 0);
  /* Zero sits mid-plot if there are negatives, else at the left. */
  const zeroX = hasNegative ? plotX + plotW / 2 : plotX;
  const scale = hasNegative
    ? plotW / 2 / maxMag
    : plotW / maxMag;

  return (
    <svg
      className="nx-chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-labelledby={titleId}
      preserveAspectRatio="xMidYMid meet"
    >
      <title id={titleId}>{title}</title>

      {/* zero line */}
      <line
        x1={zeroX}
        y1={PAD}
        x2={zeroX}
        y2={height - PAD}
        className="nx-chart-axis"
      />

      {data.map((d, i) => {
        const y = PAD + i * ROW_H;
        const cy = y + ROW_H / 2;
        const barLen = Math.abs(d.value) * scale;
        const positive = d.value >= 0;
        const barX = positive ? zeroX : zeroX - barLen;
        const errLen = (d.error ?? 0) * scale;
        return (
          <g key={d.label}>
            {/* trait / animal label */}
            <text
              x={LABEL_W}
              y={cy}
              className="nx-chart-label"
              textAnchor="end"
              dominantBaseline="central"
            >
              {d.label}
            </text>
            {/* the bar */}
            <rect
              x={barX}
              y={y + 6}
              width={Math.max(barLen, 1)}
              height={ROW_H - 12}
              rx={2}
              className={
                positive ? "nx-chart-bar-pos" : "nx-chart-bar-neg"
              }
            />
            {/* error bar */}
            {d.error !== undefined && d.error > 0 && (
              <g className="nx-chart-err">
                <line
                  x1={zeroX + d.value * scale - errLen}
                  y1={cy}
                  x2={zeroX + d.value * scale + errLen}
                  y2={cy}
                />
                <line
                  x1={zeroX + d.value * scale - errLen}
                  y1={cy - 4}
                  x2={zeroX + d.value * scale - errLen}
                  y2={cy + 4}
                />
                <line
                  x1={zeroX + d.value * scale + errLen}
                  y1={cy - 4}
                  x2={zeroX + d.value * scale + errLen}
                  y2={cy + 4}
                />
              </g>
            )}
            {/* value label */}
            <text
              x={width - VALUE_W + PAD}
              y={cy}
              className="nx-chart-value"
              dominantBaseline="central"
            >
              {d.value >= 0 ? "+" : ""}
              {d.value.toFixed(decimals)}
              {unit ? ` ${unit}` : ""}
              {d.caption ? ` ${d.caption}` : ""}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/* One slice of a contribution chart. */
export interface ContributionSlice {
  label: string;
  value: number;
}

interface ContributionChartProps {
  slices: ContributionSlice[];
  title: string;
}

/* A small fixed palette for the contribution slices. */
const SLICE_COLORS = [
  "#3d6b4e",
  "#7d9a82",
  "#4a534f",
  "#a8c0aa",
  "#2f3a37",
  "#5e7d66",
  "#8a918d",
  "#c5d4c6",
];

/**
 * A single horizontal stacked bar showing how each trait contributed to
 * one animal's index value, with a legend. Positive and negative
 * contributions are stacked from a zero line.
 */
export function ContributionChart({
  slices,
  title,
}: ContributionChartProps) {
  const titleId = useId();
  const shown = slices.filter((s) => Math.abs(s.value) > 1e-9);
  if (shown.length === 0) return null;

  const width = 720;
  const barH = 38;
  const height = barH + 16;
  const posTotal = shown
    .filter((s) => s.value > 0)
    .reduce((a, s) => a + s.value, 0);
  const negTotal = shown
    .filter((s) => s.value < 0)
    .reduce((a, s) => a - s.value, 0);
  const span = Math.max(posTotal + negTotal, 1e-9);
  const zeroX = (negTotal / span) * width;
  const scale = width / span;

  /* Walk positive slices rightward from zero, negatives leftward. */
  let posX = zeroX;
  let negX = zeroX;
  const rects = shown.map((s, i) => {
    const w = Math.abs(s.value) * scale;
    let x: number;
    if (s.value >= 0) {
      x = posX;
      posX += w;
    } else {
      negX -= w;
      x = negX;
    }
    return { x, w, color: SLICE_COLORS[i % SLICE_COLORS.length], ...s };
  });

  return (
    <div className="nx-contrib">
      <svg
        className="nx-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-labelledby={titleId}
        preserveAspectRatio="xMidYMid meet"
      >
        <title id={titleId}>{title}</title>
        {rects.map((r) => (
          <rect
            key={r.label}
            x={r.x}
            y={8}
            width={Math.max(r.w, 1)}
            height={barH}
            fill={r.color}
          />
        ))}
        <line
          x1={zeroX}
          y1={2}
          x2={zeroX}
          y2={height - 2}
          className="nx-chart-axis"
        />
      </svg>
      <div className="nx-contrib-legend">
        {rects.map((r) => (
          <span key={r.label} className="nx-contrib-key">
            <span
              className="nx-contrib-swatch"
              style={{ background: r.color }}
            />
            {r.label} ({r.value >= 0 ? "+" : ""}
            {r.value.toFixed(1)})
          </span>
        ))}
      </div>
    </div>
  );
}
