/*
 * The layered help system (Phase 3.5 Part 3).
 *
 * Layer 1 — InfoTip: a small "i" trigger beside any label. Hover or focus
 *           shows a short tooltip; clicking opens the context panel.
 * Layer 2 — ContextPanel: a docked panel showing the structured
 *           what / why / how explanation for the focused topic.
 *
 * A single React context coordinates the two so any InfoTip on the page
 * can drive the one shared panel.
 */

import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";
import { HELP, type HelpEntry } from "../lib/help";

/* ---- shared state ----------------------------------------------------- */
interface HelpContextValue {
  /** The currently displayed help id, or null when the panel is closed. */
  activeId: string | null;
  /** Open the context panel focused on a help id. */
  open: (id: string) => void;
  /** Close the context panel. */
  close: () => void;
}

const HelpContext = createContext<HelpContextValue | null>(null);

export function HelpProvider({ children }: { children: ReactNode }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  return (
    <HelpContext.Provider
      value={{
        activeId,
        open: setActiveId,
        close: () => setActiveId(null),
      }}
    >
      {children}
    </HelpContext.Provider>
  );
}

function useHelp(): HelpContextValue {
  const ctx = useContext(HelpContext);
  if (!ctx) throw new Error("useHelp must be used within a HelpProvider");
  return ctx;
}

/* ---- Layer 1: the info trigger ---------------------------------------- */
export function InfoTip({ id }: { id: string }) {
  const help = useHelp();
  const entry: HelpEntry | undefined = HELP[id];
  if (!entry) return null;

  return (
    <button
      type="button"
      className="infotip"
      aria-label={`Help: ${entry.title}`}
      title={entry.tooltip}
      onClick={() => help.open(id)}
    >
      i
    </button>
  );
}

/* ---- Layer 2: the context panel --------------------------------------- */
export function ContextPanel() {
  const help = useHelp();
  if (!help.activeId) return null;
  const entry = HELP[help.activeId];
  if (!entry) return null;

  return (
    <aside className="context-panel" aria-label="Explanation">
      <div className="context-panel-head">
        <span className="context-panel-title">{entry.title}</span>
        <button
          type="button"
          className="context-panel-close"
          aria-label="Close explanation"
          onClick={help.close}
        >
          ×
        </button>
      </div>

      <p className="context-panel-kicker">What it is</p>
      <p className="context-panel-text">{entry.what}</p>

      <p className="context-panel-kicker">Why it matters</p>
      <p className="context-panel-text">{entry.why}</p>

      <p className="context-panel-kicker">How to choose</p>
      <p className="context-panel-text">{entry.how}</p>
    </aside>
  );
}

/* A convenience hook so other components (e.g. a "Learn more" link) can
 * open the panel programmatically. */
export function useOpenHelp(): (id: string) => void {
  return useHelp().open;
}
