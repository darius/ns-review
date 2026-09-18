"""Reproduce the worked numbers of §7.2, 7.3, 7.5, 7.6 (§7.4 is in test_ch07.py)."""
import math
import pytest
from nsaudit import ch07


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


# ---- 7.2 --------------------------------------------------------------------------

def test_7_2_1_matrix_sound_speed_and_omega():
    """§7.2.1: matrix ~1/10 of mass -> v ~ (1/10)^{1/2} × diamond ≈ 5000 m/s; lambda=100 nm -> omega ≈ 3e11."""
    v = math.sqrt(0.1) * 1.8e4  # diamond longitudinal ~1.8e4 gives 5.7e3; the book says ~5000
    assert 4e3 < v < 7e3
    omega = 2 * math.pi * 5000 / 100e-9
    assert close(omega, 3e11, 0.1)


def test_7_2_2_diamond_speed_ratio():
    """§7.2.2: nu ≈ 0.1 -> v_l/v_t = sqrt(2(1-nu)/(1-2nu)) ≈ 1.5."""
    nu = 0.1
    ratio = math.sqrt(2 * (1 - nu) / (1 - 2 * nu))
    assert close(ratio, 1.5, 0.02)


def test_7_2_6_piston_limit_worked_example():
    """§7.2.6c: M=1e11, rho=2000, k=2e10 rad/m, A=0.05 nm -> ~4e6 W/m^2 at 1 m/s, ~4e2 at 1 cm/s."""
    p1 = ch07.p_rad_piston_limit_per_area(0.05e-9, 2e10 * 1.0, 1e11, 2000)
    p2 = ch07.p_rad_piston_limit_per_area(0.05e-9, 2e10 * 0.01, 1e11, 2000)
    assert close(p1, 4e6, 0.15)   # 3.5e6
    assert close(p2, 4e2, 0.15)


def test_7_2_6_soreff_probability():
    """§7.2.6d: v_s=1e4, v=1e2 -> ~1e-85. exp(-200) = 1.4e-87; 'on the order of' within 2 decades."""
    p = ch07.soreff_nonadiabatic_probability(1e4, 1e2)
    assert abs(math.log10(p) - (-85)) < 2.5


# ---- 7.3 --------------------------------------------------------------------------

def test_7_3_2_debye_wavevector_as_printed_matches_figure_caption():
    """Figure 7.3 caption: k_D = 1.24e10 rad/m for n = 100/nm^3. Reproduced by Eq. 7.29 as printed."""
    assert close(ch07.k_debye_book(1e29), 1.24e10, 0.01)


def test_7_3_2_debye_temperature_discrepancy_is_the_missing_pi():
    """§7.3.2 quotes T_D = 1570 K from Eqs. 7.29-7.31 for a diamond-like isotropic solid
    (v_s = 1.38e4, n = 176/nm^3) vs 2230 K measured (Gray 1972). With the standard
    k_D = (6 pi^2 n)^{1/3} the same inputs give ~2300 K. The 'discrepancy' the book reports
    against experiment is the factor pi^{1/3} = 1.46 missing from Eq. 7.29. Spot check, not verdict."""
    n, v = 1.76e29, 1.38e4
    t_book = ch07.debye_temperature(ch07.k_debye_book(n), v)
    t_std = ch07.debye_temperature(ch07.k_debye_standard(n), v)
    assert close(t_book, 1570, 0.02)
    assert close(t_std, 2230, 0.05)
    assert close(t_std / t_book, math.pi**(1 / 3), 1e-9)


def test_7_3_2_mean_speed_limit():
    """Eq. 7.31 maximum 1.084 v_t at E = 2G (v_l = v_t ... the book's stated limiting case)."""
    # At E=2G, nu=0 and v_l = sqrt(E/rho) = sqrt(2) v_t.
    vt = 1.0
    assert close(ch07.debye_mean_sound_speed(math.sqrt(2) * vt, vt), 1.084, 0.01)


def test_7_3_2_diamond_like_mean_speed():
    """§7.3.2: diamond-axis v_l, v_t give v_s = 1.38e4 m/s. Using v_l = 1.8e4, v_t = 1.2e4 (cubic-axis
    values consistent with nu ≈ 0.1) reproduces within a few percent."""
    assert close(ch07.debye_mean_sound_speed(1.8e4, 1.2e4), 1.38e4, 0.05)


def test_7_3_energy_density_2e8_is_the_book_working_value():
    """§7.3.4-7.3.6 use eps ≈ 2e8 J/m^3 with v_s = 1e4 and (Fig. 7.5) n = 100/nm^3 at 300 K.
    Eq. 7.28 with the PRINTED k_D (6 pi n)^{1/3} gives 1.05e8; with the standard (6 pi^2 n)^{1/3}
    it gives 1.73e8. The working value matches the standard cutoff, not the printed equation.
    (T/T_D is 0.2-0.3 here, so the cutoff is not negligible.) Spot check, not verdict."""
    e_book = ch07.debye_energy_density(1e4, 1e29, 300)
    e_std = ch07.debye_energy_density(1e4, 1e29, 300, k_D=ch07.k_debye_standard(1e29))
    assert close(e_book, 1.05e8, 0.03)
    assert close(e_std, 2e8, 0.15)
    assert 1.5 < e_std / e_book < 1.8


