"""
Guided economic-value estimator for osit-index.

The selection-index engine needs an economic value (a dollar weight) for
every trait in the breeding goal. The herd-simulation engine (osit-sim)
derives those values rigorously, but not every user will run a full
simulation. This module gives that user a transparent, defensible
alternative: a short set of plain-language questions whose answers are
turned into a starting economic value for each trait by an explicit,
documented formula.

The estimates here are deliberately simple "first-principles" partial
budgets - the marginal dollar consequence of a one-unit genetic change,
worked out from prices and rates the producer already knows. They are a
starting point a user can adjust, not a replacement for the simulation's
joint, dynamic derivation. Every recipe states its formula and its
assumptions so the number is never a black box.

Reference: NexGenIQ Phase 1 Section 2.3 (economic values); Phase 2 gap G6
(economic-value guidance for non-simulation users).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class EstimatorQuestion:
    """One plain-language question in a trait's estimator recipe.

    Attributes
    ----------
    key:
        Stable identifier the answer is stored under.
    prompt:
        The question shown to the user.
    help_text:
        A short explanation of what the number means and where to find it.
    default:
        A sensible default value, so the recipe yields a number even
        before the user customises anything.
    units:
        Units of the answer (e.g. ``"$/lb"``, ``"$"``, ``"fraction"``).
    minimum, maximum:
        Permitted range for the answer.
    """

    key: str
    prompt: str
    help_text: str
    default: float
    units: str
    minimum: float = 0.0
    maximum: float = 1_000_000.0


@dataclass(frozen=True)
class EstimatorRecipe:
    """A complete economic-value recipe for one trait.

    Attributes
    ----------
    trait_code:
        The trait this recipe estimates a value for.
    questions:
        The plain-language questions whose answers drive the estimate.
    formula:
        A function mapping the answered values to an economic value, in
        dollars per genetic unit of the trait.
    formula_text:
        A human-readable statement of the formula, surfaced to the user
        so the estimate is transparent.
    basis_note:
        A short note on what the resulting value means and its main
        simplifying assumption.
    """

    trait_code: str
    questions: tuple[EstimatorQuestion, ...]
    formula: Callable[[dict[str, float]], float]
    formula_text: str
    basis_note: str


@dataclass
class EstimateResult:
    """The estimated economic value for one trait.

    Attributes
    ----------
    trait_code:
        The trait.
    economic_value:
        The estimated dollar value per genetic unit of the trait.
    formula_text:
        The formula used (for display).
    basis_note:
        The interpretation / assumption note.
    inputs_used:
        The answer values the estimate was computed from.
    """

    trait_code: str
    economic_value: float
    formula_text: str
    basis_note: str
    inputs_used: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Shared question definitions reused across several recipes.
# ---------------------------------------------------------------------------
_Q_FRACTION_SOLD = EstimatorQuestion(
    key="fraction_marketed",
    prompt="What fraction of each calf crop do you sell?",
    help_text="The share of calves marketed rather than kept as "
              "replacements. A terminal operation is 1.0; a herd that "
              "keeps many heifers is lower.",
    default=0.85, units="fraction", minimum=0.0, maximum=1.0,
)


# ---------------------------------------------------------------------------
# The estimator recipes, keyed by trait code.
#
# Each formula returns dollars per one genetic unit of the trait. The unit
# matches the trait's EPD unit (lb, %, score, mmHg, latent-z).
# ---------------------------------------------------------------------------
def _ww_value(a: dict[str, float]) -> float:
    # A 1 lb increase in weaning-weight EPD adds ~1 lb of saleable calf.
    # Value = price per lb * fraction of calves sold.
    return (a["price_per_lb"]) * a["fraction_marketed"]


def _yw_value(a: dict[str, float]) -> float:
    # A 1 lb yearling-weight increase adds ~1 lb of saleable weight for
    # calves retained past weaning.
    return a["price_per_lb"] * a["fraction_marketed"]


def _cw_value(a: dict[str, float]) -> float:
    # A 1 lb carcass-weight increase adds 1 lb of carcass sold on the rail.
    return a["carcass_price_per_lb"] * a["fraction_marketed"]


def _marb_value(a: dict[str, float]) -> float:
    # A 1-unit marbling-score increase raises the chance of grading up a
    # quality grade by `grade_shift_per_point`; each grade-up is worth
    # `premium_per_grade` on a carcass of `carcass_weight` lb.
    return (
        a["grade_shift_per_point"]
        * a["premium_per_grade"]
        * a["carcass_weight"]
        * a["fraction_marketed"]
    )


def _rea_value(a: dict[str, float]) -> float:
    # A 1 sq-in ribeye increase lifts yield grade and saleable red meat.
    return a["value_per_sqin"] * a["fraction_marketed"]


def _fat_value(a: dict[str, float]) -> float:
    # More backfat is a cost: it is trimmed and worsens yield grade.
    # Returned negative.
    return -a["discount_per_inch"] * a["fraction_marketed"]


def _ced_value(a: dict[str, float]) -> float:
    # CED is a percentage-point probability of an unassisted birth. A
    # 1-point rise avoids `0.01` of a difficult-birth event; each avoided
    # difficult birth saves `cost_per_dystocia`.
    return 0.01 * a["cost_per_dystocia"]


def _hp_value(a: dict[str, float]) -> float:
    # HP is a percentage-point probability a heifer is pregnant. A 1-point
    # rise yields 0.01 extra pregnancy; an open heifer costs
    # `cost_per_open_female`.
    return 0.01 * a["cost_per_open_female"]


def _stay_value(a: dict[str, float]) -> float:
    # STAY is a percentage-point probability a cow stays productive. A
    # 1-point rise avoids 0.01 of a premature replacement; each
    # replacement costs `cost_per_replacement`.
    return 0.01 * a["cost_per_replacement"]


def _mw_value(a: dict[str, float]) -> float:
    # A heavier mature cow costs more to maintain every year. A 1 lb
    # increase adds `annual_feed_cost_per_lb` of yearly carrying cost,
    # borne over the cow's `productive_years`. Returned negative.
    return -a["annual_feed_cost_per_lb"] * a["productive_years"]


def _milk_value(a: dict[str, float]) -> float:
    # MILK adds calf weaning weight through the dam. A 1 lb MILK EPD adds
    # ~1 lb of weaning weight on the calves of retained daughters.
    return a["price_per_lb"] * a["fraction_marketed"]


def _doc_value(a: dict[str, float]) -> float:
    # A calmer calf shrinks less and performs better; a 1-point docility
    # rise is worth `value_per_point` on a marketed calf.
    return a["value_per_point"] * a["fraction_marketed"]


def _dmi_value(a: dict[str, float]) -> float:
    # A 1 lb/day rise in dry-matter intake costs feed every day on feed.
    # Returned negative.
    return -a["feed_cost_per_lb"] * a["days_on_feed"]


def _pap_value(a: dict[str, float]) -> float:
    # PAP economic value depends on altitude. A 1 mmHg rise in PAP raises
    # the probability of a high-altitude death by `death_risk_per_mmHg`
    # for the at-risk share of the herd; each death costs `cost_per_death`.
    # At low elevation `death_risk_per_mmHg` is ~0, so PAP's value is ~0.
    # Returned negative (higher PAP is worse).
    return -(
        a["death_risk_per_mmHg"]
        * a["fraction_at_altitude"]
        * a["cost_per_death"]
    )


def _pap_latent_value(a: dict[str, float]) -> float:
    # Latent-z PAP is the logit-transformed PAP phenotype. Its economic
    # value is the raw-PAP value converted through the slope of the
    # transform at the herd's typical PAP. For a logit on the range
    # [L, U], dz/dy = (U - L) / [(y - L)(U - y)]; the raw-PAP value per
    # mmHg is divided by that slope to express it per latent-z unit.
    raw = _pap_value(a)
    L, U = 30.0, 150.0
    y = a["typical_pap"]
    # Guard against the bounds.
    y = min(max(y, L + 1e-6), U - 1e-6)
    dz_dy = (U - L) / ((y - L) * (U - y))
    # raw is dollars per mmHg; divide by dz/dy (latent-z per mmHg) to get
    # dollars per latent-z unit.
    return raw / dz_dy


_RECIPES: dict[str, EstimatorRecipe] = {
    "WW": EstimatorRecipe(
        "WW",
        (
            EstimatorQuestion(
                "price_per_lb",
                "What do you receive per pound of weaned calf?",
                "Your sale price per pound at weaning. If you sell at "
                "$2.10/lb, enter 2.10.",
                2.10, "$/lb", 0.0, 20.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _ww_value,
        "value = price per lb x fraction of calves sold",
        "Dollars per pound of weaning-weight EPD. Assumes a 1 lb EPD "
        "rise adds 1 lb of saleable calf.",
    ),
    "YW": EstimatorRecipe(
        "YW",
        (
            EstimatorQuestion(
                "price_per_lb",
                "What do you receive per pound of yearling / feeder "
                "weight?",
                "Sale price per pound for calves marketed past weaning.",
                1.95, "$/lb", 0.0, 20.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _yw_value,
        "value = price per lb x fraction of calves sold",
        "Dollars per pound of yearling-weight EPD. Use this when calves "
        "are marketed past weaning.",
    ),
    "CW": EstimatorRecipe(
        "CW",
        (
            EstimatorQuestion(
                "carcass_price_per_lb",
                "What is the carcass base price per pound?",
                "The base price per pound of hot carcass weight, before "
                "grid premiums. A $3.00/cwt base is $3.00 per lb.",
                3.00, "$/lb", 0.0, 20.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _cw_value,
        "value = carcass price per lb x fraction of calves sold",
        "Dollars per pound of carcass-weight EPD. Use when calves are "
        "sold on the rail.",
    ),
    "MARB": EstimatorRecipe(
        "MARB",
        (
            EstimatorQuestion(
                "grade_shift_per_point",
                "How much does one marbling-score point shift quality "
                "grade?",
                "The probability a one-point marbling rise moves a "
                "carcass up a quality grade. Around 0.30 is typical.",
                0.30, "fraction", 0.0, 1.0,
            ),
            EstimatorQuestion(
                "premium_per_grade",
                "What is the grid premium for grading up one quality "
                "grade ($/lb of carcass)?",
                "The per-pound carcass premium for moving up a grade "
                "(e.g. Select to Choice).",
                0.12, "$/lb", 0.0, 5.0,
            ),
            EstimatorQuestion(
                "carcass_weight",
                "What is the typical hot carcass weight (lb)?",
                "The hot carcass weight your cattle finish at.",
                850.0, "lb", 300.0, 1500.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _marb_value,
        "value = grade-shift per point x premium per grade x carcass "
        "weight x fraction sold",
        "Dollars per marbling-score point. Captures the grid value of a "
        "higher quality grade.",
    ),
    "REA": EstimatorRecipe(
        "REA",
        (
            EstimatorQuestion(
                "value_per_sqin",
                "What is one square inch of ribeye worth on your grid "
                "($)?",
                "The carcass value of one extra square inch of ribeye "
                "area, through improved yield grade and red-meat yield.",
                12.0, "$", 0.0, 200.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _rea_value,
        "value = value per sq in x fraction sold",
        "Dollars per square inch of ribeye-area EPD.",
    ),
    "FAT": EstimatorRecipe(
        "FAT",
        (
            EstimatorQuestion(
                "discount_per_inch",
                "What does an inch of extra backfat cost you ($)?",
                "The carcass value lost to one inch of extra external "
                "fat - trim loss and a worse yield grade.",
                200.0, "$", 0.0, 2000.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _fat_value,
        "value = -(discount per inch x fraction sold)",
        "Dollars per inch of backfat EPD. Negative: more fat is a cost.",
    ),
    "CED": EstimatorRecipe(
        "CED",
        (
            EstimatorQuestion(
                "cost_per_dystocia",
                "What does one difficult birth cost you ($)?",
                "The total cost of a difficult calving - veterinary and "
                "labour cost, plus the chance of losing the calf or "
                "harming the cow.",
                450.0, "$", 0.0, 5000.0,
            ),
        ),
        _ced_value,
        "value = 0.01 x cost per difficult birth",
        "Dollars per percentage point of calving-ease EPD. A 1-point "
        "rise avoids one in a hundred difficult births.",
    ),
    "HP": EstimatorRecipe(
        "HP",
        (
            EstimatorQuestion(
                "cost_per_open_female",
                "What does an open (non-pregnant) heifer cost you ($)?",
                "The net loss when a heifer fails to conceive - her "
                "development cost less her salvage value.",
                700.0, "$", 0.0, 5000.0,
            ),
        ),
        _hp_value,
        "value = 0.01 x cost per open female",
        "Dollars per percentage point of heifer-pregnancy EPD.",
    ),
    "STAY": EstimatorRecipe(
        "STAY",
        (
            EstimatorQuestion(
                "cost_per_replacement",
                "What does one replacement female cost you ($)?",
                "The net cost of replacing a cow - a developed or "
                "purchased replacement, less the culled cow's salvage "
                "value.",
                900.0, "$", 0.0, 5000.0,
            ),
        ),
        _stay_value,
        "value = 0.01 x cost per replacement female",
        "Dollars per percentage point of stayability EPD. A 1-point "
        "rise avoids one premature replacement in a hundred.",
    ),
    "MW": EstimatorRecipe(
        "MW",
        (
            EstimatorQuestion(
                "annual_feed_cost_per_lb",
                "What does one pound of mature cow weight cost to "
                "maintain per year ($)?",
                "The extra annual feed and pasture cost of carrying one "
                "more pound of cow. Often around $0.03-0.05/lb/year.",
                0.04, "$/lb/year", 0.0, 5.0,
            ),
            EstimatorQuestion(
                "productive_years",
                "How many years does a cow stay in the herd on average?",
                "The average productive lifespan of a cow - the number "
                "of years she carries the extra maintenance cost.",
                6.0, "years", 1.0, 20.0,
            ),
        ),
        _mw_value,
        "value = -(annual feed cost per lb x productive years)",
        "Dollars per pound of mature-weight EPD. Negative: a bigger cow "
        "costs more to maintain every year of her life.",
    ),
    "MILK": EstimatorRecipe(
        "MILK",
        (
            EstimatorQuestion(
                "price_per_lb",
                "What do you receive per pound of weaned calf?",
                "Sale price per pound at weaning - milk adds calf "
                "weaning weight through the dam.",
                2.10, "$/lb", 0.0, 20.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _milk_value,
        "value = price per lb x fraction of calves sold",
        "Dollars per pound of milk EPD. Milk is expressed as added calf "
        "weaning weight, so it is valued like weaning weight.",
    ),
    "DOC": EstimatorRecipe(
        "DOC",
        (
            EstimatorQuestion(
                "value_per_point",
                "What is one docility-score point worth per calf ($)?",
                "The value of calmer cattle per calf - less shrink, "
                "fewer injuries, better feedlot performance.",
                2.0, "$", 0.0, 100.0,
            ),
            _Q_FRACTION_SOLD,
        ),
        _doc_value,
        "value = value per point x fraction sold",
        "Dollars per docility-score point.",
    ),
    "DMI": EstimatorRecipe(
        "DMI",
        (
            EstimatorQuestion(
                "feed_cost_per_lb",
                "What does one pound of feed dry matter cost ($)?",
                "The cost per pound of dry-matter feed in the feedlot or "
                "backgrounding ration.",
                0.16, "$/lb", 0.0, 5.0,
            ),
            EstimatorQuestion(
                "days_on_feed",
                "How many days are cattle on feed?",
                "The total days a calf is on a measured ration "
                "(backgrounding plus feedlot).",
                200.0, "days", 0.0, 600.0,
            ),
        ),
        _dmi_value,
        "value = -(feed cost per lb x days on feed)",
        "Dollars per lb/day of dry-matter-intake EPD. Negative: eating "
        "more for the same gain is a cost.",
    ),
    "PAP": EstimatorRecipe(
        "PAP",
        (
            EstimatorQuestion(
                "death_risk_per_mmHg",
                "How much does each mmHg of PAP raise the annual "
                "death risk?",
                "At high elevation, the added probability of a "
                "high-altitude (brisket) death per mmHg of PAP. Near "
                "zero at low elevation; ~0.005-0.015 in high mountain "
                "country.",
                0.010, "fraction", 0.0, 0.2,
            ),
            EstimatorQuestion(
                "fraction_at_altitude",
                "What fraction of your herd grazes at altitude?",
                "The share of the herd exposed to high-altitude "
                "conditions where brisket disease occurs.",
                1.0, "fraction", 0.0, 1.0,
            ),
            EstimatorQuestion(
                "cost_per_death",
                "What does one animal lost to brisket disease cost "
                "you ($)?",
                "The economic loss of a productive animal lost to "
                "high-altitude disease.",
                1400.0, "$", 0.0, 10000.0,
            ),
        ),
        _pap_value,
        "value = -(death risk per mmHg x fraction at altitude x cost "
        "per death)",
        "Dollars per mmHg of PAP EPD. Negative: higher PAP is worse. "
        "At low elevation set the death risk near zero - PAP then "
        "carries almost no economic value.",
    ),
    "PAP_L": EstimatorRecipe(
        "PAP_L",
        (
            EstimatorQuestion(
                "death_risk_per_mmHg",
                "How much does each mmHg of PAP raise the annual "
                "death risk?",
                "At high elevation, the added probability of a "
                "high-altitude (brisket) death per mmHg of PAP.",
                0.010, "fraction", 0.0, 0.2,
            ),
            EstimatorQuestion(
                "fraction_at_altitude",
                "What fraction of your herd grazes at altitude?",
                "The share of the herd exposed to high-altitude "
                "conditions.",
                1.0, "fraction", 0.0, 1.0,
            ),
            EstimatorQuestion(
                "cost_per_death",
                "What does one animal lost to brisket disease cost "
                "you ($)?",
                "The economic loss of a productive animal lost to "
                "high-altitude disease.",
                1400.0, "$", 0.0, 10000.0,
            ),
            EstimatorQuestion(
                "typical_pap",
                "What is the typical raw PAP of your herd (mmHg)?",
                "The mean PAP of your cattle. Used to convert the "
                "per-mmHg value onto the latent (logit) scale.",
                41.0, "mmHg", 31.0, 149.0,
            ),
        ),
        _pap_latent_value,
        "value = raw-PAP value per mmHg / (latent-z per mmHg), where "
        "latent-z per mmHg is the slope of the logit transform at the "
        "herd's typical PAP",
        "Dollars per latent-z unit of the latent-scale PAP EPD. The "
        "latent-z trait is dimensionless, so its value is converted from "
        "the per-mmHg value through the transform's local slope.",
    ),
}


def available_recipes() -> list[str]:
    """Return the trait codes that have an economic-value recipe."""
    return list(_RECIPES)


def get_recipe(trait_code: str) -> EstimatorRecipe:
    """Return the estimator recipe for ``trait_code``.

    Raises
    ------
    KeyError
        If the trait has no recipe. The message lists the traits that do.
    """
    try:
        return _RECIPES[trait_code]
    except KeyError:
        valid = ", ".join(sorted(_RECIPES))
        raise KeyError(
            f"No economic-value recipe for trait {trait_code!r}. "
            f"Recipes exist for: {valid}."
        ) from None


def estimate_economic_value(
    trait_code: str,
    answers: dict[str, float] | None = None,
) -> EstimateResult:
    """Estimate the economic value of a trait from plain-language answers.

    Parameters
    ----------
    trait_code:
        The trait to estimate a value for.
    answers:
        A mapping of question key -> answer value. Any question not
        answered falls back to its default, so a partial (or empty)
        answer set still yields a number.

    Returns
    -------
    EstimateResult
        The estimated economic value, the formula used, and the inputs.
    """
    recipe = get_recipe(trait_code)
    answers = dict(answers or {})

    # Fill in defaults and clamp every answer to its permitted range.
    resolved: dict[str, float] = {}
    for q in recipe.questions:
        raw = float(answers.get(q.key, q.default))
        resolved[q.key] = min(max(raw, q.minimum), q.maximum)

    value = recipe.formula(resolved)
    return EstimateResult(
        trait_code=trait_code,
        economic_value=value,
        formula_text=recipe.formula_text,
        basis_note=recipe.basis_note,
        inputs_used=resolved,
    )
