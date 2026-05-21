"""
Economic layer of the osit-sim herd simulation.

Turns the physical output of the simulated herd - calves of given weights
and carcass merit - into dollars, according to the sale endpoint and the
economic scenario. Two public functions:

* endpoint_revenue - the sale value of one calf.
* herd_costs - the annual cost of running the cow herd.

Every economically relevant trait is wired in here or in herd.py, so a
perturbation of any trait moves simulated profit and the MEV engine can
derive a non-zero economic value for it:

* WW            -> weaning sale weight, and the base for later endpoints.
* YW / PWG      -> post-weaning growth rate, hence feedlot out-weight.
* DMI / RFI     -> feed cost per pound of gain (efficiency).
* CW            -> hot carcass weight on the rail.
* MARB          -> quality grade, hence grid premium.
* REA / FAT     -> yield grade, hence grid premium.
* DOC           -> yard shrink / death loss and a small price effect.
* BW            -> handled in herd.py (dystocia / calving loss).
* MW            -> handled in herd_costs (size-dependent pasture cost).
* PAP           -> handled in herd.py (altitude death loss / culling).

Reference: NexGenIQ Phase 3 Part 3B Section 2.5.1; Phase 2 Section 1.3.1.
"""

from __future__ import annotations

import numpy as np

from .inputs import EconomicScenario, SaleEndpoint

# Conversion / growth assumptions used to project a calf forward from
# weaning to a later sale endpoint. Constants of the economic model.
_ADG_BACKGROUND = 1.8   # lb/day average daily gain, backgrounding (base)
_ADG_FEEDLOT = 3.3      # lb/day average daily gain, feedlot (base)
_DM_PER_LB_GAIN = 6.5   # lb dry matter consumed per lb of gain (base)
_DRESSING_PCT = 0.63    # carcass weight as a fraction of live weight

# The reference cow weight an animal-unit-month is defined for (1,000 lb).
_AUM_REFERENCE_WEIGHT = 1000.0

# --- Trait-response constants --------------------------------------------
# Genetic means the economic responses are referenced against. A calf's
# trait value is compared to its mean; the deviation drives the response.
_YW_MEAN = 850.0        # yearling-weight mean (growth reference)
_DMI_MEAN = 22.0        # dry-matter-intake mean (lb/day)
_DOC_MEAN = 22.0        # docility-score mean
_CW_MEAN = 800.0        # carcass-weight mean (lb)

# How strongly post-weaning gain responds to yearling-weight genetics:
# a calf one YW genetic SD above the mean gains proportionally faster
# through the feedlot. Expressed as fractional ADG change per lb of YW
# deviation.
_GAIN_PER_LB_YW = 0.0011

# Feed efficiency: a calf's dry-matter conversion improves with a lower
# DMI deviation and a lower (more negative) RFI. Expressed as the change
# in lb DM per lb gain per unit of trait deviation.
_DM_PER_LB_DMI = 0.030   # per lb/day of DMI deviation above the mean
_DM_PER_LB_RFI = 0.65    # per lb/day of RFI (RFI mean is 0)

# Docility: calmer cattle shrink less and suffer less yard morbidity.
# A calf one docility point above the mean realises this fractional
# uplift on its net sale value.
_DOC_VALUE_PER_POINT = 0.004


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


def _feedlot_adg(traits: dict[str, float], base_adg: float) -> float:
    """Return the average daily gain for a calf, adjusted for its genetics.

    A calf with above-average yearling-weight genetics gains faster; the
    response is the YW deviation times :data:`_GAIN_PER_LB_YW`. Post-weaning
    gain (PWG), if present, adds directly on the same footing. The result
    is clamped to a sensible positive range.
    """
    yw_dev = traits.get("YW", _YW_MEAN) - _YW_MEAN
    pwg_dev = traits.get("PWG", 0.0)
    # PWG is already a deviation-style growth measure in the sim genetics.
    frac = _GAIN_PER_LB_YW * (yw_dev + pwg_dev)
    return max(0.5, base_adg * (1.0 + frac))


