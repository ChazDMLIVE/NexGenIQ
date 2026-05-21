/*
 * How to Use page.
 *
 * A thorough, zero-knowledge walkthrough of NexGenIQ. It assumes the
 * reader knows nothing about cattle genetics or selection indexes, and
 * explains every term, every screen, every input box and button, and what
 * the tool is doing behind each step. It follows the two real workflows -
 * the Herd Simulation and the Index Builder - screen by screen, and ends
 * each with a worked example the reader can follow along with.
 *
 * Content is layered: each step is an expandable section so the page is a
 * calm table of contents until the reader opens what they need.
 */

import { useState } from "react";
import { Card } from "../components/UI";
import { ContextPanel } from "../components/Help";

/* One walkthrough step: a title, and a body shown when expanded. */
interface Step {
  id: string;
  title: string;
  body: JSX.Element;
}

/* One glossary term. */
interface Term {
  term: string;
  definition: string;
}

const GLOSSARY: Term[] = [
  {
    term: "EPD (Expected Progeny Difference)",
    definition:
      "A prediction of how an animal's future calves will perform for a " +
      "trait, compared with the calves of an average animal. A bull with " +
      "a weaning-weight EPD of +40 lb is expected to sire calves about " +
      "40 lb heavier at weaning than a bull with an EPD of 0. EPDs are " +
      "what breed associations publish; they are the raw material this " +
      "tool works with.",
  },
  {
    term: "Trait",
    definition:
      "A measurable characteristic of an animal — weaning weight, " +
      "calving ease, marbling, and so on. Each trait has its own EPD.",
  },
  {
    term: "Accuracy",
    definition:
      "A number from 0 to 1 that says how much to trust an EPD. A young " +
      "bull with no calves on the ground has a low-accuracy EPD (it may " +
      "change a lot); a proven sire with hundreds of calves has a " +
      "high-accuracy EPD. NexGenIQ uses accuracy to put a confidence " +
      "range on every result.",
  },
  {
    term: "Economic value (economic weight)",
    definition:
      "How many dollars a one-unit genetic improvement in a trait is " +
      "worth to your operation. Weaning weight might be worth about " +
      "$1.80 per pound; mature cow weight is usually negative (a bigger " +
      "cow costs more to keep). Economic values are what turn a list of " +
      "traits into a single ranking.",
  },
  {
    term: "Selection index",
    definition:
      "A single number that combines all of an animal's EPDs, each " +
      "weighted by its economic value. It estimates the animal's overall " +
      "breeding merit for your operation in dollar terms. A higher index " +
      "value means a more valuable animal for your goal.",
  },
  {
    term: "Breeding goal",
    definition:
      "Your list of which traits matter and what each is worth. The " +
      "Index Builder turns your breeding goal into a selection index.",
  },
  {
    term: "MEV (Marginal Economic Value)",
    definition:
      "The economic value of a trait as worked out by the Herd " +
      "Simulation — the change in herd profit, per cow per year, from a " +
      "one-unit genetic improvement in that trait. The simulation's MEVs " +
      "can be carried straight into the Index Builder as a breeding goal.",
  },
  {
    term: "Heritability",
    definition:
      "How strongly a trait is passed from parent to calf, from 0 to 1. " +
      "A high-heritability trait (like yearling weight) responds quickly " +
      "to selection; a low-heritability trait (like stayability) " +
      "responds slowly. The tool uses heritability internally; you do " +
      "not have to enter it.",
  },
  {
    term: "PAP (Pulmonary Arterial Pressure)",
    definition:
      "A measure of susceptibility to high-altitude (brisket) disease — " +
      "lower is better. It is only economically important for herds " +
      "grazing at elevation. An official PAP EPD is published only by " +
      "the American Angus and American Simmental associations.",
  },
  {
    term: "Across-breed adjustment",
    definition:
      "EPDs from different breed associations sit on different scales " +
      "and cannot be compared directly. Across-breed adjustment places " +
      "them on a common base so animals of different breeds can be " +
      "ranked together.",
  },
];

/* ----------------------------------------------------------------------
 * The Herd Simulation walkthrough.
 * -------------------------------------------------------------------- */
