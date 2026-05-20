"""
Economic layer of the osit-sim herd simulation.

Turns the physical output of the simulated herd - calves of given weights
and carcass merit - into dollars, according to the sale endpoint and the
economic scenario. Two public functions:

* endpoint_revenue - the sale value of one calf.
* herd_costs - the annual cost of running the cow herd.

Reference: NexGenIQ Phase 3 Part 3B Section 2.5.1; Phase 2 Section 1.3.1.
"""

from __future__ import annotations

import numpy as np

from .inputs import EconomicScenario, SaleEndpoint

# Conversion / growth assumptions used to project a calf forward from
# weaning to a later sale endpoint. Constants of the economic model.
_ADG_BACKGROUND = 1.8   # lb/day average daily gain, backgrounding
_ADG_FEEDLOT = 3.3      # lb/day average daily gain, feedlot
_DM_PER_LB_GAIN = 6.5   # lb dry matter consumed per lb of gain
_DRESSING_PCT = 0.63    # carcass weight as a fraction of live weight

# The reference cow weight an animal-unit-month is defined for (1,000 lb).
_AUM_REFERENCE_WEIGHT = 1000.0


def _quality_grade(marbling: float, rng: np.random.Generator) -> str:
    """Map a marbling score to a USDA quality grade.

    Marbling is on a score scale where ~5.0 is low Choice. A small random
    component reflects the imperfect link between score and grader call.
    """
    score = marbling + rng.normal(0.0, 0.25)
    if score >= 7.0:
        return "Prime"
    if score >= 5.0:
        return "Choice"
    if score >= 4.0:
        return "Select"
    return "Standard"


def _yield_grade(rea: float, fat: float, carcass_wt: float) -> int:
    """Compute a USDA yield grade (1-5) from carcass measures.

    A simplified USDA yield-grade equation: more external fat raises the
    grade (worse), more ribeye per unit carcass lowers it.
    """
    yg = 2.5 + 6.35 * fat - 0.32 * rea + 0.0017 * carcass_wt
    return int(min(5, max(1, round(yg))))


def endpoint_revenue(
    traits: dict[str, float],
    sex: str,
    economics: EconomicScenario,
    rng: np.random.Generator,
) -> float:
    """Return the sale revenue for one calf at the scenario's endpoint.

    Parameters
    ----------
    traits:
        The calf's simulated trait values.
    sex:
        "S" steer or "F" heifer.
    economics:
        The economic scenario - endpoint, prices, grid, costs.
    rng:
        Random generator, for the small stochastic element in grading.

    Returns
    -------
    float
        Net sale revenue for the calf (sale value minus any post-weaning
        feed cost incurred to reach the endpoint).
    """
    endpoint = economics.sale_endpoint
    weaning_wt = traits.get("WW", 0.0)

    if endpoint is SaleEndpoint.WEANING:
        price = economics.price_for(sex, weaning_wt)
        return (weaning_wt / 100.0) * price

    if endpoint is SaleEndpoint.BACKGROUND:
        gain = _ADG_BACKGROUND * economics.background_days
        out_wt = weaning_wt + gain
        feed_cost = gain * _DM_PER_LB_GAIN * economics.feed_cost_per_lb_dm
        price = economics.price_for(sex, out_wt)
        return (out_wt / 100.0) * price - feed_cost

    if endpoint is SaleEndpoint.FED:
        bg_gain = _ADG_BACKGROUND * economics.background_days
        fl_gain = _ADG_FEEDLOT * economics.days_on_feed
        total_gain = bg_gain + fl_gain
        out_wt = weaning_wt + total_gain
        feed_cost = (
            total_gain * _DM_PER_LB_GAIN * economics.feed_cost_per_lb_dm
        )
        price = economics.price_for(sex, out_wt)
        return (out_wt / 100.0) * price - feed_cost

    # CARCASS: reach a finished weight, value the carcass on the grid.
    bg_gain = _ADG_BACKGROUND * economics.background_days
    fl_gain = _ADG_FEEDLOT * economics.days_on_feed
    total_gain = bg_gain + fl_gain
    live_wt = weaning_wt + total_gain
    feed_cost = total_gain * _DM_PER_LB_GAIN * economics.feed_cost_per_lb_dm

    carcass_wt = traits.get("CW") or live_wt * _DRESSING_PCT
    quality = _quality_grade(traits.get("MARB", 5.0), rng)
    yg = _yield_grade(
        traits.get("REA", 13.0), traits.get("FAT", 0.5), carcass_wt
    )
    premium = economics.grid_premium(quality, yg)
    price = economics.carcass_base_price + premium
    return (carcass_wt / 100.0) * price - feed_cost


def herd_costs(herd, genetics, economics: EconomicScenario) -> float:
    """Return the annual cost of running the cow herd.

    Comprises pasture cost and the per-cow fixed cost (labour, health,
    overhead). Pasture cost is size-dependent: an animal-unit-month is
    defined for a 1,000 lb cow, so a heavier cow consumes proportionally
    more AUMs. This is the mechanism by which mature cow weight (MW)
    carries a negative economic value in a cow-calf system - a bigger cow
    costs more to maintain every year of her life.

    Parameters
    ----------
    herd:
        The list of cows (each carrying a genetic MW deviation).
    genetics:
        Per-trait genetics, used for the base mature weight.
    economics:
        The economic scenario.

    Returns
    -------
    float
        Total annual herd cost in dollars.
    """
    base_mw = genetics["MW"].mean
    pasture = 0.0
    for cow in herd:
        cow_weight = base_mw + cow.genetics.get("MW", 0.0)
        aums = 12.0 * (cow_weight / _AUM_REFERENCE_WEIGHT)
        pasture += aums * economics.aum_cost
    fixed = len(herd) * economics.fixed_cost_per_cow
    return pasture + fixed
