"""Reproduce the worked numbers of Ch. 3 and the values Ch. 7/9/10 read off its figures."""
import math
import pytest
from nsaudit import ch03
from nsaudit.ch03 import MAJ, AJ, AMU


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


# ---- 3.3.2 ----------------------------------------------------------------------------------

def test_k_perp_ccc_19_4():
    assert close(ch03.k_perp_from_bend(0.450 * AJ, 1.523e-10), 19.4, 0.01)
    assert close(19.4 / 440, 1 / 20, 0.15)


def test_torsional_stiffness_0_36():
    k = ch03.torsional_stiffness_at_anti(1.39 * MAJ, 1.88 * MAJ, 0.65 * MAJ, 1.523e-10, math.radians(109.47))
    assert close(k, 0.36, 0.03)
    assert close(k / 19.4, 1 / 50, 0.1)


def test_cf_partial_charge():
    assert close(ch03.dipole_partial_charge(4.7e-30, 1.392e-10), 0.2, 0.06)


def test_exp6_minimum_and_constants():
    eps, r0 = ch03.pair_params("C1", "C1")
    assert close(ch03.v_vdw(r0, eps, r0), -eps, 0.01)          # "minimum of -eps at r = r_vdw0"
    assert abs(ch03.f_vdw(r0, eps, r0)) < 2e-2 * eps / r0        # ~zero force at the minimum (rounded constants)
    assert close(2.48e5 * 12.5, 3.1e6, 0.01)                    # Eq. 3.16
    assert close(1.924 * 6, 11.54, 0.001)
    assert close(2.48e5 * 12.5**2, 3.88e7, 0.01)                # Eq. 3.17
    assert close(1.924 * 42, 80.81, 0.001)


def test_exp6_breakdown_radius_is_the_stiffness_zero():
    """§3.3.3b: 'below 0.323 r_vdw0 the exponential repulsion is overwhelmed by a nonphysical
    extension of the r^-6 attraction.' Numerically 0.323 r_vdw0 is where the MM2 stiffness
    (Eq. 3.17) crosses zero, i.e. the repulsive force peaks; the force itself does not reverse
    until ~0.275 r_vdw0 and the energy until ~0.22 r_vdw0."""
    eps, r0 = ch03.pair_params("C1", "C1")
    rb = ch03.r_breakdown(r0)
    assert ch03.k_vdw(0.98 * rb, eps, r0) < 0 < ch03.k_vdw(1.02 * rb, eps, r0)
    assert ch03.f_vdw(rb, eps, r0) > 0


# ---- 3.3.3 ----------------------------------------------------------------------------------

def test_eq_3_18_3_19_constants():
    assert close(ch03.k_over_f_strong_repulsion(0.36e-9), 3.5e10, 0.01)
    assert close(ch03.v_over_f_strong_repulsion(0.36e-9), 2.9e-11, 0.01)


def test_eq_3_18_holds_in_strong_repulsion():
    """At 1 nN on a C|C contact, k/F is within ~15% of 12.5/r_vdw0 (attraction still ~ -10%)."""
    eps, r0 = ch03.pair_params("C1", "C1")
    r = ch03.r_at_force(1e-9, eps, r0)
    ratio = ch03.k_vdw(r, eps, r0) / ch03.f_vdw(r, eps, r0)
    assert close(ratio, 12.5 / r0, 0.15)


def test_loaded_radius_matches_mm2_within_4pct():
    """Eq. 3.20 vs the exact MM2 separation at 0.1, 1 and 5 nN for C|C, C|H, H|H, N|N."""
    for a, b in [("C1", "C1"), ("C1", "H5"), ("H5", "H5"), ("N8", "N8")]:
        eps, r0 = ch03.pair_params(a, b)
        for F in (0.1e-9, 1e-9, 5e-9):
            exact = ch03.r_at_force(F, eps, r0)
            approx = ch03.r_loaded(F, *ch03.VDW[a]) + ch03.r_loaded(F, *ch03.VDW[b])
            assert close(approx, exact, 0.04), (a, b, F, approx, exact)


def test_radius_0_1_nN_convention_gives_delta_surf():
    """9.4.2 uses summable 0.1 nN radii (3.3.3b). For sp3 carbon Eq. 3.20 gives 0.150 nm, and
    0.150 - 0.077 (covalent radius) = 0.073 nm: this is 9.4.2's delta_surf ~0.07 nm."""
    r = ch03.r_loaded(0.1e-9, *ch03.VDW["C1"])
    assert close(r, 0.150e-9, 0.02)
    assert close(r - 0.077e-9, 0.07e-9, 0.1)


