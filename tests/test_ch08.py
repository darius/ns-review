"""Chapter 8 (partial): reproduce §8.3.3-8.3.4 and §8.5 numbers from their stated inputs."""
import math

from nsaudit import ch06, ch08
from nsaudit.ch08 import MAJ


def close(a, b, tol):
    return abs(a - b) <= tol * abs(b)


def test_effective_concentration_2e4():
    """§8.3.3a: Eq. 6.5 at 20 N/m in three dimensions -> ~2e4 nm^-3."""
    assert close(ch08.effective_concentration() * 1e-27, 2e4, 0.1)


def test_electrostatic_and_piezochemical_scales():
    """§8.3.3b-c: 2.5e-29 C·m × 2e9 V/m = 50 maJ (> 1e5); 110 maJ > 1e10; 2 GPa × -0.02 nm^3
    -> 1.6e4; 550 GPa -> >= 30 nN/bond, 50 GPa ~3 nN; 50 GPa × 0.01 nm^3 and 5 nN × 0.1 nm
    both 500 maJ; Eq. 8.9-8.10 -> ~4 nN."""
    assert close(ch08.dipole_field_energy(), 50 * MAJ, 1e-9)
    assert math.exp(50 * MAJ / ch08.KT) > 1e5
    assert math.exp(110 * MAJ / ch08.KT) > 1e10
    assert close(ch08.piezo_rate_factor(2e9, -0.02e-27), 1.6e4, 0.03)
    assert ch08.per_bond_load(550e9) >= 30e-9
    assert close(ch08.per_bond_load(50e9), 3e-9, 0.1)
    assert close(50e9 * 0.01e-27, 500 * MAJ, 1e-9)
    assert close(ch08.instability_load_limit(), 4e-9, 1e-9)


def test_diffusive_yield():
    """§8.3.3f: 95% per step -> ~0.6% after 100 steps, ~1e-43 % after 2000."""
    assert close(ch08.yield_after_steps(0.95, 100), 0.006, 0.02)
    assert ch08.yield_after_steps(0.95, 2000) < 1e-44


def test_misreaction_elastic_criterion_brackets():
    """§8.3.3f: 180 maJ at 20 N/m needs d_t >= 0.135 nm; 30 N/m, 0.15 nm is 338 maJ (book
    P_err <= 1e-27). The 180 maJ -> 1e-15 value is read from the worst-case decoupling curve
    (Fig. 6.8); it lies between Ch. 6's two computable limits (equilibrium 1.6e-19,
    instantaneous-onset 2.7e-6), as the worst-case model should."""
    assert close(ch08.elastic_energy(20, 0.135e-9), 180 * MAJ, 0.02)
    assert ch06.p_err_total_equilibrium(300, 20, 0.135e-9) < 1e-15 < ch06.p_err_instantaneous(300, 20, 0.135e-9)
    assert ch06.p_err_total_equilibrium(300, 30, 0.15e-9) < 1e-27 < ch06.p_err_instantaneous(300, 30, 0.15e-9)


def test_single_trial_barrier_33maj():
    """Eq. 8.11: t = 1e-7 s, f_TST = 1e12, P_err = 1e-15 -> 33 maJ; t >= 35/k."""
    assert close(ch08.max_barrier_single_trial(), 33 * MAJ, 0.01)
    assert close(-math.log(1e-15), 35, 0.02)


def test_speedup_70maj():
    """§8.3.4e: 1e3 s -> 1e-7 s with t >= 35/k is ~3e11; /3e4 from concentration leaves 1e7,
    ~70 maJ (67)."""
    assert close(35 * 1e3 / 1e-7, 3e11, 0.2)
    assert close(ch08.energy_for_ratio(1e7), 70 * MAJ, 0.05)


def test_conditional_repetition_examples():
    """§8.3.4f: ΔF = 0 -> 0.5 per trial, 50 trials, mean 2; -25 maJ -> 0.9976, 6 trials, 1.002."""
    p, n, mean = ch08.trials_needed(0.0)
    assert p == 0.5 and n == 50 and mean == 2.0
    p, n, mean = ch08.trials_needed(-25 * MAJ)
    assert close(p, 0.9976, 1e-4) and n == 6 and close(mean, 1.002, 1e-3)


def test_reagent_stability_230_and_275():
    """§8.3.4g: 1e-4 s between reactions, f <= 1e13 -> >= 230 maJ; 275 maJ -> ~1e-20 per
    reaction; 1e4 moieties MTTF ~1e4 years (2e4 computed)."""
    assert close(ch08.stability_barrier(), 230 * MAJ, 0.01)
    assert close(ch08.instability_rate(275 * MAJ), 1e-20, 0.5)
    mttf_years = 1e-4 / (ch08.instability_rate(275 * MAJ) * 1e4) / ch06.YEAR
    assert 1e4 < mttf_years < 3e4


def test_equal_well_barrier_38maj():
    """§8.5.3b: 1e9 /s transitions at f = 1e13 need barriers <= 38 maJ."""
    assert close(ch08.barrier_for_rate(), 38 * MAJ, 0.01)


def test_cleavage_stiffness_margin():
    """§8.5.3d: 153 × 1.05 × 1.14 ≈ 183 N/m; k_struct ≈ 90 N/m; 1.5× the 60 N/m C-C
    requirement (Fig. 8.8, not reproducible from the text)."""
    assert close(ch08.k_sz_estimate(), 183, 0.01)
    assert close(ch08.k_struct(ch08.k_sz_estimate()), 90, 0.02)
    assert close(ch08.k_struct(ch08.k_sz_estimate()) / 60, 1.5, 0.02)


def test_abstraction_barrier_timescale():
    """§8.5.4a: 29 maJ at f = 1e13 gives P_omit <= 1e-15 in ~4e-9 s; 2 kT = 8.3 maJ."""
    t = -math.log(1e-15) / (1e13 * math.exp(-29 * MAJ / ch08.KT))
    assert close(t, 4e-9, 0.1)


def test_abstract_donate_exoergicity():
    """Spot check, not a verdict: §8.5.4c-d bounds (alkynyl 915 maJ, donors <= 530) make a
    single-step abstraction-donation pair exoergic by >= 385 maJ per H moved, dissipated
    unless recovered by the 8.5.2b route."""
    assert close(ch08.abstract_donate_exoergicity(), 385 * MAJ, 1e-9)


def test_radical_addition_stiffness():
    """§8.5.5a: 12 N/m at 0.177 nm -> > 180 maJ; 6 N/m with 0.1 nm bias -> ~200 maJ
    difference while raising the favoured TS by 30 maJ (book: 25)."""
    assert ch08.elastic_energy(12, 0.177e-9) > 180 * MAJ
    fav, diff = ch08.radical_addition_bias()
    assert close(diff, 200 * MAJ, 0.01)
    assert close(fav, 30 * MAJ, 1e-9)


def test_torsion_cycle_and_trans_effect():
    """§8.5.6: 410-440 maJ weakening less 2 × 145 -> >= 120 maJ; §8.5.10c: 1e4 -> ~40 maJ."""
    assert close(ch08.torsion_cycle_gain(), 120 * MAJ, 1e-9)
    assert close(ch08.energy_for_ratio(1e4), 40 * MAJ, 0.05)
