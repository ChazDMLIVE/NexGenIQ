/*
 * Shared UI primitives for NexGenIQ.
 *
 * Small, consistent building blocks implementing the component library of
 * Phase 3.5 Section 1.4. Every component styles itself entirely from the
 * design tokens via class names defined in app.css.
 */

import type { ButtonHTMLAttributes, ReactNode } from "react";
import type { ValidationIssue } from "../lib/api";
import { InfoTip } from "./Help";

/* ---- Buttons ---------------------------------------------------------- */
type ButtonVariant = "primary" | "secondary" | "quiet";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  busy?: boolean;
}

/** A button. `primary` for the main action, `secondary` for cancel/back,
 *  `quiet` for tertiary actions. Shows a spinner and disables while busy. */
export function Button({
  variant = "secondary",
  busy = false,
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant}`}
      disabled={disabled || busy}
      {...rest}
    >
      {busy && <span className="btn-spinner" aria-hidden="true" />}
      {children}
    </button>
  );
}

/* ---- Card -------------------------------------------------------------- */
interface CardProps {
  /** Optional card title shown in a header row. */
  title?: string;
  /** Optional help id — renders an InfoTip beside the title. */
  helpId?: string;
  /** Optional element shown at the right of the header (e.g. an action). */
  action?: ReactNode;
  children: ReactNode;
}

/** The primary grouping surface — a white card on the warm canvas. */
export function Card({ title, helpId, action, children }: CardProps) {
  return (
    <section className="card">
      {(title || action) && (
        <header className="card-head">
          <h2 className="card-title">
            {title}
            {helpId && <InfoTip id={helpId} />}
          </h2>
          {action}
        </header>
      )}
      <div className="card-body">{children}</div>
    </section>
  );
}

/* ---- Field ------------------------------------------------------------- */
interface FieldProps {
  label: string;
  helpId?: string;
  /** Persistent helper text shown beneath the control (guided mode). */
  hint?: string;
  children: ReactNode;
}

/** A labelled form field: label + optional InfoTip + control + hint. */
export function Field({ label, helpId, hint, children }: FieldProps) {
  return (
    <div className="field">
      <label className="field-label">
        {label}
        {helpId && <InfoTip id={helpId} />}
      </label>
      {children}
      {hint && <p className="field-hint">{hint}</p>}
    </div>
  );
}

/* ---- Stepper ----------------------------------------------------------- */
interface StepperProps {
  steps: string[];
  /** 1-based index of the current step. */
  current: number;
  /** Called when a step is clicked (only completed steps are clickable). */
  onStepClick?: (step: number) => void;
}

/** The wizard step indicator (Phase 3.5 Section 4, the four-step flow). */
export function Stepper({ steps, current, onStepClick }: StepperProps) {
  return (
    <nav className="stepper" aria-label="Progress">
      {steps.map((label, i) => {
        const n = i + 1;
        const state =
          n < current ? "done" : n === current ? "current" : "future";
        const clickable = n < current && onStepClick;
        return (
          <div key={label} className="stepper-item">
            <button
              type="button"
              className={`stepper-dot stepper-${state}`}
              disabled={!clickable}
              onClick={() => clickable && onStepClick(n)}
              aria-current={n === current ? "step" : undefined}
            >
              {n < current ? "✓" : n}
            </button>
            <span className={`stepper-label stepper-label-${state}`}>
              {label}
            </span>
            {i < steps.length - 1 && <span className="stepper-line" />}
          </div>
        );
      })}
    </nav>
  );
}

/* ---- Badge ------------------------------------------------------------- */
type BadgeTone = "neutral" | "sage" | "warn";

/** A small rounded label — breed, percentile, status. */
export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: BadgeTone;
  children: ReactNode;
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

/* ---- Alert ------------------------------------------------------------- */
/** An inline validation alert. Maps an engine ValidationIssue to a
 *  semantic-coloured block with an icon, message and optional fix hint. */
export function Alert({ issue }: { issue: ValidationIssue }) {
  const label =
    issue.severity === "error"
      ? "Problem"
      : issue.severity === "warn"
        ? "Heads up"
        : "Note";
  return (
    <div className={`alert alert-${issue.severity}`} role="status">
      <p className="alert-title">{label}</p>
      <p className="alert-message">{issue.message}</p>
      {issue.fix_hint && (
        <p className="alert-fix">How to fix: {issue.fix_hint}</p>
      )}
    </div>
  );
}

/* ---- Empty state ------------------------------------------------------- */
/** A designed empty state — never a blank screen (Phase 3.5 Section 1.4). */
export function EmptyState({
  message,
  children,
}: {
  message: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <p className="empty-state-message">{message}</p>
      {children}
    </div>
  );
}