def test_morse_cc():
    k, r0, D0, De = ch03.BONDS["C-C"]
    beta = ch03.morse_beta(k, De)
    assert close(beta, 1.989e10, 0.005)
    assert close(ch03.zero_point_correction(k, 12 * AMU, 12 * AMU), De - D0, 0.1)   # 0.011 aJ
    assert close(De / D0, 1.02, 0.005)
    assert close(ch03.morse_inflection(r0, beta), 0.187e-9, 0.005)
    r_neg = ch03.morse_most_negative_stiffness_point(r0, beta)
    assert close(ch03.k_morse(r_neg, De, beta, r0), -0.125 * k, 0.01)
    assert close(ch03.k_morse(r0, De, beta, r0), k, 1e-9)


def test_table_3_8_betas():
    for name, (k, r0, D0, De) in ch03.BONDS.items():
        pass
    assert close(ch03.morse_beta(560, 0.417 * AJ), 2.592e10, 0.005)     # N-N
    assert close(ch03.morse_beta(185, 0.559 * AJ), 1.286e10, 0.005)     # Si-Si


# ---- 3.5.1 ----------------------------------------------------------------------------------

def test_hamaker_lifshitz_table_3_9():
    assert close(ch03.hamaker_lifshitz(2.40, 5.5), 340 * MAJ, 0.02)     # diamond
    assert close(ch03.hamaker_lifshitz(1.52, 2.3), 76 * MAJ, 0.05)      # polyethylene
    assert close(ch03.hamaker_lifshitz(1.33, 78.5), 37 * MAJ, 0.05)     # water
    assert close(ch03.hamaker_lifshitz(1.35, 2.1), 38 * MAJ, 0.05)      # PTFE


def test_hamaker_pairwise_mm2_vs_lifshitz():
    """Not a book number: Eq. 3.29 with MM2 sp3-carbon C and diamond density gives ~2x the
    Lifshitz value of Table 3.9. Recorded for the 9.7 audit (which convention 9.7.1 used)."""
    eps, r0 = ch03.pair_params("C1", "C1")
    A = ch03.hamaker_pairwise(ch03.dispersion_C(eps, r0), 1.76e29, 1.76e29)
    assert 1.5 < A / (340 * MAJ) < 2.5


def test_fig_3_10_worked_examples():
    A, s = 400 * MAJ, 0.2e-9
    assert close(ch03.f_sphere_sphere(A, 1e-9, 1e-9, s), 0.83e-9, 0.01)
    assert close(ch03.p_plane_plane(A, s), 2.7e9, 0.02)
    assert close(ch03.p_plane_plane(A, 2 * s), 3.3e8, 0.02)
    assert close(2.7e9 / 50e9, 1 / 20, 0.1)                            # "~1/20 the tensile strength of diamond"


# ---- 3.5.2 Fig. 3.12 -> 9.7.1 and 10.4.5 -------------------------------------------------------

def summary(k):
    S = ch03.FIG_3_12[k]
    return ch03.interface_summary(ch03.surface_curve(S, S))


def test_fig_3_12_which_curve_9_7_1_read():
    """9.7.1 reads off Fig. 3.12: tensile strength ~1 GPa, stiffness per area > 30 N/m·nm^2
    (3e19 N/m^3), compliance of a ~30 nm diamond slab; 10.4.5: at k_a ≈ 0 the tension 'can be
    ~1 GPa'. Reconstructing Eqs. 3.33-3.38 (continuum surface d_g behind each plane):
    curve a (n_a = 0.9e19): 0.45 GPa, 22 N/m·nm^2 — does NOT match;
    curve c (n_a = 1.8e19 ≈ diamond (111)): 0.81 GPa, 41 N/m·nm^2 — matches;
    curve e (Si-terminated): 1.13 GPa, 50. So 9.7.1's 'simple complementary vdW contact' is a
    full-density carbon surface layer, curve c or e, not the sparse layer of curve a."""
    a, c, e = summary("a"), summary("c"), summary("e")
    assert close(a["tensile_max"], 0.45e9, 0.05) and close(a["k_a_eq"], 2.2e19, 0.05)
    assert 0.7e9 < c["tensile_max"] < 1.3e9 and c["k_a_eq"] > 3e19
    assert 0.9e9 < e["tensile_max"] < 1.5e9 and e["k_a_eq"] > 3e19
    assert close(1.05e12 / c["k_a_eq"], 26e-9, 0.05)        # "compliance equal to a ~30 nm slab"


def test_fig_3_12_equilibrium_separation_is_sub_vdw():
    """§3.3.2e: equilibrium separations between surfaces are smaller than the pairwise r_vdw0
    (0.38 nm for C|C) because many atoms contribute to attraction."""
    for k in "abcd":
        assert summary(k)["s_eq"] < 0.38e-9
