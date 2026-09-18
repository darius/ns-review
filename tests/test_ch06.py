"""Reproduce Ch. 6's worked numbers and thresholds."""
import math
import pytest
from nsaudit import ch06
from nsaudit.ch06 import K_B, MAJ, AJ, YEAR

AMU = 1.66053907e-27


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


def test_tst_prefactor_300K():
    assert close(ch06.tst_prefactor(300), 6.25e12, 0.01)


def test_6_7_1_barrier_thresholds():
    """1e-20 /s per bond needs dV > 313 maJ at 300 K, 366 at 350 K (q_long = 1); a 1% population
    may run at 1e-18 /s: 294 and 344 maJ."""
    assert close(ch06.barrier_for_rate(300, 1e-20), 313 * MAJ, 0.005)
    assert close(ch06.barrier_for_rate(350, 1e-20), 366 * MAJ, 0.005)
    assert close(ch06.barrier_for_rate(300, 1e-18), 294 * MAJ, 0.005)
    assert close(ch06.barrier_for_rate(350, 1e-18), 344 * MAJ, 0.005)


def test_6_7_1_common_bonds_below_1e_33():
    """C-{H,N,O,F,Si,P,S,Cl} 'all ... yield cleavage rates below 1e-33 /s' with Table 3.8 D_0.
    The weakest, C-P (439 maJ), gives 5e-34: just inside the claim."""
    for name, D0 in [("C-H", 642), ("C-N", 498), ("C-O", 564), ("C-F", 876), ("C-Si", 616),
                     ("C-P", 439), ("C-S", 532), ("C-Cl", 583)]:
        assert ch06.k_cleave_thermal(300, D0 * MAJ) < 1e-33, name
    assert 1e-34 < ch06.k_cleave_thermal(300, 439 * MAJ) < 1e-33
    assert ch06.k_cleave_thermal(300, 259 * MAJ) > 1e-20        # O-O peroxide falls short (6.4.3a)


def test_6_4_4_cc_allowable_stress_1_2_nN():
    """Fig. 6.11: tau_cl > 1e20 s for C-C at 300 K iff F <= ~1.2 nN; barrier vanishes at
    beta D_e / 2 = 5.5 nN. Quantum 1-D TST of §6.4.4a with Table 3.8 (D_e 0.556 aJ, beta 1.989e10)."""
    D_e, beta, mu = 0.556 * AJ, 1.989e10, 6 * AMU
    assert close(ch06.critical_force(D_e, beta), 5.5e-9, 0.02)
    F = ch06.force_for_lifetime(300, D_e, beta, mu, 1e20)
    assert close(F, 1.2e-9, 0.15)


def test_6_4_4_bond_pair_threshold_6_nN():
    """'Replacing each stressed C-C bond by a pair (doubling the mass, energy, and stiffness)
    ... threshold stress ~6 nN, substantially more than twice the single-bond threshold.'"""
    D_e, beta, mu = 2 * 0.556 * AJ, math.sqrt(2 * 440 / (2 * 2 * 0.556 * AJ)), 12 * AMU
    F2 = ch06.force_for_lifetime(300, D_e, beta, mu, 1e20)
    assert close(F2, 6e-9, 0.2)
    assert F2 > 2 * 1.2e-9 * 1.3


def test_6_4_4_lawn_strength_per_bond():
    assert close(1.9e11 / 1.8e19, 10.6e-9, 0.01)
    assert close(1.2e11 / 1.8e19, 6.7e-9, 0.01)


def test_6_4_5_ion_separation_energies():
    assert close(ch06.ion_pair_separation_energy(0.3e-9, 3e-9), 700 * MAJ, 0.02)
    assert close(ch06.ion_pair_separation_energy(0.3e-9, 3e-9, 78.5), 9 * MAJ, 0.03)


def test_6_4_5_pyrolysis_scaling():
    """>= 1 s for thorough pyrolysis at 750 K -> tau >= 1e20 s at 300 K; 50% loss in 30 min at
    610 K -> <= 1e-20 /s per monomer at 300 K."""
    assert ch06.rate_at_T2_from_T1(1.0, 750, 300) < 1e-20
    assert ch06.rate_at_T2_from_T1(math.log(2) / 1800, 610, 300) < 1e-20
    assert ch06.rate_at_T2_from_T1(1.0, 740, 300) > 1e-20      # the 750 K figure is close to the edge