const SIMULATION_STEPS: Step[] = [
  {
    id: "sim-what",
    title: "What the Herd Simulation does, and when to use it",
    body: (
      <>
        <p className="docs-body">
          The Herd Simulation answers one question:{" "}
          <em>what is each trait actually worth to my operation?</em> It
          builds a virtual herd that matches the operation you describe,
          runs it forward year by year, and measures how herd profit
          changes when each trait is improved. The result is a set of
          economic values — one per trait — tailored to your herd.
        </p>
        <p className="docs-body">
          Use the Herd Simulation when you want economic values you can
          trust for your own operation, rather than guessing them. Once it
          finishes, you can carry its economic values straight into the
          Index Builder. If you already know what your traits are worth,
          you can skip the simulation and go straight to the Index
          Builder.
        </p>
      </>
    ),
  },
  {
    id: "sim-step1",
    title: "Step 1 — Your herd",
    body: (
      <>
        <p className="docs-body">
          This screen describes your operation. Every box has a sensible
          default, so if you are unsure of a number you can leave it.
        </p>
        <ul className="howto-list">
          <li>
            <strong>Name this operation</strong> — a label for your own
            reference. It has no effect on the result.
          </li>
          <li>
            <strong>Number of breeding cows</strong> — how many cows are
            in your herd. The simulation builds a herd this size.
          </li>
          <li>
            <strong>Conception rate</strong> — the fraction of cows that
            become pregnant each breeding season. 0.92 means 92%.
          </li>
          <li>
            <strong>Calving loss rate</strong> — the fraction of
            pregnancies lost before the calf is weaned.
          </li>
          <li>
            <strong>Replacement rate</strong> — the fraction of cows
            replaced each year.
          </li>
          <li>
            <strong>Do you keep your own replacement heifers?</strong> —
            “Yes” means you raise your own replacements (a self-replacing
            herd, which values fertility and longevity more); “No” means a
            terminal operation that sells every calf.
          </li>
        </ul>
        <p className="docs-body">
          <strong>Breed composition.</strong> Below the herd numbers you
          describe the breed makeup of your cow herd and of the bulls you
          mate them to. Most herds are one breed — leave it as a single
          group at 100% of one breed. For a crossbred herd, use “Add a
          breed to this group” to make a cross, or “Add another group” for
          a herd with more than one kind of animal. The shares must add to
          100%. NexGenIQ then shows the <strong>resulting calf crop</strong>{" "}
          automatically — you never enter it, because it is just half the
          cow side and half the bull side. Breed makeup matters because
          breeds differ genetically, crossbred calves get a heterosis
          (hybrid vigour) boost, and some EPDs only exist for some breeds.
        </p>
        <p className="docs-body">
          When everything adds up correctly, the{" "}
          <strong>Continue</strong> button turns on.
        </p>
      </>
    ),
  },
  {
    id: "sim-step2",
    title: "Step 2 — Economics",
    body: (
      <>
        <p className="docs-body">
          This screen describes your prices and costs — the numbers that
          decide what each trait is worth.
        </p>
        <ul className="howto-list">
          <li>
            <strong>When do you sell your calves?</strong> — your
            marketing endpoint. “At weaning” values weaning weight; later
            endpoints (backgrounding, finished off the feedlot, or on the
            rail as a carcass) make growth, feed efficiency, and carcass
            traits economically real. Choosing a later endpoint reveals
            extra inputs further down.
          </li>
          <li>
            <strong>Price bands</strong> — your sale price per
            hundredweight (100 lb) by weight range, for steers, heifers,
            and cull cows. Lighter calves usually bring more per cwt, so
            you can enter several weight bands. The simulation prices each
            calf from the band its weight and sex fall into.
          </li>
          <li>
            <strong>Pasture cost ($/AUM)</strong> — the monthly cost of
            carrying one 1,000 lb cow on pasture. This is what makes a
            bigger cow cost more.
          </li>
          <li>
            <strong>Fixed cost per cow ($/year)</strong> — annual non-feed
            cost per cow: labour, health, overhead.
          </li>
          <li>
            <strong>Ranch elevation</strong> — feet above sea level. This
            is what gives the PAP trait economic weight: below about
            5,000 ft, high-altitude disease is not a real cost; above it,
            PAP starts to matter.
          </li>
          <li>
            <strong>Replacement and herd costs</strong> — what it costs to
            develop or buy a replacement female, and the loss when a
            productive cow dies. These decide what fertility and longevity
            are worth.
          </li>
          <li>
            <strong>Feedlot and carcass</strong> — only shown if you sell
            past weaning: days backgrounded, days on feed, and the carcass
            base price.
          </li>
          <li>
            <strong>Simulation precision</strong> — choose Quick,
            Standard, or High precision. The tool works out trait values
            by running many independent virtual herds and averaging them;
            more herds give a more precise value (especially for the
            noisier traits like PAP and stayability) but take longer. Each
            option shows an approximate run time. If your herd grazes at
            altitude with a PAP-evaluated breed, the tool will suggest
            High precision.
          </li>
        </ul>
        <p className="docs-body">
          Press <strong>Run the simulation</strong>. The tool builds the
          virtual herds, runs each forward, and works out the economic
          values. Depending on the precision you chose this takes roughly
          30 seconds to a few minutes — a note on screen tells you the
          estimate, and you can leave the screen open while it runs.
        </p>
      </>
    ),
  },
  {
    id: "sim-step3",
    title: "Step 3 — Results",
    body: (
      <>
        <p className="docs-body">
          The results screen opens with a{" "}
          <strong>plain-language interpretation</strong> — a headline and
          short readout telling you what the analysis found and what it
          means. Open “Explain this in more detail” for the fuller
          reasoning. A standing note reminds you this is information, not a
          recommendation to take any particular action.
        </p>
        <p className="docs-body">
          Below that, the <strong>Derived economic values</strong> table
          lists every trait with its economic value (in dollars per unit),
          a “±” figure showing the uncertainty of the estimate, and a
          precision label. A value marked <em>imprecise</em> means the
          estimate is noisy — you could re-run for a tighter number, but it
          is usually still usable.
        </p>
        <p className="docs-body">
          The key button is <strong>Use these in the Index Builder</strong>
          . It carries every economic value straight across as a breeding
          goal, so you do not have to retype anything.
        </p>
      </>
    ),
  },
  {
    id: "sim-example",
    title: "Worked example — a 200-cow Angus herd selling at weaning",
    body: (
      <>
        <p className="docs-body">
          Suppose you run 200 straight-Angus cows, keep your own
          replacement heifers, and sell your calves at weaning.
        </p>
        <ul className="howto-list">
          <li>
            <strong>Step 1:</strong> Set the number of breeding cows to
            200, leave conception, calving loss and replacement at their
            defaults, and answer “Yes” to keeping your own heifers. Under
            breed composition, leave the cow herd and the bull battery
            each as one group, 100% Angus. The calf crop shows as 100%
            Angus.
          </li>
          <li>
            <strong>Step 2:</strong> Choose “At weaning”. Enter your steer
            and heifer prices by weight band. Set your pasture cost, fixed
            cost, and your ranch elevation (say 4,000 ft — low enough that
            PAP will carry little weight). Press “Run the simulation”.
          </li>
          <li>
            <strong>Step 3:</strong> You see economic values for every
            trait. Weaning weight comes out positive (heavier calves are
            worth more); mature cow weight comes out negative (a bigger
            cow costs more to keep); calving ease and stayability are
            positive. Press “Use these in the Index Builder”.
          </li>
        </ul>
        <p className="docs-body">
          You now have a breeding goal built from your own operation, and
          the tool moves you to the Index Builder.
        </p>
      </>
    ),
  },
];

