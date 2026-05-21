/*
 * My Saved Work page.
 *
 * Lists everything the current user has explicitly saved - index
 * results, herd-simulation results, and breeding goals - newest first.
 * Each item can be opened (its content is shown inline) or deleted.
 * A saved breeding goal can be loaded straight into the Index Builder.
 *
 * Nothing is saved automatically; this page only ever shows items the
 * user chose to keep, and deleting one removes it for good.
 */

import { useEffect, useState } from "react";
import {
  api,
  type GoalComponent,
  type SavedItem,
  type SavedItemSummary,
} from "../lib/api";
import { Button, Card, EmptyState } from "../components/UI";

interface SavedWorkProps {
  /** Load a saved breeding goal into the Index Builder. */
  onUseGoal: (components: GoalComponent[], name: string) => void;
}

/* A human label for each saved-item kind. */
const KIND_LABEL: Record<string, string> = {
  index_result: "Index ranking",
  simulation_result: "Herd simulation",
  breeding_goal: "Breeding goal",
};

export function SavedWork({ onUseGoal }: SavedWorkProps) {
  const [items, setItems] = useState<SavedItemSummary[] | null>(null);
  const [error, setError] = useState("");
  /* The item currently expanded for viewing, fetched in full. */
  const [openItem, setOpenItem] = useState<SavedItem | null>(null);
  const [openBusy, setOpenBusy] = useState(false);

  /* Load the user's saved items on mount. */
  useEffect(() => {
    let cancelled = false;
    api
      .listSaved()
      .then((list) => {
        if (!cancelled) setItems(list);
      })
      .catch(() => {
        if (!cancelled)
          setError("Could not load your saved work.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function openSaved(id: string) {
    setOpenBusy(true);
    setError("");
    try {
      const full = await api.getSaved(id);
      setOpenItem(full);
    } catch {
      setError("Could not open that saved item.");
    } finally {
      setOpenBusy(false);
    }
  }

  async function deleteSaved(id: string, name: string) {
    if (
      !window.confirm(
        `Delete the saved item "${name}"? This cannot be undone.`,
      )
    ) {
      return;
    }
    try {
      await api.deleteSaved(id);
      setItems((cur) => (cur ?? []).filter((i) => i.id !== id));
      if (openItem?.id === id) setOpenItem(null);
    } catch {
      setError("Could not delete that saved item.");
    }
  }

  return (
    <main className="main-area">
      <div className="main-content">
        <div className="panel-main">
          <h1 className="page-title">My Saved Work</h1>
          <p className="page-intro">
            Everything you have chosen to save, newest first. Open an
            item to view it, or delete the ones you no longer need.
          </p>

          {error && <p className="auth-error">{error}</p>}

          {items === null && !error && (
            <p className="field-hint">Loading your saved work…</p>
          )}

          {items !== null && items.length === 0 && (
            <EmptyState
              message={
                "You have not saved anything yet. Use the Save buttons " +
                "on the Index Builder and Herd Simulation to keep work " +
                "here."
              }
            />
          )}

          {items !== null && items.length > 0 && (
            <Card>
              <table className="rank-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Saved</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {items.map((it) => (
                    <tr key={it.id}>
                      <td>
                        <strong>{it.name}</strong>
                      </td>
                      <td>{KIND_LABEL[it.kind] ?? it.kind}</td>
                      <td>
                        {new Date(
                          it.created_at,
                        ).toLocaleDateString()}
                      </td>
                      <td>
                        <div className="saved-row-actions">
                          <button
                            type="button"
                            className="goal-estimate-link"
                            onClick={() => openSaved(it.id)}
                          >
                            Open
                          </button>
                          <button
                            type="button"
                            className="goal-estimate-link saved-delete"
                            onClick={() =>
                              deleteSaved(it.id, it.name)
                            }
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}

          {openBusy && (
            <p className="field-hint">Opening…</p>
          )}

          {openItem && (
            <Card title={`Saved: ${openItem.name}`}>
              <p className="field-hint" style={{ marginBottom: 10 }}>
                {KIND_LABEL[openItem.kind] ?? openItem.kind} &middot;
                saved{" "}
                {new Date(
                  openItem.created_at,
                ).toLocaleString()}
              </p>
              <SavedItemView
                item={openItem}
                onUseGoal={onUseGoal}
              />
              <div style={{ marginTop: 12 }}>
                <Button
                  variant="secondary"
                  onClick={() => setOpenItem(null)}
                >
                  Close
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </main>
  );
}

/* --------------------------------------------------------------------- *
 * Renders the content of one opened saved item, by kind.
 * ------------------------------------------------------------------- */
function SavedItemView({
  item,
  onUseGoal,
}: {
  item: SavedItem;
  onUseGoal: (components: GoalComponent[], name: string) => void;
}) {
  const p = item.payload;

  if (item.kind === "breeding_goal") {
    const components = (p.components as GoalComponent[]) ?? [];
    return (
      <>
        <table className="rank-table">
          <thead>
            <tr>
              <th>Trait</th>
              <th>Economic weight</th>
            </tr>
          </thead>
          <tbody>
            {components.map((c) => (
              <tr key={c.trait_code}>
                <td>{c.trait_code}</td>
                <td className="tnum">
                  {c.economic_weight}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: 12 }}>
          <Button
            variant="primary"
            onClick={() =>
              onUseGoal(
                components,
                (p.goalName as string) ?? item.name,
              )
            }
          >
            Use this goal in the Index Builder &rarr;
          </Button>
        </div>
      </>
    );
  }

  if (item.kind === "index_result") {
    const result = p.result as
      | { scores?: { rank: number; animal_id: string;
          index_value: number }[] }
      | undefined;
    const scores = result?.scores ?? [];
    return (
      <table className="rank-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Animal</th>
            <th>Index value</th>
          </tr>
        </thead>
        <tbody>
          {scores.map((s) => (
            <tr key={s.animal_id}>
              <td>{s.rank}</td>
              <td>{s.animal_id}</td>
              <td className="tnum">
                {s.index_value.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  if (item.kind === "simulation_result") {
    const result = p.result as
      | { mevs?: { trait_code: string; mev: number;
          units: string }[] }
      | undefined;
    const mevs = result?.mevs ?? [];
    return (
      <table className="rank-table">
        <thead>
          <tr>
            <th>Trait</th>
            <th>Economic value</th>
          </tr>
        </thead>
        <tbody>
          {mevs.map((m) => (
            <tr key={m.trait_code}>
              <td>{m.trait_code}</td>
              <td className="tnum">
                {m.mev >= 0 ? "+" : ""}
                {m.mev.toFixed(2)} /{m.units}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  return <p className="field-hint">Nothing to display.</p>;
}
