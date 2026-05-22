/**
 * PhenotypeStep — the candidate-animals step for producers who have raw
 * performance records instead of EPDs.
 *
 * The producer uploads a phenotype CSV (Animal ID, Breed, Sex,
 * Contemporary Group, then one column per measured trait: WW, YW, BW,
 * IMF, REA, BF, DMI, RFI, DOC, PAP, LPAP). The file is parsed in the
 * browser into PhenotypeRecordIn objects; the backend converts them to
 * estimated breeding values by mass selection (within-contemporary-group
 * adjustment) before ranking.
 */

import { useState } from "react";

import { Button, Card } from "../UI";
import type { PhenotypeRecordIn } from "../../lib/api";

interface PhenotypeStepProps {
  records: PhenotypeRecordIn[];
  onRecords: (records: PhenotypeRecordIn[]) => void;
  onRunExample: (records: PhenotypeRecordIn[]) => void;
}

/* The producer-facing phenotype trait columns the CSV may carry. Any
 * other column is treated as metadata and ignored. */
const PHENOTYPE_TRAIT_COLUMNS = [
  "WW", "YW", "BW", "ADG", "IMF", "REA", "BF", "DMI", "RFI", "DOC", "PAP",
  "LPAP",
];

/* Parse a phenotype CSV into records. Column matching is
 * case-insensitive. Blank phenotype cells are skipped so a producer need
 * not measure every trait on every animal. */
function parsePhenotypeCsv(text: string): {
  records: PhenotypeRecordIn[];
  error: string;
} {
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);
  if (lines.length < 2) {
    return { records: [], error: "The file has no data rows." };
  }
  const header = lines[0].split(",").map((h) => h.trim());
  const lower = header.map((h) => h.toLowerCase());
  const idx = (name: string) => lower.indexOf(name.toLowerCase());

  const idCol = idx("Animal ID");
  const cgCol = idx("Contemporary Group");
  if (idCol < 0) {
    return { records: [], error: "The file has no 'Animal ID' column." };
  }
  if (cgCol < 0) {
    return {
      records: [],
      error:
        "The file has no 'Contemporary Group' column. Every animal must " +
        "state the group it was managed and measured with.",
    };
  }
  const breedCol = idx("Breed");
  const sexCol = idx("Sex");
  /* Map each phenotype trait column to its position in the header. */
  const traitCols: Record<string, number> = {};
  for (const trait of PHENOTYPE_TRAIT_COLUMNS) {
    const c = idx(trait);
    if (c >= 0) traitCols[trait] = c;
  }
  if (Object.keys(traitCols).length === 0) {
    return {
      records: [],
      error:
        "The file has no recognised trait columns. Expected one or more " +
        "of: " + PHENOTYPE_TRAIT_COLUMNS.join(", ") + ".",
    };
  }

  const records: PhenotypeRecordIn[] = [];
  for (let i = 1; i < lines.length; i++) {
    const cells = lines[i].split(",").map((c) => c.trim());
    const animalId = cells[idCol] ?? "";
    if (!animalId) {
      return { records: [], error: `Row ${i + 1} has no Animal ID.` };
    }
    const cg = cells[cgCol] ?? "";
    if (!cg) {
      return {
        records: [],
        error:
          `Row ${i + 1} (${animalId}) has no Contemporary Group. Every ` +
          "animal needs one so its performance can be compared fairly.",
      };
    }
    const phenotypes: Record<string, number> = {};
    for (const [trait, c] of Object.entries(traitCols)) {
      const raw = cells[c];
      if (raw === undefined || raw === "") continue;
      const v = Number(raw);
      if (Number.isNaN(v)) {
        return {
          records: [],
          error: `Row ${i + 1} (${animalId}): ${trait} value "${raw}" is not a number.`,
        };
      }
      phenotypes[trait] = v;
    }
    records.push({
      animal_id: animalId,
      breed: breedCol >= 0 ? cells[breedCol] || "Angus" : "Angus",
      sex: sexCol >= 0 ? cells[sexCol] || "" : "",
      contemporary_group: cg,
      phenotypes,
    });
  }
  return { records, error: "" };
}

