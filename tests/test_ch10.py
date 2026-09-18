"""Reproduce the worked numbers of §10.3.4-10.3.6 and §10.4.6, and re-derive the diamond constants."""
import math
import pytest
from nsaudit import ch10, ch07

kT = ch07.K_B * 300


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


def test_10_3_4b_contact_acoustic_radiation():
    """ΔV = 1 maJ, diamond, k = 2.2e10 -> ~3e-19 W at 1 m/s, ~3e-23 at 1 cm/s."""
    assert close(ch10.p_rad_contact(1e-21, 1.0, 2.2e10), 3e-19, 0.1)
    assert close(ch10.p_rad_contact(1e-21, 0.01, 2.2e10), 3e-23, 0.1)


def test_10_3_4c_contact_thermoelastic_loaded_region():
    """Δp = 1 GPa, l = 1 nm, V = 1 nm^3, K_T = 10, t_cycle = l/v at 1 m/s -> ~1e-27 J/cycle, ~1e-18 W."""
    tau = ch07.tau_therm(1.7e6, 10, 1e-9)
    w = ch07.cycle_loss_thermoelastic(3.5e-6, 300, 1.7e6, 1e9, 1e-27, tau, 1e-9)
    assert close(w, 1e-27, 0.35)        # 7.3e-28
    assert close(w / 1e-9, 1e-18, 0.35)


def test_10_3_4c_alternating_force_case_not_reproduced():
    """The book gives ~3e-30 J/cycle for the alternating-force part. Taking F from Eq. 10.6 at
    ΔV = 1 maJ over 1 nm^2 gives Δp = 17 MPa and ~2e-31 J with the same recipe: 15x below the
    printed figure. The inputs behind 3e-30 are not stated. Recorded, not asserted."""
    dp = ch10.f_max_from_barrier(1e-21) / 1e-18
    tau = ch07.tau_therm(1.7e6, 10, 1e-9)
    w = ch07.cycle_loss_thermoelastic(3.5e-6, 300, 1.7e6, dp, 1e-27, tau, 1e-9)
    assert w < 3e-30


def test_10_3_5_static_friction():
    assert close(ch10.static_friction(1e-21, 0.25e-9) / 1e-21, 0.05e-9 / 1e-21, 0.01)


def test_10_3_6_negative_stiffness_and_rod():
    assert close(ch10.negative_stiffness_bound(1e-21, 0.25e-9), 0.5, 0.07)   # 0.47
    assert close(1.05e12 * 1e-18 / 10e-9, 100, 0.06)


def test_10_4_6a_torsional_radiation():
    """ΔV = 1 maJ, r = 1 nm, v = 1 m/s, d_a = 0.25 nm, diamondlike -> 'P_rad ≈ 1e-25 W'. Eq. 10.16
    gives 4.9e-25 with G = E/2; the book's rounding is downward by 5x."""
    p = ch10.p_rad_torsional_bearing(1e-21, 1e-9, 1.0, 0.25e-9)
    assert 1e-25 < p < 1e-24


def test_10_4_6a_force_radiation_and_critical_speed():
    assert close(ch10.p_rad_force_bearing(1e-10, 1.0, 0.25e-9), 1e-17, 0.4)   # 1.4e-17 for F = 0.1 nN
    assert close(ch10.p_rad_force_bearing(1e-13, 1.0, 0.25e-9), 1e-23, 0.4)
    m = 3500 * (3e-9)**3
    assert close(ch10.critical_sliding_speed(0.25e-9, 1000, m), 100, 0.3)   # ~130


def test_10_4_6b_transmission_constant_requires_measured_TD_and_n_plus_third():
    """Eq. 10.19's 2.4e-37 follows from Eq. 7.41 with diamond M = 1.05e12, n = 176/nm^3 and
    T_D = 2230 K (the measured value), reading d_n as n^{+1/3} M/k_a. With the 1570 K that the
    printed Eq. 7.29 yields, the constant would be 1.5e-37."""
    c_meas = ch10.t_trans_coefficient(T_D=ch10.DIAMOND_TD_MEASURED)
    c_729 = ch10.t_trans_coefficient(T_D=ch10.DIAMOND_TD_EQ7_29)
    assert close(c_meas, 2.4e-37, 0.1)
    assert not close(c_729, 2.4e-37, 0.2)
    assert close(ch10.t_trans_bearing(1e19), 2.4e-37 * (1e19)**1.7, 0.01)   # z << 1 regime


def test_10_4_6b_shear_reflection_constants_and_example():
    """1.8e-33 = (eps/2) 2.4e-37 / v_s with eps = 2e8, v_s = 1.38e4; 1.6e-33 = 1.8e-33 × 0.897;
    r = l = 2 nm, k_s = 1000 -> 3e-16 W at 1 m/s, 3e-20 at 1 cm/s."""
    assert close(ch10.shear_reflection_coefficient(), 1.8e-33, 0.05)
    assert close(1.8e-33 * ch10.cyl_conversion(), 1.6e-33, 0.02)
    assert close(ch10.p_drag_shear_reflection(1000, 2e-9, 2e-9, 1.0), 3e-16, 0.1)
    assert close(ch10.p_drag_shear_reflection(1000, 2e-9, 2e-9, 0.01), 3e-20, 0.1)


