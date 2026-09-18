"""Reproduce the published exemplar-rod figures of §12.3–12.4 and §12.7.4."""
import math
import pytest
from nsaudit import ch12
from nsaudit.ch12 import EX

maJ, aJ = 1e-21, 1e-18


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


def test_geometry():
    assert close(EX.l_rod, 66e-9, 1e-9)
    assert close(EX.S_eff, 0.64e-18, 1e-9)
    assert close(EX.l_in, 32e-9, 1e-9)


def test_k_s_rod_4_85():
    assert close(ch12.k_s(EX, EX.l_rod), 4.85, 0.01)


def test_m_rod_two_formulas():
    """§12.3.3c quotes 1.9e-22 kg (Eq. 12.6); §12.3.4a quotes 1.94e-22 kg (Eq. 12.8). The two
    printed formulas differ in how knob mass is counted and give 1.85e-22 vs 1.94e-22."""
    assert close(ch12.m_rod_eq12_6(EX), 1.85e-22, 0.01)
    assert close(ch12.m_rod_eq12_8(EX), 1.94e-22, 0.01)


def test_f_accel_and_v_max():
    m = ch12.m_rod_eq12_8(EX)
    assert close(ch12.f_accel(EX, m), 0.096e-9, 0.01)
    assert close(ch12.v_max(EX), 15.7, 0.01)


def test_kinetic_energy_23_maJ():
    assert close(ch12.kinetic_energy(EX, ch12.m_rod_eq12_8(EX)), 23 * maJ, 0.05)


def test_v_sound_11_km_s():
    assert close(ch12.v_sound(EX), 11e3, 0.03)


def test_e_vib_0_56_maJ():
    assert close(ch12.e_vib(EX), 0.56 * maJ, 0.02)


def test_e_drag_0_052_maJ():
    assert close(ch12.e_drag(EX), 0.052 * maJ, 0.02)


def test_v_cam_38():
    assert close(ch12.v_cam(EX), 38, 0.02)


def test_e_cam_0_06_maJ():
    """§12.3.4d: ~0.012 maJ per 0.1 ns, ×5 duty -> ~0.06 maJ. Reconstructed by re-expressing
    Eq. 12.17 per area and mean-square speed; 5% tolerance."""
    assert close(ch12.e_cam(EX, duty_factor=1), 0.012 * maJ, 0.05)
    assert close(ch12.e_cam(EX), 0.06 * maJ, 0.05)


def test_e_therm_bound_0_41_maJ():
    assert close(ch12.e_therm_eq12_19(EX), 0.41 * maJ, 0.02)


def test_eq_12_19_coefficient_vs_eq_7_49():
    """The printed 8.2e-5 should be (1/2) T/C_vol = 8.8e-5 for one transition; ~7% low.
    Not a verdict: recorded as a spot check on 12.3.4/thermoelastic-bound-0.41maJ."""
    ratio = ch12.e_therm_eq12_19(EX) / ch12.e_therm_from_eq7_49(EX)
    assert 0.9 < ratio < 0.96


def test_switching_cycle_2_maJ():
    assert close(ch12.e_switching_cycle(EX), 2.0 * maJ, 0.1)


def test_e_state_1_2_aJ():
    assert close(ch12.e_state(EX), 1.2 * aJ, 0.02)


def test_q_implied_3770():
    """Prase's Q ≈ 3770 (loss 1/600 per cycle) from 2 maJ / 1.2 aJ; ±10%."""
    assert close(ch12.q_implied(EX), 3770, 0.10)


def test_error_model():
    assert close(ch12.sigma_el(EX), 0.023e-9, 0.02)
    assert close(ch12.dx_thresh(EX), 0.7e-9, 1e-9)
    p = ch12.p_err_disp(EX)
    # Book: 1.3e-67. Our 1.5e-67 differs by the value of kT and rounding of sigma; compare in log.
    assert abs(math.log10(p) - math.log10(1.3e-67)) < 0.2


def test_per_interlock_energy_typo_flag():
    """§12.3.8b prints '~0.013 maJ per interlock' and '~0.031 kT_300'. 2 maJ / 16 switching events
    = 0.125 maJ = 0.030 kT, matching the kT figure; the maJ figure is a typo for ~0.13."""
    per_interlock = ch12.e_switching_cycle(EX) / 16
    assert close(per_interlock / (ch12.K_B * 300), 0.031, 0.06)
    assert not close(per_interlock, 0.013 * maJ, 0.5)


def test_cpu_interlock_term_vs_12_3_8():
    """§12.7.4 uses 0.03 maJ per interlock-operation (30 aJ per clock for 1e6 interlocks); §12.3.8b's
    2 maJ per rod cycle × 1e5 rods is 200 aJ. Recorded as a discrepancy, not a verdict."""
    from_rods = 1e5 * ch12.e_switching_cycle(EX)
    assert close(from_rods, 200 * aJ, 0.1)
    assert from_rods / (1e6 * 0.03 * maJ) > 6


def test_cpu_power_74_aJ_60_nW():
    assert close(ch12.cpu_energy_per_clock(), 74 * aJ, 0.01)
    assert close(ch12.cpu_power(), 60e-9, 0.05)
