/*
 * Step 3 of the Index Builder — add the animals to rank.
 *
 * Two ways in: upload a CSV (the guided inspect -> confirm-mapping ->
 * parse flow of Phase 3.5 Section 4.3) or add a few animals by hand.
 *
 * The user also records the EPD SOURCE EVALUATION - which national or
 * breed-association genetic evaluation the EPDs came from. EPDs from
 * different evaluations are on different bases and are not directly
 * comparable; recording the source makes every ranking traceable and
 * citable, and flags when animals span more than one evaluation.
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

/* Common national / breed evaluations, offered as quick picks. The user
   can also type any label - this is a free-form provenance record, not a
   fixed enumeration. */
const COMMON_EVALUATIONS = [
  "AAA (American Angus Association)",
  "RAAA (Red Angus Association of America)",
  "AHA (American Hereford Association)",
  "ASA (American Simmental Association)",
  "AICA (American-International Charolais Association)",
  "AGA (American Gelbvieh Association)",
  "NALF (North American Limousin Foundation)",
  "IBBA (International Brangus Breeders Association)",
  "ASA-Shorthorn (American Shorthorn Association)",
  "ASBA (American Salers / Salers Breeders)",
  "ABBA (American Brahman Breeders Association)",
  "AMAA (American Maine-Anjou Association)",
  "ACA (American Chianina Association)",
  "RAAA/AGA/ASA via International Genetic Solutions (IGS)",
];

/* Stamp one evaluation label onto every animal in a set. */
function withEvaluation(list: Animal[], evaluation: string): Animal[] {
  return list.map((a) => ({
    ...a,
    /* A per-row evaluation from the CSV is kept; otherwise the
       set-level label is applied. */
    evaluation_id: a.evaluation_id || evaluation,
  }));
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

  /* The EPD source evaluation - one label for the whole set. */
  const [evaluation, setEvaluation] = useState("");

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

  /* Re-stamp the current animals whenever the set-level evaluation
     label changes, so the choice always takes effect. */
  function updateEvaluation(value: string) {
    setEvaluation(value);
    if (animals.length > 0) {
      onAnimals(
        animals.map((a) => ({ ...a, evaluation_id: value })),
      );
    }
  }

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
      onAnimals(withEvaluation(result.animals, evaluation));
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
      {/* EPD source evaluation - applies to the whole set. */}
      <Card title="Where did these EPDs come from?">
        <Field
          label="EPD source evaluation"
          hint="The national or breed-association genetic evaluation your
                animals' EPDs were published in. EPDs from different
                evaluations sit on different bases and are not directly
                comparable, so recording the source keeps your ranking
                traceable. Type your own, or pick a common one."
        >
          <input
            type="text"
            list="evaluation-options"
            value={evaluation}
            onChange={(e) => updateEvaluation(e.target.value)}
            placeholder="e.g. AAA 2025 spring evaluation"
          />
          <datalist id="evaluation-options">
            {COMMON_EVALUATIONS.map((ev) => (
              <option key={ev} value={ev} />
            ))}
          </datalist>
        </Field>
        <p className="field-hint">
          If your file has its own evaluation column, that is kept
          per-animal; this field fills in any animal that does not.
        </p>
      </Card>

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
          evaluation={evaluation}
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
  evaluation,
}: AnimalsStepProps & { evaluation: string }) {
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
      {
        animal_id: id.trim(),
        breed,
        evaluation_id: evaluation,
        epds,
      },
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