export function PhenotypeStep({
  records,
  onRecords,
  onRunExample,
}: PhenotypeStepProps) {
  const [error, setError] = useState("");

  async function handleFile(
    file: File,
    runAfter: boolean,
  ): Promise<void> {
    setError("");
    const text = await file.text();
    const parsed = parsePhenotypeCsv(text);
    if (parsed.error) {
      setError(parsed.error);
      return;
    }
    onRecords(parsed.records);
    if (runAfter) onRunExample(parsed.records);
  }

  async function onUpload(
    e: React.ChangeEvent<HTMLInputElement>,
  ): Promise<void> {
    const file = e.target.files?.[0];
    if (file) await handleFile(file, false);
    e.target.value = "";
  }

  async function onRunExampleClick(): Promise<void> {
    setError("");
    const res = await fetch("/nexgeniq_phenotype_example.csv");
    const text = await res.text();
    const parsed = parsePhenotypeCsv(text);
    if (parsed.error) {
      setError(parsed.error);
      return;
    }
    onRecords(parsed.records);
    onRunExample(parsed.records);
  }

  return (
    <>
      <Card title="How phenotype ranking works">
        <p>
          You are ranking animals on your own measured performance, not on
          EPDs. NexGenIQ adjusts each animal's record to a deviation from
          its contemporary-group average, then estimates a breeding value
          from that deviation. This is selection on own performance (mass
          selection): it ranks the animals you measured on their own
          merit. The accuracy is lower than a published EPD's, and the
          confidence intervals on the results reflect that.
        </p>
        <p>
          Your file needs an <strong>Animal ID</strong>, a{" "}
          <strong>Contemporary Group</strong> label (the group each animal
          was managed and weighed with), and one column per measured
          trait. Values should already be age-standardized (e.g. 205-day
          weaning weight).
        </p>
        <div className="phenotype-warning">
          <p className="phenotype-warning-title">
            Before you use phenotypic data — please read
          </p>
          <ul className="phenotype-warning-list">
            <li>
              <strong>This is not an EPD evaluation.</strong> It ranks the
              animals you measured on their own performance only. It uses
              no pedigree and no progeny, so it cannot predict how an
              animal&rsquo;s offspring will perform the way an EPD does.
            </li>
            <li>
              <strong>Accuracy is lower.</strong> A single own-performance
              record has an accuracy of roughly the square root of the
              trait heritability — well below a proven animal&rsquo;s EPD.
              The confidence intervals on the results will be wide, and
              that is honest, not a defect.
            </li>
            <li>
              <strong>Contemporary groups matter enormously.</strong>{" "}
              Animals are only compared within the group you assign them
              to. If animals managed differently share a group, or a group
              has only a few animals, the ranking can be misleading.
            </li>
            <li>
              <strong>It cannot separate look-alikes.</strong> Two animals
              with the same adjusted performance will rank the same, even
              if their true genetic merit differs.
            </li>
            <li>
              <strong>Use it as a screening tool.</strong> It is well
              suited to sorting your own calf crop on the data you have.
              For high-stakes decisions — buying a herd sire, marketing
              seedstock — official EPDs remain the stronger basis.
            </li>
          </ul>
        </div>
      </Card>

      <Card title="Upload your performance records">
        <p className="builder-help">
          Traits NexGenIQ reads (use the short code as your CSV column
          header): Weaning Weight (WW), Yearling Weight (YW), Birth Weight
          (BW), Average Daily Gain (ADG), Intramuscular Fat (IMF), Ribeye
          Area (REA), Backfat (BF), Dry-Matter Intake (DMI), Residual Feed
          Intake (RFI), Docility (DOC), Pulmonary Arterial Pressure (PAP),
          and Latent PAP (LPAP).
          You only need the ones you measured.
        </p>
        <div className="builder-downloads">
          <a
            className="builder-download-link"
            href="/nexgeniq_phenotype_template.csv"
            download
          >
            Download the phenotype column template (CSV)
          </a>
          <a
            className="builder-download-link"
            href="/nexgeniq_phenotype_example.csv"
            download
          >
            Download the example data (20 animals, CSV)
          </a>
        </div>

        <div className="builder-upload-row">
          <label className="file-upload-button">
            <span>Upload phenotype CSV</span>
            <input
              type="file"
              accept=".csv,text/csv"
              onChange={onUpload}
              className="file-upload-input"
            />
          </label>
          <Button variant="secondary" onClick={onRunExampleClick}>
            Run the example
          </Button>
        </div>

        {error && <p className="form-error">{error}</p>}

        {records.length > 0 && (
          <p className="builder-upload-summary">
            Loaded <strong>{records.length}</strong> animals across{" "}
            <strong>
              {new Set(records.map((r) => r.contemporary_group)).size}
            </strong>{" "}
            contemporary group(s).
          </p>
        )}
      </Card>
    </>
  );
}