def test_10_4_6c_band_stiffness_constants_and_examples():
    """3.0e-33 = 0.85 × (eps/v_s) × 2.4e-37; 2.7e-33 after the cylinder conversion;
    R = 10, Δk/k = 0.4 -> ~2e-14 W; 0.003 -> ~1.5e-16 W."""
    c = 0.85 * ch10.EPS_300 / ch10.DIAMOND_V_S * 2.4e-37
    assert close(c, 3.0e-33, 0.05)
    assert close(c * ch10.cyl_conversion(), 2.7e-33, 0.03)
    assert close(ch10.p_drag_band_stiffness(1000, 2e-9, 2e-9, 10, 0.4, 1.0), 2e-14, 0.05)
    assert close(ch10.p_drag_band_stiffness(1000, 2e-9, 2e-9, 10, 0.003, 1.0), 1.5e-16, 0.05)


def test_10_4_6d_band_flutter_example():
    """k_a = 8e19, Δk/k = 0.4, R = 10, d_a = 0.25 nm -> w ≈ 0.4 nm, P < 5e-18 W."""
    dp, w, A = ch10.flutter_amplitude(8e19, 0.4, 10, 0.25e-9)
    assert close(w, 0.4e-9, 0.01)
    p = ch10.p_drag_band_flutter(1000, 2e-9, 2e-9, 10, A / 0.25e-9, 1.0)
    assert close(p, 5e-18, 0.1)
    c = ch10.EPS_300 / ch10.DIAMOND_V_S * 2.4e-37 * (2 * math.pi)**2 * ch10.cyl_conversion()
    assert close(c, 1.2e-31, 0.07)


def test_10_4_6e_thermoelastic_constant_and_examples():
    """4.3e-27 = 2 beta^2 T tau / C_vol (Eq. 7.50 form with t_cycle = d_a/v, tau = 1e-12 s).
    Δk/k = 0.4 -> ~6e-16 W. The 0.003 case prints ~8e-20 W; scaling by (0.003/0.4)^2 gives 3.6e-20."""
    assert close(ch10.thermoelastic_coefficient(), 4.3e-27, 0.02)
    dp, w, _ = ch10.flutter_amplitude(8e19, 0.4, 10, 0.25e-9)
    p = ch10.p_drag_thermoelastic(2e-9, 2e-9, w, dp, 1.0, 0.25e-9)
    assert close(p, 6e-16, 0.1)
    dp2, _, _ = ch10.flutter_amplitude(8e19, 0.003, 10, 0.25e-9)
    p2 = ch10.p_drag_thermoelastic(2e-9, 2e-9, w, dp2, 1.0, 0.25e-9)
    assert 2e-20 < p2 < 8e-20


def test_10_4_6e_tau_therm_1e_12_is_conservative_vs_eq_7_51():
    """Eq. 7.51 for the 0.4 nm stress region gives 2.7e-14 s (K_T = 10) or 3.9e-22 s (K_T = 700);
    the 1e-12 s used is 40x-2.5e9x larger: conservative direction for loss."""
    assert ch07.tau_therm(1.7e6, 10, 0.4e-9) < 1e-12 / 30


def test_10_4_6f_total_drag_bound():
    """k_s = 1000, r = l = 2 nm, R = 10: 2.7e-14 v^2 W (0.4) and 5.8e-16 v^2 W (0.003)."""
    assert close(ch10.p_drag_total(1000, 2e-9, 2e-9, 10, 0.4, 1.0), 2.7e-14, 0.05)
    assert close(ch10.p_drag_total(1000, 2e-9, 2e-9, 10, 0.003, 1.0), 5.8e-16, 0.05)
    assert close(1.6e-33 * 1.3, 2.0e-33, 0.05)
    assert close(2.7e-33 * 1.3, 3.5e-33, 0.05)


def test_10_4_6f_energy_per_rotation_vs_0_06_kT():
    """'< 0.06 kT_300 per rotation' at 1 m/s using the 2.7e-14 W bound: 2.7e-14 × 2 pi r / v =
    3.4e-22 J = 0.082 kT. The printed 0.06 is 25% lower than its own inputs give."""
    e = ch10.energy_per_rotation(2.7e-14, 2e-9, 1.0)
    assert close(e / kT, 0.082, 0.05)
    assert not close(e / kT, 0.06, 0.15)


def test_10_4_6f_power_density():
    """'~1e11 W/m^3': 2.7e-14 W over the interface cylinder pi r^2 l = 2.5e-26 m^3 is 1.1e12; an
    outer radius of ~6 nm is needed for 1e11. Order-of-magnitude statement; volume not defined."""
    assert close(2.7e-14 / (math.pi * (2e-9)**2 * 2e-9), 1.1e12, 0.05)
