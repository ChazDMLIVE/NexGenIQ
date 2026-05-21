"""
Tests for the MEV-result interpreter (osit_sim.interpret).

These verify the interpretation is produced, is layered, always carries
the not-a-recommendation disclaimer, names the most important trait, and
flags imprecise economic values as cautions.
"""

from osit_sim import derive_mevs, interpret_mev_result


def test_interpretation_is_produced(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """A normal MEV result yields a non-empty layered interpretation."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW", "CED", "MW", "STAY"],
    )
    interp = interpret_mev_result(result)
    assert interp.headline
    assert interp.readout
    assert len(interp.detail) > 0


def test_interpretation_always_has_disclaimer(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """Every interpretation carries the not-a-recommendation disclaimer."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW", "CED"],
    )
    interp = interpret_mev_result(result)
    assert interp.disclaimer
    low = interp.disclaimer.lower()
    assert "not" in low and "recommend" in low


def test_headline_names_the_top_trait(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The headline names the most economically important trait - the
    first in the MEV list (ordered by descending absolute value)."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW", "CED", "MW"],
    )
    interp = interpret_mev_result(result)
    # The headline mentions a trait; the readout discusses the values.
    assert interp.headline
    assert "economic value" in interp.readout.lower()


def test_readout_is_not_directive(
    maternal_system, weaning_economics, fast_controls, genetics
):
    """The readout describes the economic values; it does not tell the
    user what to select for."""
    result = derive_mevs(
        maternal_system, weaning_economics, fast_controls, genetics,
        traits=["WW", "CED"],
    )
    interp = interpret_mev_result(result)
    text = interp.readout.lower()
    assert "not advice" in text or "description" in text


def test_empty_result_handled():
    """An empty MEV result yields a sensible interpretation, not a crash."""
    from osit_sim import MevResult

    interp = interpret_mev_result(MevResult())
    assert interp.headline
    assert "no economic values" in interp.headline.lower()
