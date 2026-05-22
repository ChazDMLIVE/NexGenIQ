/*
 * Help content for the NexGenIQ explanation system.
 *
 * Implements the three-layer help model of Phase 3.5 Part 3: every control
 * has a short tooltip and a structured context-panel entry (what it is /
 * why it matters / how to choose). Keeping this content as data — separate
 * from the components — means it can be reviewed and extended as a unit.
 */

export interface HelpEntry {
  /** Short title shown in tooltips and the context panel header. */
  title: string;
  /** One- or two-sentence tooltip — the quick answer. */
  tooltip: string;
  /** Context-panel: a plain-language definition. */
  what: string;
  /** Context-panel: what this input changes about the result. */
  why: string;
  /** Context-panel: concrete guidance on how to choose or read it. */
  how: string;
}

/* Keyed by a stable help id used in the markup via the InfoTip component. */
export const HELP: Record<string, HelpEntry> = {
  goal: {
    title: "Your breeding goal",
    tooltip:
      "The traits you want to improve and what each is worth. This is " +
      "what 'a good animal' means for your operation.",
    what:
      "The set of traits you want to improve, each paired with an " +
      "economic weight. Together they define the breeding goal the index " +
      "ranks animals against.",
    why:
      "Everything downstream flows from this. Two herds with identical " +
      "animals but different goals should — and will — rank them " +
      "differently.",
    how:
      "Start from a template if you are unsure; it pre-fills sensible " +
      "traits and weights. Edit weights only when you have a reason to.",
  },
  basis: {
    title: "Economic basis",
    tooltip:
      "The common yardstick all your economic weights are measured " +
      "against — for example, profit per cow you breed.",
    what:
      "The shared denominator for every economic weight in the goal — " +
      "per cow exposed, per calf, or per unit.",
    why:
      "Every weight must share one basis, or the index is distorted. " +
      "NexGenIQ keeps them consistent for you.",
    how:
      "'Per cow exposed' suits most cow-calf operations. Leave it unless " +
      "you have a specific reason to change it.",
  },
  economic_weight: {
    title: "Economic weight",
    tooltip:
      "How much profit changes when this trait improves by one unit. " +
      "A bigger number means the trait matters more.",
    what:
      "The change in profit per one-unit genetic improvement in this " +
      "trait, holding the other traits steady.",
    why:
      "A bigger weight pulls the index harder toward that trait. It is " +
      "how your operation's priorities enter the ranking. Weights can be " +
      "negative — for a trait where less is better.",
    how:
      "If unsure, keep the cited default. Adjust only when you know a " +
      "trait is worth more or less in your market.",
  },
  parameters: {
    title: "Genetic parameters",
    tooltip:
      "Numbers describing how heritable each trait is and how the " +
      "traits move together genetically.",
    what:
      "Heritabilities and genetic correlations for your traits. The " +
      "index needs them so it does not double-count traits that are " +
      "genetically linked.",
    why:
      "They shape how the index combines traits. Growth traits, for " +
      "example, move together — the parameters stop that being counted " +
      "twice.",
    how:
      "Use the built-in research library unless you have your own " +
      "estimates from a geneticist. Every value is cited.",
  },
  index_mode: {
    title: "Index mode",
    tooltip:
      "How the index combines your traits. 'Standard' uses economic " +
      "value only; 'Accuracy-adjusted' also accounts for EPD reliability.",
    what:
      "Two ways of turning economic weights into one index. Standard " +
      "applies the weights directly to each animal's EPDs. " +
      "Accuracy-adjusted solves the full selection-index equations, " +
      "which also down-weight EPDs measured with less certainty.",
    why:
      "If all your animals have similarly reliable EPDs, the two give " +
      "almost the same ranking. If some animals are young with " +
      "low-accuracy EPDs, accuracy-adjusted protects you from " +
      "over-trusting an uncertain number.",
    how:
      "Keep Standard unless your candidate set mixes young and proven " +
      "animals — then switch to Accuracy-adjusted.",
  },
  animals: {
    title: "The animals to rank",
    tooltip:
      "The candidate bulls, semen, heifers or embryos you are choosing " +
      "between.",
    what:
      "The selection candidates. NexGenIQ scores each one against your " +
      "goal and ranks them.",
    why:
      "These are what the whole index exists to compare. Their EPDs are " +
      "the raw material the ranking is built from.",
    how:
      "Upload a spreadsheet or data export (CSV or Excel) \u2014 the column " +
      "mapper handles messy headers for you. A designed sale-catalogue " +
      "PDF cannot be read; use the seller\u2019s data export.",
  },
  index_value: {
    title: "Index value",
    tooltip:
      "A single number summarising an animal's overall merit for your " +
      "goal. Higher is better; compare animals by the difference.",
    what:
      "The economically weighted sum of an animal's EPDs — one number " +
      "capturing its total merit against your breeding goal.",
    why:
      "It is the whole point of an index: it lets you rank many traits " +
      "at once instead of juggling them by hand.",
    how:
      "Only differences between animals matter, not the absolute number. " +
      "The shaded range is the 95% confidence interval.",
  },
  confidence_interval: {
    title: "Confidence interval",
    tooltip:
      "The range the true value is likely to fall in. A wider range " +
      "means the EPDs behind it are less certain.",
    what:
      "A 95% confidence interval around the index value, derived from " +
      "the accuracy of the underlying EPDs.",
    why:
      "It tells you when two animals are too close to call. If their " +
      "intervals overlap heavily, the ranking between them is not solid.",
    how:
      "Prefer animals whose advantage holds up across the interval, not " +
      "just on the point estimate.",
  },
  contributions: {
    title: "Trait contributions",
    tooltip:
      "How much each trait adds to this animal's index value — which " +
      "traits carry it, and which hold it back.",
    what:
      "A breakdown of the index value into one piece per trait, so you " +
      "can see exactly where an animal's score comes from.",
    why:
      "It turns a single opaque number into an explanation. Two animals " +
      "with the same index value can get there very differently.",
    how:
      "Read the bar left to right: the widest segments are the traits " +
      "doing the most for that animal.",
  },
};
