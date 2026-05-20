/*
 * Troubleshooting page.
 *
 * The dedicated help-when-stuck destination (Phase 3.5 Part 5). Organised
 * by what the user was doing, with each entry following the symptom /
 * meaning / fix structure. Content tone never blames the user and always
 * ends with a way forward.
 */

import { useState } from "react";
import { Card } from "../components/UI";
import { ContextPanel } from "../components/Help";

interface TroubleEntry {
  section: string;
  symptom: string;
  meaning: string;
  fix: string;
}

const ENTRIES: TroubleEntry[] = [
  {
    section: "Importing animals & files",
    symptom: "NexGenIQ could not match some of my file's columns",
    meaning:
      "The column-mapping step did not recognise a header automatically. " +
      "This is normal — catalogue files use all sorts of header names.",
    fix:
      "On the column-mapping screen, open the dropdown next to each " +
      "unmatched column and pick the NexGenIQ field it holds. Columns you " +
      "leave unmapped are simply ignored.",
  },
  {
    section: "Importing animals & files",
    symptom: "NexGenIQ excluded some of my animals from the ranking",
    meaning:
      "Those animals were missing an EPD for one of your index traits, " +
      "so they could not be scored on the same basis as the others.",
    fix:
      "Either add the missing EPDs to your file, remove that trait from " +
      "the goal, or switch the missing-data setting to fill gaps with the " +
      "breed average (the result for those animals is then marked " +
      "approximate).",
  },
  {
    section: "Building an index",
    symptom: "The correlations I entered were rejected as inconsistent",
    meaning:
      "The genetic correlations are not mathematically possible all at " +
      "once — no real population could have every one of them. This " +
      "almost always means a typo in one value.",
    fix:
      "Review the correlation values, especially any that look extreme. " +
      "If you are unsure, switch to the built-in research library, which " +
      "is always consistent.",
  },
  {
    section: "Building an index",
    symptom: "My animals come from different breeds and won't compare",
    meaning:
      "EPDs from different breed associations are on different scales, " +
      "so they cannot be compared directly.",
    fix:
      "Choose an across-breed adjustment table — NexGenIQ will place " +
      "every animal's EPDs on a common base before ranking. If your data " +
      "already comes from a single multi-breed evaluation, mark it as " +
      "such instead.",
  },
  {
    section: "Reading your results",
    symptom: "An animal's index value shows a wide confidence range",
    meaning:
      "The EPDs behind that animal have low accuracy, so its true merit " +
      "is less certain. Young animals without progeny records are the " +
      "usual reason.",
    fix:
      "Treat close rankings between low-accuracy animals with caution. " +
      "If your candidates vary a lot in accuracy, the accuracy-adjusted " +
      "index mode handles this more carefully.",
  },
  {
    section: "Reading your results",
    symptom: "A row in my ranking is flagged",
    meaning:
      "A flag means the result for that animal needs context — usually " +
      "that some of its EPDs were missing and filled with a breed " +
      "average, making its position approximate.",
    fix:
      "Open the Checks panel below the ranking for the plain-language " +
      "detail on every flag, or click the animal's row to see exactly " +
      "what is approximate.",
  },
];

export function Troubleshooting() {
  const [query, setQuery] = useState("");

  const filtered = ENTRIES.filter((e) => {
    const q = query.toLowerCase();
    return (
      !q ||
      e.symptom.toLowerCase().includes(q) ||
      e.meaning.toLowerCase().includes(q) ||
      e.section.toLowerCase().includes(q)
    );
  });

  /* Group entries by section for the browse-by-where-you-are layout. */
  const sections = [...new Set(filtered.map((e) => e.section))];

  return (
    <main className="main-area">
      <div className="main-content with-panel">
        <div className="panel-main">
          <h1 className="page-title">Troubleshooting</h1>
          <p className="page-intro">
            Find the thing you were doing, or search in plain language.
            Every entry ends with a way forward.
          </p>

          <Card>
            <input
              type="text"
              placeholder="Search — e.g. 'my file won't upload'"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </Card>

          {sections.length === 0 && (
            <Card>
              <p className="trouble-body">
                Nothing matched that search. Try fewer words, or browse the
                sections by clearing the search box.
              </p>
            </Card>
          )}

          {sections.map((section) => (
            <Card key={section} title={section}>
              {filtered
                .filter((e) => e.section === section)
                .map((e) => (
                  <div key={e.symptom} className="trouble-entry">
                    <p className="trouble-symptom">{e.symptom}</p>
                    <p className="trouble-body">
                      <strong>What it means.</strong> {e.meaning}
                    </p>
                    <p className="trouble-body">
                      <strong>What to do.</strong> {e.fix}
                    </p>
                  </div>
                ))}
            </Card>
          ))}

          <Card title="Still stuck?">
            <p className="trouble-body">
              NexGenIQ is open-source research software. If nothing here
              solves it, the project's community forum and issue tracker
              are the place to ask — and bug reports genuinely help the
              tool improve.
            </p>
          </Card>
        </div>

        <ContextPanel />
      </div>
    </main>
  );
}
