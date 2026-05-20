/*
 * Step 3 of the Index Builder — add the animals to rank.
 *
 * Two ways in: upload a CSV (the guided inspect -> confirm-mapping ->
 * parse flow of Phase 3.5 Section 4.3) or add a few animals by hand.
 */

import { useState } from "react";
import { api, type Animal, type Trait } from "../../lib/api";
import { Button, Card, EmptyState, Field } from "../UI";

interface AnimalsStepProps {
  traits: Trait[];
  animals: Animal[];
  onAnimals: (a: Animal[]) => void;
}

interface InspectState {
  file: File;
  filename: string;
  rowCount: number;
  columns: {
    source_column: string;
    target_field: string;
    confidence: string;
  }[];
}

export function AnimalsStep({
  traits,
  animals,
  onAnimals,
}: AnimalsStepProps) {
  const [tab, setTab] = useState<"upload" | "manual">("upload");
  const [inspect, setInspect] = useState<InspectState | null>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [problems, setProblems] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  /* The set of fields a CSV column can map to. */
  const targetOptions = [
    { value: "", label: "(ignore this column)" },
    { value: "animal_id", label: "Animal ID" },
    { value: "breed", label: "Breed" },
    { value: "sex", label: "Sex" },
    { value: "evaluation_id", label: "Evaluation" },
    ...traits.flatMap((t) => [
      { value: t.code, label: `${t.name} — EPD` },
      { value: `${t.code}_acc`, label: `${t.name} — accuracy` },
    ]),
  ];

  async function onFile(file: File) {
    setError("");
    setBusy(true);
    try {
      const result = await api.inspectCsv(file);
      setInspect({
        file,
        filename: result.filename,
        rowCount: result.row_count,
        columns: result.columns,
      });
      /* Seed the editable mapping from the auto-detection. */
      const m: Record<string, string> = {};
      result.columns.forEach((c) => {
        m[c.source_column] = c.target_field;
      });
      setMapping(m);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not read that file.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function confirmMapping() {
    if (!inspect) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.parseCsv(inspect.file, mapping);
      onAnimals(result.animals);
      setProblems(result.problems);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not parse the file.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="tabs">
        <button
          className={`tab ${tab === "upload" ? "tab-active" : ""}`}
          onClick={() => setTab("upload")}
        >
          Upload a file
        </button>
        <button
          className={`tab ${tab === "manual" ? "tab-active" : ""}`}
          onClick={() => setTab("manual")}
        >
          Enter by hand
        </button>
      </div>

      {error && <p className="auth-error">{error}</p>}

      {/* ---- upload tab ---- */}
      {tab === "upload" && (
        <Card title="Upload a catalogue file" helpId="animals">
          {!inspect ? (
            <label className="dropzone" style={{ display: "block" }}>
              <input
                type="file"
                accept=".csv,text/csv"
                style={{ display: "none" }}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) onFile(f);
                }}
              />
              {busy
                ? "Reading your file…"
                : "Choose a CSV file — a sale catalogue export works well."}
            </label>
          ) : (
            <>
              <p className="field-hint" style={{ marginBottom: 12 }}>
                <strong>{inspect.filename}</strong> — {inspect.rowCount}{" "}
                rows. Confirm how each column maps to NexGenIQ.
              </p>
              <table className="map-table">
                <tbody>
                  {inspect.columns.map((col) => (
                    <tr key={col.source_column}>
                      <td>
                        <strong>{col.source_column}</strong>
                      </td>
                      <td>
                        <select
                          value={mapping[col.source_column] ?? ""}
                          onChange={(e) =>
                            setMapping({
                              ...mapping,
                              [col.source_column]: e.target.value,
                            })
                          }
                        >
                          {targetOptions.map((o) => (
                            <option key={o.value} value={o.value}>
                              {o.label}
                            </option>
                          ))}
                        </select>
                        {col.confidence === "detected" && (
                          <span className="map-detected">
                            ✓ auto-detected
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
                <Button
                  variant="primary"
                  busy={busy}
                  onClick={confirmMapping}
                >
                  Confirm and import
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setInspect(null);
                    setProblems([]);
                  }}
                >
                  Choose a different file
                </Button>
              </div>

              {animals.length > 0 && (
                <p className="import-summary">
                  ✓ {animals.length} animals imported and ready to rank
                  {problems.length > 0
                    ? ` · ${problems.length} row(s) needed attention`
                    : ""}
                  .
                </p>
              )}
              {problems.map((p) => (
                <p
                  key={p}
                  className="field-hint"
                  style={{ marginTop: 4 }}
                >
                  {p}
                </p>
              ))}
            </>
          )}
        </Card>
      )}

      {/* ---- manual tab ---- */}
      {tab === "manual" && (
        <ManualEntry
          traits={traits}
          animals={animals}
          onAnimals={onAnimals}
        />
      )}
    </>
  );
}

/* --------------------------------------------------------------------- *
 * Manual single-animal entry — a quick path for comparing a few animals.
 * ------------------------------------------------------------------- */
function ManualEntry({
  traits,
  animals,
  onAnimals,
}: AnimalsStepProps) {
  const [id, setId] = useState("");
  const [breed, setBreed] = useState("Angus");
  const [epdText, setEpdText] = useState("");

  function addAnimal() {
    if (!id.trim()) return;
    /* EPDs entered as "WW:72:0.85, CED:14:0.70" — trait:value:accuracy. */
    const epds = epdText
      .split(",")
      .map((part) => part.trim())
      .filter(Boolean)
      .map((part) => {
        const [code, value, acc] = part.split(":").map((s) => s.trim());
        return {
          trait_code: code,
          value: Number(value),
          bif_accuracy: acc ? Number(acc) : null,
          scale: "EPD",
        };
      })
      .filter((e) => e.trait_code && !Number.isNaN(e.value));

    onAnimals([
      ...animals,
      { animal_id: id.trim(), breed, evaluation_id: "", epds },
    ]);
    setId("");
    setEpdText("");
  }

  const traitHint = traits
    .slice(0, 4)
    .map((t) => t.code)
    .join(", ");

  return (
    <Card title="Enter animals by hand" helpId="animals">
      <Field label="Animal ID">
        <input
          type="text"
          value={id}
          onChange={(e) => setId(e.target.value)}
          placeholder="e.g. AAA-1842"
        />
      </Field>
      <Field label="Breed">
        <input
          type="text"
          value={breed}
          onChange={(e) => setBreed(e.target.value)}
        />
      </Field>
      <Field
        label="EPDs"
        hint={`Enter as trait:value:accuracy, comma-separated. ` +
          `Trait codes include ${traitHint}. ` +
          `Example: WW:72:0.85, CED:14:0.70`}
      >
        <input
          type="text"
          value={epdText}
          onChange={(e) => setEpdText(e.target.value)}
          placeholder="WW:72:0.85, CED:14:0.70, STAY:22:0.55"
        />
      </Field>
      <Button variant="secondary" onClick={addAnimal}>
        Add this animal
      </Button>

      <div style={{ marginTop: 16 }}>
        {animals.length === 0 ? (
          <EmptyState message="No animals added yet — add your first above." />
        ) : (
          <p className="import-summary">
            ✓ {animals.length} animal(s) ready:{" "}
            {animals.map((a) => a.animal_id).join(", ")}
          </p>
        )}
      </div>
    </Card>
  );
}