def test_7_3_4_sliding_contact_drag_worked_example():
    """§7.3.4: sigma ≈ 1e-20 m^2, v_s = 1e4, eps = 2e8 -> ~3e-16 W at 1 m/s, 3e-20 at 1 cm/s;
    3e-25 and 3e-27 J/nm."""
    p1 = ch07.p_drag_scattering(2e8, 1e-20, 1.0, 1e4)
    p2 = ch07.p_drag_scattering(2e8, 1e-20, 0.01, 1e4)
    assert close(p1, 3e-16, 0.15)   # 2.67e-16
    assert close(p2, 3e-20, 0.15)
    assert close(p1 / 1.0 * 1e-9, 3e-25, 0.15)


def test_7_3_5c_band_stiffness_worked_example():
    """§7.3.5c: T_trans = 1e-3, R = 10, dk/k = 0.1, v_s = 1e4, eps = 2e8 -> ~200 W/m^2 at 1 m/s,
    ~0.02 at 1 cm/s; 2e-25 J/nm^2 per nm of travel."""
    p1 = ch07.p_drag_band_stiffness_per_area(2e8, 1e-3, 0.1, 10, 1.0, 1e4)
    p2 = ch07.p_drag_band_stiffness_per_area(2e8, 1e-3, 0.1, 10, 0.01, 1e4)
    assert close(p1, 200, 0.2)   # 170
    assert close(p2, 0.02, 0.2)
    assert close(p1 * 1e-18 * 1e-9, 2e-25, 0.2)


def test_7_3_5d_band_flutter_worked_example():
    """§7.3.5d: A/d = 1e-2, other values as before -> ~10 W/m^2 at 1 m/s."""
    p = ch07.p_drag_band_flutter_per_area(2e8, 1e-3, 1e-2, 10, 1.0, 1e4)
    assert close(p, 10, 0.25)    # 7.9


def test_7_3_5e_fit_is_small_for_stiff_media():
    """§7.3.5c: 'values of T_trans can easily be less than 1e-3'. Eq. 7.41 at d_n = 100 atomic
    layers (M/k_a = 100 n^{-1/3}), T' = 0.2."""
    assert ch07.t_trans_fit(100, 0.2) < 1e-3
    assert ch07.t_trans_fit(10, 0.2) > 1e-3


def test_7_3_6_shear_reflection_worked_example():
    """§7.3.6: assumptions of 7.3.5c, D_sr = 1 -> ~10 W/m^2 at 1 m/s."""
    assert close(ch07.p_drag_shear_reflection_per_area(2e8, 1e-3, 1.0, 1e4), 10, 0.01)


# ---- 7.5 --------------------------------------------------------------------------

def test_7_5_1_square_well_worked_example():
    """§7.5.1c: m = 2e-25, ratio 10, alpha = 0.5, 300 K -> 1.6e-22 J at 1 m/s, 1.6e-24 at 1 cm/s."""
    w1 = ch07.dw_square_well_compression(2e-25, 300, 0.5, 10, 1.0)
    w2 = ch07.dw_square_well_compression(2e-25, 300, 0.5, 10, 0.01)
    assert close(w1, 1.6e-22, 0.03)
    assert close(w2, 1.6e-24, 0.03)


def test_7_5_2_k_s1_and_harmonic_worked_example():
    """§7.5.2b: m = 1e-24, rho_c = 2000 -> k_s1 ≈ 19 N/m; with T = 300, M = 5e11, rho = 2000,
    k_ext = 10 -> ΔW ≈ 2e-21 J at 1 m/s, 2e-23 at 1 cm/s; polymer surroundings (M = 3e9,
    rho = 1000) reduce by ~7e-4."""
    k1 = ch07.k_s1_nonbonded_contact(1e-24, 2000)
    assert close(k1, 19, 0.02)
    w = ch07.dw_harmonic_well_compression(300, 1e-24, 5e11, 2000, 10, 1.0, 19)
    assert close(w, 2e-21, 0.15)   # 1.75e-21
    w_poly = ch07.dw_harmonic_well_compression(300, 1e-24, 3e9, 1000, 10, 1.0, 19)
    assert close(w_poly / w, 7e-4, 0.1)


# ---- 7.6 --------------------------------------------------------------------------

def test_7_6_3_ln2_kT():
    assert close(ch07.f_diss_symmetric_merge(300), 2.87e-21, 0.01)