def test_6_4_5_diamond_1800K_gives_1e85():
    """'Diamond itself is stable to 1800 K ... (tau > 1e85 s at 300 K)'. Scaling with Eq. 6.28:
    a 1800 K rate of 1 /s gives 1e68 s at 300 K; the printed 1e85 requires ~2e-3 /s at 1800 K
    (minutes-scale stability), which is what 'stable' must mean here. Not a discrepancy, but the
    unstated input."""
    assert 1e67 < 1 / ch06.rate_at_T2_from_T1(1.0, 1800, 300) < 1e69
    assert 1e84 < 1 / ch06.rate_at_T2_from_T1(2e-3, 1800, 300) < 1e86


def test_6_4_7_and_6_5_thresholds():
    assert close(ch06.photon_wavelength_for_energy(0.864 * AJ), 230e-9, 0.01)
    assert close(ch06.H_PLANCK * ch06.C_LIGHT / 400e-9, 0.50 * AJ, 0.01)      # Table 6.2


def test_6_5_4_shield_thickness_250nm():
    """1e-12 m^2 × 1e9 s × 1e19 photons/m^2 s = 1e16 photons; q.e. 1e-2 -> T <= 1e-14; Eq. 6.52 at
    320 nm (worst k among UV-A/B) gives 'just under 250 nm'."""
    flux = 5.0 / (0.5 * AJ)
    assert close(flux, 1e19, 0.05)
    dose = flux * 1e-12 * 1e9
    assert close(dose, 1e16, 0.05)
    d = ch06.al_thickness_for_transmittance(1e-14, 320e-9)
    assert 220e-9 < d < 250e-9


def test_6_6_2_hits_per_kg_rad_and_background():
    assert close(ch06.hits_per_kg_rad(), 1e15, 0.06)
    assert close(1e15 * 0.5 / YEAR, 1.5e7, 0.06)


def test_6_7_1_bond_rate_criterion_vs_radiation():
    """1e-20 /bond s × ~1e26 bonds/kg (diamond: 2 × 1.76e29 / 3500) = 1e6 /kg s, an order of
    magnitude below 1.5e7 hits/kg s."""
    bonds_per_kg = 2 * 1.76e29 / 3500
    assert 1e25 < bonds_per_kg < 2e26
    assert 5 < 1.5e7 / (bonds_per_kg * 1e-20) < 20


def test_6_7_2_redundancy_examples():
    D, m = 1.0, 1e-16          # 1e15 D m = 0.1
    assert close(ch06.p_functional(D, m), math.exp(-0.1), 1e-9)
    assert abs(math.log10(ch06.p_system_redundant(D, m, 1, 1000)) - (-44)) < 0.7    # 3.7e-44
    assert close(ch06.p_system_redundant(D, m, 5, 1000), 0.992, 0.002)
    assert 1 - ch06.p_system_redundant(D, m, 10, 1000) < 1e-7
    assert 1 - ch06.p_system_redundant_approx(D, m, 25, 4e19) < 2e-6      # 1000 kg system
    assert close(0.1 / 1e15 / 1e-18 / 0.5, 200, 0.01)                     # 1e-18 kg: 0.1 after 200 y


def test_6_3_3_t_crit_coefficient():
    """Eq. 6.24 as printed: 0.2332 d^2/A. First-barrier condition on Eq. 6.21 gives 0.1166 k_s d^2 / A."""
    k_s, d, A = 1.0, 1.0, 1.0
    assert close(ch06.t_crit_first_barrier(k_s, d, A), 0.1166, 0.01)
    assert close(2 * ch06.t_crit_first_barrier(k_s, d, A), 0.2332, 0.01)


def test_6_3_3_error_models_order():
    """Instantaneous onset >= total equilibrium error probability (6.3.3c: 'maximizes error rates')."""
    for a in (2.0, 4.0, 8.0):        # d_err / sigma
        T, k_s = 300, 10.0
        d = a * math.sqrt(K_B * T / k_s)
        assert ch06.p_err_instantaneous(T, k_s, d) >= ch06.p_err_total_equilibrium(T, k_s, d)