/* ----------------------------------------------------------------------
 * The Index Builder walkthrough.
 * -------------------------------------------------------------------- */
const INDEX_STEPS: Step[] = [
  {
    id: "idx-what",
    title: "What the Index Builder does, and when to use it",
    body: (
      <>
        <p className="docs-body">
          The Index Builder ranks a set of animals on a single number —
          the selection index — so you can see which animals best fit your
          breeding goal. You give it (1) your breeding goal — which traits
          matter and what each is worth — and (2) the animals to compare,
          with their EPDs. It returns a ranked list with a plain-language
          explanation of why each animal sits where it does.
        </p>
        <p className="docs-body">
          Use the Index Builder whenever you have a group of animals to
          choose between — a sale catalogue, your own bulls, a set of
          replacement heifers.
        </p>
      </>
    ),
  },
  {
    id: "idx-step1",
    title: "Step 1 — Goal",
    body: (
      <>
        <p className="docs-body">
          Here you tell the tool what you are breeding for. The fastest
          start is one of the <strong>templates</strong> at the top —
          “Self-replacing herd”, “Terminal — sell all calves”, “Retained
          ownership / feedlot”, or “High-altitude / brisket disease”. Each
          fills the goal with a sensible set of traits and economic values
          you can then adjust. (If you came from the Herd Simulation, your
          goal is already filled in with your derived economic values.)
        </p>
        <p className="docs-body">
          The <strong>economic-weight grid</strong> is the heart of this
          screen — one row per trait, each with an economic value you can
          type or set with the slider. A positive value means “more of
          this trait is better”; a negative value means “less is better”
          (mature cow weight, for example).
        </p>
        <p className="docs-body">
          Not sure what a trait is worth? Every row has a{" "}
          <strong>“Help me price this”</strong> link. It opens a short
          guided estimator that asks plain questions about your operation
          (your sale price, the cost of a difficult calving, and so on)
          and computes a starting economic value, showing you the formula
          it used. Use “Add another trait” to bring in more traits;
          breed-restricted traits like PAP are labelled so you know which
          breeds publish them.
        </p>
      </>
    ),
  },
  {
    id: "idx-step2",
    title: "Step 2 — Parameters",
    body: (
      <>
        <p className="docs-body">
          This screen sets the genetic background the index needs — how
          the traits relate to each other genetically. Almost everyone
          should leave the built-in research library selected; it is a set
          of published, cited values and needs no input from you.
        </p>
        <p className="docs-body">
          The one choice here is the <strong>index mode</strong>:
        </p>
        <ul className="howto-list">
          <li>
            <strong>Standard</strong> — weights each EPD purely by its
            economic value. The right choice for most users.
          </li>
          <li>
            <strong>Accuracy-adjusted</strong> — also accounts for how
            reliable each EPD is, favouring proven animals over unproven
            ones. Choose this only if your animals vary a lot in EPD
            accuracy.
          </li>
        </ul>
      </>
    ),
  },
  {
    id: "idx-step3",
    title: "Step 3 — Animals",
    body: (
      <>
        <p className="docs-body">
          Here you provide the animals to rank. First, record the{" "}
          <strong>EPD source evaluation</strong> — which breed
          association or evaluation your animals' EPDs came from. This
          matters because EPDs from different evaluations are not directly
          comparable; recording the source keeps your ranking traceable.
        </p>
        <p className="docs-body">
          There are two ways to enter animals:
        </p>
        <ul className="howto-list">
          <li>
            <strong>Upload a file</strong> — choose a CSV (a sale
            catalogue export works well). NexGenIQ reads it and shows you
            how it matched each column; you confirm or correct the
            matching, then import. Any column it could not match you can
            set by hand, or leave to be ignored.
          </li>
          <li>
            <strong>Enter by hand</strong> — for comparing just a few
            animals, type each one's ID, breed, and EPDs directly.
          </li>
        </ul>
        <p className="docs-body">
          When at least one animal is loaded, press{" "}
          <strong>Build my index</strong>.
        </p>
      </>
    ),
  },
  {
    id: "idx-step4",
    title: "Step 4 — Results",
    body: (
      <>
        <p className="docs-body">
          The results screen leads with a{" "}
          <strong>plain-language interpretation</strong>: a headline
          naming your top animal, a readout of what the ranking means and
          how the field compares, and a standing note that this is
          information, not a recommendation to keep or cull any animal.
        </p>
        <p className="docs-body">
          The <strong>ranked table</strong> lists every animal best-first,
          with its index value and a confidence range. Click any animal's
          row to see, in plain language, exactly why it ranks where it
          does — which traits carry it and which hold it back. Animals
          close together in index value are close in merit; the ranking
          is guidance, not a hard cutoff.
        </p>
        <p className="docs-body">
          A <strong>flag</strong> on a row means that result needs context
          — usually that some EPDs were missing and filled with a breed
          average, making the position approximate. The{" "}
          <strong>Checks</strong> panel explains every flag and warning in
          plain language. The <strong>Sensitivity</strong> tab shows how
          much the ranking would change if your economic values were a
          little different — a way to see how solid your ranking is.
        </p>
      </>
    ),
  },
  {
    id: "idx-example",
    title: "Worked example — ranking five bulls in a sale catalogue",
    body: (
      <>
        <p className="docs-body">
          Suppose you have a sale catalogue with five Angus bulls and you
          want the best one for a self-replacing commercial herd.
        </p>
        <ul className="howto-list">
          <li>
            <strong>Step 1:</strong> Click the “Self-replacing herd”
            template. It fills the goal with weaning weight, calving ease,
            stayability and milk, each with a starting economic value. If
            one looks off for your operation, adjust it — or use “Help me
            price this”.
          </li>
          <li>
            <strong>Step 2:</strong> Leave the built-in research library
            selected and the index mode on “Standard”. Continue.
          </li>
          <li>
            <strong>Step 3:</strong> Set the EPD source to your bulls'
            association (for example, the American Angus Association).
            Upload the catalogue CSV, confirm the column matching, and
            import. Press “Build my index”.
          </li>
          <li>
            <strong>Step 4:</strong> The five bulls come back ranked. The
            interpretation names the top bull and explains the ranking.
            Click a row to see which traits carried each bull. If the top
            two are nearly tied in index value, that is telling you they
            are close in merit — weigh other factors freely.
          </li>
        </ul>
      </>
    ),
  },
];

