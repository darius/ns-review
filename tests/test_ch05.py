"""Reproduce Ch. 5's stated identities, approximation accuracies, and the claims Ch. 9/12 import."""
import math
import pytest
from nsaudit import ch05
from nsaudit.ch05 import K_B, HBAR


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


# ---- 5.3 -------------------------------------------------------------------------------------

def test_quantum_ratio_limits():
    """Eq. 5.18: ratio -> 1 for kT >> hbar omega; -> hbar omega / 2kT for kT << hbar omega."""
    assert close(ch05.quantum_to_classical_ratio(1.0, 1e-20, 300), 1.0, 1e-3)      # omega = 1e10
    k, m, T = 400.0, 1.66e-27, 1.0                                                   # bond-stretch, H atom, 1 K
    omega = math.sqrt(k / m)
    assert close(ch05.quantum_to_classical_ratio(k, m, T), HBAR * omega / (2 * K_B * T), 1e-6)


def test_12_3_7_knob_is_classical_but_a_single_atom_is_not():
    """12.3.7b invokes Section 5.3 to treat positional variance classically. For the exemplar
    rod mass (1.9e-22 kg) at 40 N/m, hbar omega / kT = 0.011: classical to 1e-4. For a single
    carbon atom at 40 N/m, hbar omega / kT = 1.1 and the variance is 11% above classical: the
    classical license holds for the rod, and is a 10% question for single-atom contacts."""
    assert close(ch05.quantum_to_classical_ratio(40.0, 1.9e-22, 300), 1.0, 1e-3)
    r_atom = ch05.quantum_to_classical_ratio(40.0, 12 * 1.66e-27, 300)
    assert 1.08 < r_atom < 1.15


# ---- 5.4 -------------------------------------------------------------------------------------

def test_modal_sum_identity_5_25():
    assert close(sum(1 / (2 * n + 1)**2 for n in range(200000)), math.pi**2 / 8, 1e-5)


def test_eq_5_22_modal_stiffnesses_sum_to_rod_variance():
    """sum_n kT/k_n = kT l / E_l (Eq. 5.26) — the modal decomposition reproduces the whole-rod stiffness."""
    T, l, E_l = 300, 10e-9, 1e12 * 1e-18
    v = sum(K_B * T / ch05.rod_modal_stiffness(n, l, E_l) for n in range(20000))
    assert close(v, ch05.var_rod_longitudinal_classical(T, l, E_l), 1e-4)


@pytest.mark.parametrize("l", [1e-9, 3e-9, 10e-9, 30e-9])
def test_5_44_within_few_percent_and_conservative(l):
    """§5.4.2d: Eq. 5.44 'within a few percent of the correct values' and conservative; Eq. 5.43
    conservative but 'can amount to tens of percent' near kT/hbar omega_0 ~ 1. Diamond-like rod of
    1 nm^2 cross-section (E_l = 1e-6 N, rho_l = 3.5e-15 kg/m), 300 K, N = 1e10 l."""
    E_l, rho_l, T = 1e12 * 1e-18, 3500 * 1e-18, 300
    N = ch05.n_planes(l)
    exact = ch05.var_rod_exact(l, E_l, rho_l, T, N)
    a44 = ch05.var_rod_approx_5_44(l, E_l, rho_l, T, N)
    a43 = ch05.var_rod_approx_5_43(l, E_l, rho_l, T, N)
    assert a44 >= exact * 0.99
    assert a44 <= exact * 1.06
    assert a43 >= exact * 0.99


def test_fig_5_8_quantum_major_only_below_1nm():
    """Fig. 5.8 caption: for diamond-like rods at 300 K, 'quantum effects make a major contribution to
    the positional uncertainty only for l <= 1 nm'. Ratio exact/classical for a 1 nm^2 rod."""
    E_l, rho_l, T = 1e12 * 1e-18, 3500 * 1e-18, 300
    def ratio(l):
        N = ch05.n_planes(l)
        return ch05.var_rod_exact(l, E_l, rho_l, T, N) / ch05.var_rod_longitudinal_classical(T, l, E_l)
    # exact/classical: 1.13 at 1 nm, falling to ~1.02 at 10 nm ("major" is generous at 13%)
    r1, r3, r10 = ratio(1e-9), ratio(3e-9), ratio(10e-9)
    assert 1.1 < r1 < 1.2
    assert r3 < r1 and r10 < r3
    assert r10 < 1.05


# ---- 5.5 -------------------------------------------------------------------------------------

def test_cantilever_roots_and_identities():
    R = ch05.cantilever_roots(12)
    assert close(R[0], 1.8751, 1e-3)
    assert close(sum(1 / r**4 for r in R) + sum(1 / ((n + 0.5) * math.pi)**4 for n in range(12, 100000)), 1 / 12, 1e-3)   # Eq. 5.52
    s = sum(2 / r**2 for r in R) + sum(2 / ((n + 0.5) * math.pi)**2 for n in range(12, 100000))
    assert close(s, 0.7588, 2e-3)                                                                                          # Eq. 5.63
    assert close(2 / R[0]**2, 0.5688, 1e-3)


def test_eq_5_58_approximation_accuracy():
    """Exact for N = 1, 2 and infinity; otherwise high by < 1%."""
    for N in (1, 2):
        assert close(ch05.discrete_bending_factor_approx(N), ch05.discrete_bending_factor_exact(N), 1e-9)
    assert close(ch05.discrete_bending_factor_approx(10**6), 1 / 3, 1e-5)
    for N in range(3, 60):
        a, e = ch05.discrete_bending_factor_approx(N), ch05.discrete_bending_factor_exact(N)
        assert e <= a <= e * 1.01, N


def test_eq_5_70_bound():
    for r in (1e-3, 0.1, 1, 10, 1e3):
        v = ch05.two_source_overestimate(r, 1.0)
        assert 1 <= v <= math.sqrt(2) + 1e-12
    assert close(ch05.two_source_overestimate(1.0, 1.0), math.sqrt(2), 1e-12)


def test_eq_5_65_vs_5_64_never_low_at_large_N():
    """§5.5.3: Eq. 5.65 'is always high, but never by more than 1%' vs the N -> inf sum (Eq. 5.60);
    here we check it against the classical limit it must approach for a stiff nm rod."""
    T, l, rho_l = 300, 20e-9, 3500 * 1e-18
    k_b = ch05.k_b_tube(1e12, 0, 0.5e-9)
    v65 = ch05.var_transverse_bending_5_65(T, l, k_b, rho_l)
    vcl = ch05.var_cantilever_bending_classical(T, l, k_b)
    assert 1.0 <= v65 / vcl < 1.1


# ---- 5.6, 5.7 --------------------------------------------------------------------------------

def test_piston_erlang_moments():
    mean, var = ch05.piston_mean_and_variance(10, 300, 1e-10)
    a = K_B * 300 / 1e-10
    assert close(mean, 11 * a, 1e-12) and close(var, 11 * a * a, 1e-12)


def test_eq_5_98_zeta_4():
    assert close(sum(1 / n**4 for n in range(1, 10000)), 1.082, 1e-3)