def _dm_per_lb_gain(traits: dict[str, float]) -> float:
    """Return lb of dry matter per lb of gain, adjusted for efficiency.

    An efficient calf - lower dry-matter intake, lower (more negative)
    residual feed intake - converts feed to gain on fewer pounds of dry
    matter. The result is clamped so it stays physically sensible.
    """
    dmi_dev = traits.get("DMI", _DMI_MEAN) - _DMI_MEAN
    rfi = traits.get("RFI", 0.0)
    conversion = (
        _DM_PER_LB_GAIN
        + _DM_PER_LB_DMI * dmi_dev
        + _DM_PER_LB_RFI * rfi
    )
    return max(3.5, min(10.0, conversion))


def _docility_multiplier(traits: dict[str, float]) -> float:
    """Return a small price multiplier reflecting docility.

    Calmer cattle shrink less in transit and suffer less yard morbidity,
    realising slightly more of their gross value. Centred on 1.0.
    """
    doc_dev = traits.get("DOC", _DOC_MEAN) - _DOC_MEAN
    return 1.0 + _DOC_VALUE_PER_POINT * doc_dev


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
    doc_mult = _docility_multiplier(traits)

    if endpoint is SaleEndpoint.WEANING:
        price = economics.price_for(sex, weaning_wt)
        return (weaning_wt / 100.0) * price * doc_mult

    # Growth- and efficiency-adjusted projection forward to the endpoint.
    dm_per_gain = _dm_per_lb_gain(traits)

    if endpoint is SaleEndpoint.BACKGROUND:
        adg = _feedlot_adg(traits, _ADG_BACKGROUND)
        gain = adg * economics.background_days
        out_wt = weaning_wt + gain
        feed_cost = gain * dm_per_gain * economics.feed_cost_per_lb_dm
        price = economics.price_for(sex, out_wt)
        return (out_wt / 100.0) * price * doc_mult - feed_cost

    if endpoint is SaleEndpoint.FED:
        bg_adg = _feedlot_adg(traits, _ADG_BACKGROUND)
        fl_adg = _feedlot_adg(traits, _ADG_FEEDLOT)
        bg_gain = bg_adg * economics.background_days
        fl_gain = fl_adg * economics.days_on_feed
        total_gain = bg_gain + fl_gain
        out_wt = weaning_wt + total_gain
        feed_cost = total_gain * dm_per_gain * economics.feed_cost_per_lb_dm
        price = economics.price_for(sex, out_wt)
        return (out_wt / 100.0) * price * doc_mult - feed_cost

    # CARCASS: reach a finished weight, value the carcass on the grid.
    bg_adg = _feedlot_adg(traits, _ADG_BACKGROUND)
    fl_adg = _feedlot_adg(traits, _ADG_FEEDLOT)
    bg_gain = bg_adg * economics.background_days
    fl_gain = fl_adg * economics.days_on_feed
    total_gain = bg_gain + fl_gain
    live_wt = weaning_wt + total_gain
    feed_cost = total_gain * dm_per_gain * economics.feed_cost_per_lb_dm

    # Hot carcass weight: use the calf's carcass-weight genetics if the
    # simulation tracked CW, otherwise derive it from the live weight.
    # When CW is tracked, add its deviation around the CW mean onto the
    # projected dressed weight so carcass-weight genetics feed through.
    if "CW" in traits:
        carcass_wt = live_wt * _DRESSING_PCT + (traits["CW"] - _CW_MEAN)
    else:
        carcass_wt = live_wt * _DRESSING_PCT
    carcass_wt = max(300.0, carcass_wt)

    quality = _quality_grade(traits.get("MARB", 5.0), rng)
    yg = _yield_grade(
        traits.get("REA", 13.0), traits.get("FAT", 0.5), carcass_wt
    )
    premium = economics.grid_premium(quality, yg)
    price = economics.carcass_base_price + premium
    return (carcass_wt / 100.0) * price * doc_mult - feed_cost


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