export function HowToUse() {
  /* Which steps are expanded. */
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [glossaryOpen, setGlossaryOpen] = useState(false);

  function toggle(id: string) {
    setOpen((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function renderSteps(steps: Step[]) {
    return steps.map((s) => (
      <Card key={s.id} title={s.title}>
        <button
          type="button"
          className="docs-toggle"
          onClick={() => toggle(s.id)}
          aria-expanded={!!open[s.id]}
        >
          {open[s.id] ? "Hide this step" : "Show this step"}
        </button>
        {open[s.id] && <div className="docs-detail">{s.body}</div>}
      </Card>
    ));
  }

  return (
    <main className="main-area">
      <div className="main-content with-panel">
        <div className="panel-main">
          <h1 className="page-title">How to Use NexGenIQ</h1>
          <p className="page-intro">
            A complete, step-by-step guide. It assumes you are starting
            from scratch — every term is explained, every screen and
            button is covered. Open the section you need; nothing here is
            required reading in order.
          </p>

          {/* --- the two workflows, in one sentence --- */}
          <Card title="The two things NexGenIQ does">
            <p className="docs-body">
              NexGenIQ has two tools that work together. The{" "}
              <strong>Herd Simulation</strong> works out what each trait
              is economically worth to your operation. The{" "}
              <strong>Index Builder</strong> uses those values (or values
              you supply yourself) to rank a group of animals from best to
              worst for your goal. A typical user runs the simulation
              once, then carries its results into the Index Builder. If
              you already know your economic values, you can start at the
              Index Builder.
            </p>
          </Card>

          {/* --- glossary --- */}
          <Card title="Plain-language glossary — every term explained">
            <p className="docs-body">
              If a word in this guide is unfamiliar, it is defined here.
            </p>
            <button
              type="button"
              className="docs-toggle"
              onClick={() => setGlossaryOpen((v) => !v)}
              aria-expanded={glossaryOpen}
            >
              {glossaryOpen
                ? "Hide the glossary"
                : "Show the glossary"}
            </button>
            {glossaryOpen && (
              <dl className="howto-glossary">
                {GLOSSARY.map((t) => (
                  <div key={t.term} className="howto-term">
                    <dt>{t.term}</dt>
                    <dd>{t.definition}</dd>
                  </div>
                ))}
              </dl>
            )}
          </Card>

          {/* --- workflow 1 --- */}
          <h2 className="howto-section-title">
            Workflow 1 — The Herd Simulation
          </h2>
          <p className="page-intro">
            Work out what each trait is worth to your operation.
          </p>
          {renderSteps(SIMULATION_STEPS)}

          {/* --- workflow 2 --- */}
          <h2 className="howto-section-title">
            Workflow 2 — The Index Builder
          </h2>
          <p className="page-intro">
            Rank a group of animals for your breeding goal.
          </p>
          {renderSteps(INDEX_STEPS)}

          {/* --- where to go next --- */}
          <Card title="If you get stuck">
            <p className="docs-body">
              Every screen has small “i” information tips next to inputs —
              hover or tap them for a quick explanation in place. The{" "}
              <strong>Help</strong> page lists common problems and what to
              do about them. The{" "}
              <strong>Technical Docs</strong> page explains the
              mathematics and methods for anyone who wants the full
              detail.
            </p>
          </Card>
        </div>

        <ContextPanel />
      </div>
    </main>
  );
}
