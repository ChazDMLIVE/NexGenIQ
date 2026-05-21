/*
 * CSV export helpers for NexGenIQ result pages.
 *
 * Builds a CSV string from rows of data and triggers a client-side
 * download - no backend round-trip. Values are quoted and escaped so a
 * field containing a comma, quote, or newline cannot break the file.
 */

/* Escape one CSV field: wrap in quotes and double any inner quotes. */
function csvField(value: string | number): string {
  const s = String(value);
  if (/[",\n\r]/.test(s)) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/**
 * Turn a header row and data rows into a CSV string.
 *
 * @param header  the column names
 * @param rows    the data rows, each an array aligned to the header
 */
export function toCsv(
  header: string[],
  rows: (string | number)[][],
): string {
  const lines = [header, ...rows].map((r) =>
    r.map(csvField).join(","),
  );
  return lines.join("\r\n");
}

/**
 * Trigger a browser download of `content` as a file named `filename`.
 * Used for the CSV exports; works without any backend.
 */
export function downloadTextFile(
  filename: string,
  content: string,
  mimeType = "text/csv;charset=utf-8",
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  /* Release the object URL once the download has been initiated. */
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

/** A timestamp suffix for export filenames, e.g. "2026-05-21". */
export function dateStamp(): string {
  return new Date().toISOString().slice(0, 10);
}
