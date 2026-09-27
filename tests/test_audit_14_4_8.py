"""Audit of the §14.4.8 budget (nsaudit/audit_14_4_8_budget.py): the numbers the verdicts cite."""
from nsaudit import audit_14_4_8_budget as a


def close(x, y, tol):
    return abs(x - y) <= tol * abs(y)


def test_thermochemistry():
    """ΔG = 1.68e7 - 300 × 8.2e3 ≈ 1.43e7 J/kg (book: 1.7e7 - 1.7e6 = 1.5e7)."""
    assert close(a.DG, 1.43e7, 0.01)


def test_mill_term_scenarios():
    """A ~2.0e6 (book intent), B ~8.7e6 (conditional repetition), C ~7.3e7 (route 1, the
    book's own naive 7e7)."""
    assert close(a.mill_term("A"), 2.0e6, 0.01)
    assert close(a.mill_term("B"), 8.7e6, 0.01)
    assert close(a.mill_term("C"), 7.3e7, 0.01)


def test_computation_term_from_ch12():
    """12.7.4's 0.03 maJ/interlock gives 7.4e4 J/kg (book rounds to 1e5); Ch. 12's own
    per-interlock and per-rod counts with the +15% 7.4.2 bound give 2.0e5 and 2.9e5."""
    t = {k: a.computation_term(v) for k, v in a.interlock_terms().items()}
    assert close(t["book"], 7.4e4, 0.01)
    assert close(t["per-interlock"], 2.0e5, 0.02)
    assert close(t["per-rod"], 2.9e5, 0.02)


def test_negligible_terms_are_small():
    """Sorting ~1e5 J/kg and manipulators ~1.5e4 J/kg: each < 5% of even the low-end budget."""
    assert close(a.sorting_term(), 1.0e5, 0.1)
    assert close(a.manipulator_term(), 1.5e4, 0.01)
    low = a.budget("A").dissipated
    assert a.sorting_term() < 0.05 * low and a.manipulator_term() < 0.05 * low


def test_book_itemisation_vs_total():
    """The book's itemised terms sum to 2.1e6; it carries 3.1e6."""
    assert close(a.BOOK.dissipated, 2.1e6, 1e-9)


def test_scenario_A_matches_book():
    """Under the book's intended physics the budget holds: 2.8e6 dissipated (< the 3.1e6
    carried), surplus 1.14e7 (book 1.2e7), waste 1.5 kW per kg/hr, within 1.8 kW air cooling."""
    b = a.budget("A")
    assert close(b.dissipated, 2.83e6, 0.01)
    assert close(b.surplus, 1.14e7, 0.01)
    assert b.waste_power() < a.AIR_COOLING


def test_scenario_B_net_producer_but_cooling_short():
    """B: still a net producer (+2.8e6 J/kg) but 3.9 kW of waste heat, ~2.1× the stated air
    cooling."""
    b = a.budget("B")
    assert b.surplus > 0
    assert close(b.waste_power(), 3.9e3, 0.02)
    assert close(b.waste_power() / a.AIR_COOLING, 2.1, 0.05)


def test_scenario_C_net_consumer():
    """C: dissipation 8.2e7 J/kg exceeds ΔG ~5.7×; the system consumes ~6.8e7 J/kg; waste heat
    ~23.5 kW per kg/hr, ~13× the air cooling."""
    b = a.budget("C")
    assert b.surplus < 0 and close(b.surplus, -6.8e7, 0.01)
    assert close(b.dissipated / a.DG, 5.7, 0.02)
    assert close(b.waste_power() / a.AIR_COOLING, 13, 0.05)


def test_uncertainty_span():
    """Dissipation spans 2.8e6 to 8.2e7 J/kg: ~1.5 orders of magnitude, upward only."""
    import math
    span = math.log10(a.budget("C").dissipated / a.budget("A").dissipated)
    assert close(span, 1.46, 0.02)
