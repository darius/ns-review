"""Reproduce the published §7.4 figures. Tolerances are stated per test; 'rel' is relative."""
import math
import pytest
from nsaudit import ch07


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


def test_grueneisen_diamond_0_9():
    """§7.4.1: gamma_G ≈ 0.9 for diamond."""
    g = ch07.grueneisen(ch07.DIAMOND_BETA, ch07.DIAMOND_K, ch07.DIAMOND_C_VOL)
    assert close(g, 0.9, 0.02)


def test_worst_case_coefficient_2_2e_24_J_per_nm3_GPa2():
    """§7.4.1: worst-case cycle ≈ 2.2e-24 (Δp)^2 J/nm^3·cycle with p in GPa."""
    coef = ch07.worst_case_cycle_thermoelastic(ch07.DIAMOND_BETA, 300, ch07.DIAMOND_C_VOL, 1e9, 1e-27)
    assert close(coef, 2.2e-24, 0.03)


def test_tau_therm_worked_example():
    """§7.4.1: K_T=10, l=10 nm, C_vol=2e6 -> tau_therm ≈ 1e-11 s. The diffusive term alone gives
    2e-11; the book's '≈ 1e-11' is a factor-2 rounding. Tolerance is a factor of 2.5."""
    t = ch07.tau_therm(2e6, 10, 10e-9)
    assert 1e-11 / 2.5 < t < 1e-11 * 2.5


def test_isothermal_reduction_factors():
    """§7.4.1: reduction ~1e-2 at 1 GHz, ~1e-5 at 1 MHz relative to worst case (tau=1e-11)."""
    args = (3.5e-6, 300, 2e6, 1e8, 1e-27)
    worst = ch07.worst_case_cycle_thermoelastic(*args)
    r_ghz = ch07.cycle_loss_thermoelastic(*args, 1e-11, 1e-9) / worst
    r_mhz = ch07.cycle_loss_thermoelastic(*args, 1e-11, 1e-6) / worst
    assert 1e-2 / 2.5 < r_ghz < 1e-2 * 2.5
    assert 1e-5 / 2.5 < r_mhz < 1e-5 * 2.5


def test_p_drag_worked_example_4_W_per_m2():
    """§7.4.3: beta=3.5e-6, K_T=10, l=10 nm, R=10, T=300, Δp=1e8 -> ~4 W/m^2 at 1 m/s."""
    p1 = ch07.p_drag_per_area(3.5e-6, 300, 10, 10e-9, 1e8, 10, 1.0)
    assert close(p1, 4.0, 0.1)


@pytest.mark.xfail(strict=True, reason="book says 0.04 W/m^2 at 1 cm/s, but Eq. 7.54 is ∝ v^2, giving 4e-4; "
                   "text and equation disagree (spot check on 7.4.3/moving-part-drag, not a verdict)")
def test_p_drag_at_1_cm_s_book_figure():
    p2 = ch07.p_drag_per_area(3.5e-6, 300, 10, 10e-9, 1e8, 10, 0.01)
    assert close(p2, 0.04, 0.1)


def test_eq_7_49_equals_relaxation_strength_times_elastic_energy():
    """Consistency: Drexler's ΔW (Eq. 7.49) is Δ × (½ dp^2 V / K) with Δ = gamma^2 C T / K."""
    beta, T, C, K, dp, V = 3.5e-6, 300, 1.7e6, 4.4e11, 1e9, 1e-27
    gamma = ch07.grueneisen(beta, K, C)
    lhs = ch07.delta_w_thermoelastic(beta, T, C, dp, V)
    rhs = ch07.relaxation_strength(gamma, C, T, K) * 0.5 * dp**2 * V / K
    assert close(lhs, rhs, 1e-9)


def test_akhiezer_peak_is_half_delta():
    assert close(ch07.akhiezer_q_inverse(1e-3, 1.0, 1.0), 5e-4, 1e-9)


def test_landau_rumer_crossover_from_prase_fq():
    """DECISIONS.md: backing tau out of the f·Q = 3.7e13 Hz ceiling Prase cites gives a
    crossover (omega·tau = 1) of ~10-30 GHz, not ~1 THz (Prase fn. 28). Diamond: rho=3500,
    v = 1.2e4 (mean) to 1.8e4 (longitudinal), C=1.7e6, T=300, gamma=0.9."""
    taus = [ch07.tau_from_fq_max(3500, v, 1.7e6, 300, 0.9, 3.7e13) for v in (1.2e4, 1.8e4)]
    for tau in taus:
        f_cross = 1 / (2 * math.pi * tau)
        assert 3e-12 < tau < 2e-11
        assert 8e9 < f_cross < 6e10
