"""Chapter 13: reproduce the published numbers of §13.2–13.4 from their stated inputs."""
from nsaudit import ch13
from nsaudit.ch13 import MAJ


def close(a, b, tol):
    return abs(a - b) <= tol * abs(b)


# ---- 13.2 sorting ----

def test_concentration_work_20maj():
    """§13.2.1a: ~20 maJ per molecule for concentration from 1e-2."""
    assert close(ch13.concentration_work(), 20 * MAJ, 0.1)


def test_rotor_drag_0_1_maj_per_receptor():
    """§13.2.1e: 0.0027 m/s rim, ~1e-16 W, ~0.1 maJ per receptor at 1e6 /s."""
    assert close(ch13.rim_speed(), 0.0027, 1e-9)
    assert close(ch13.rotor_viscous_drag(), 1e-16, 0.4)
    assert close(ch13.rotor_viscous_drag() / 1e6, 0.1 * MAJ, 0.4)


def test_discrimination_factors():
    """§13.2.1c: 24 maJ -> ~0.003; 45 maJ -> ~5e4."""
    assert close(ch13.boltzmann_factor(24 * MAJ), 0.003, 0.05)
    assert close(1 / ch13.boltzmann_factor(45 * MAJ), 5e4, 0.1)


def test_cascade_R_printed_as_reciprocal():
    """§13.2.2b prints 'R >= ~5e3' with f_rat = 0.1; Eq. 13.5 with the 45 maJ factor gives
    R ~2e-4, i.e. 1/R ~5e3. The printed inequality is the reciprocal (spot check)."""
    R = ch13.cascade_R(0.1, 1 / ch13.boltzmann_factor(45 * MAJ))
    assert R < 1 and close(1 / R, 5e3, 0.1)


def test_cascade_five_stages():
    """§13.2.2b: impurity 0.99 -> 1e-15 at R = 1e-3 needs N <= 5."""
    assert ch13.cascade_stages(0.99, 1e-15, 1e-3) == 5


def test_binding_energy_143_161():
    """§13.2.3b: 143 maJ for P_empty <= 1e-15; with 6e-23 J/K, ΔV ≈ -161 maJ."""
    assert close(ch13.energy_for_probability(1e-15), 143 * MAJ, 0.01)
    assert close(ch13.binding_potential_energy(), 161 * MAJ, 0.01)


def test_ethyne_pressure_1_3_gpa():
    """§13.2.3b: ethyne ~5e-29 m^3/molecule at pressure; 64 maJ needs ~1.3 GPa."""
    v = ch13.molecular_volume(621, 26.04e-3)
    assert close(v, 5e-29, 0.1)
    assert close(ch13.pressure_for_increment(64 * MAJ, v), 1.3e9, 0.1)


# ---- 13.3 mills ----

def test_eq_13_7_reaction_time():
    """Eq. 13.7: v = 0.005 m/s, r = 10 nm, δ = 0.01 nm -> 1.8e-7 s (both forms)."""
    assert close(ch13.t_trans_exact(0.005, 10e-9, 10e-9, 0.01e-9), 1.8e-7, 0.01)
    assert close(ch13.t_trans_approx(0.005, 10e-9, 10e-9, 0.01e-9), 1.8e-7, 0.01)


def test_mechanism_totals():
    """§13.3.5: roller pair ~310 nm^3; close-packed ~2300 nm^3, 5.7e-21 kg, 2.9e5 atoms;
    sparse ~800 nm^3, 2.0e-21 kg, 1.0e5 atoms."""
    assert close(ch13.roller_pair_volume(), 310e-27, 0.02)
    assert close(ch13.mechanism_volume(True), 2300e-27, 0.03)
    assert close(ch13.mechanism_mass(True), 5.7e-21, 0.04)
    assert close(ch13.mechanism_atoms(True), 2.9e5, 0.02)
    assert close(ch13.mechanism_volume(False), 800e-27, 0.01)
    assert close(ch13.mechanism_mass(False), 2.0e-21, 0.01)
    assert close(ch13.mechanism_atoms(False), 1.0e5, 0.01)


def test_processing_system_own_mass_3s():
    """§13.3.5d: 10 encounters, 5.7e-20 kg, own mass in ~3 s at 1e6 one-carbon moieties/s."""
    assert close(ch13.self_mass_time(10 * ch13.mechanism_mass(True)), 3.0, 0.05)


def test_fail_stop_unit_mass():
    """§13.3.6c: 2e-18 kg -> P_fail ~0.01 in 10 years at 0.5 rad/yr; ~350 mechanisms."""
    assert close(ch13.p_unit_fail_10yr(2e-18), 0.01, 0.01)
    assert close(2e-18 / ch13.mechanism_mass(True), 350, 0.05)


def test_roller_drag_reproduces_from_eq_10_27():
    """§13.3.7a: ~7e-20 W per roller; ×20 rollers / 1e6 moieties -> ~1.4e-24 J per moiety."""
    assert close(ch13.roller_bearing_drag(), 7e-20, 0.02)
    assert close(20 * ch13.roller_bearing_drag() / 1e6, 1.4e-24, 0.02)


def test_mill_dissipation_per_kg():
    """§13.3.7b: 650 maJ × 10 steps -> ~3e8; 145 × 10 -> ~7e7; 1 maJ/atom -> '~1e5'
    (5e4 computed); 30 maJ per op, 1 atom per op -> 1.5e6 J/kg."""
    assert close(ch13.per_kg(650 * MAJ, 10), 3e8, 0.1)
    assert close(ch13.per_kg(145 * MAJ, 10), 7e7, 0.05)
    assert close(ch13.per_kg(1 * MAJ, 1), 5e4, 0.01)
    assert close(ch13.per_kg(30 * MAJ, 1), 1.5e6, 0.01)


def test_mill_dissipation_ops_per_atom_lever():
    """Spot check, not a verdict: the 1.5e6 figure is one 30 maJ operation per atom. With the
    ~10 preparation encounters per moiety of §13.3.3 plus one application at the same mean,
    it is ~1.65e7 J/kg — the whole ~1.5e7 J/kg free energy of §14.4.8."""
    assert close(ch13.per_kg(30 * MAJ, 11), 1.65e7, 0.01)


def test_conditional_repetition():
    """§13.3.7b: N = 10 -> modulation ~20 maJ; simple repetition exoergicity ~15 maJ."""
    assert close(ch13.conditional_repetition_modulation(10), 20 * MAJ, 0.03)
    assert close(ch13.conditional_repetition_exoergicity(10), 15 * MAJ, 0.05)


def test_power_generation():
    """§13.3.8: 475 maJ per H2O is the enthalpy (ΔH_f liquid water); ~8e6 W/kg, ~2e9 W/m^3.
    The free energy is 394 maJ (spot check: the reversible work ceiling is 83% of 475)."""
    assert close(ch13.per_molecule(ch13.H2O_DH_F), 475 * MAJ, 0.01)
    assert close(ch13.per_molecule(ch13.H2O_DG_F), 394 * MAJ, 0.01)
    w_kg, w_m3 = ch13.power_density()
    assert close(w_kg, 8e6, 0.05)
    assert close(w_m3, 2e9, 0.2)


# ---- 13.4 manipulators ----

def test_tube_bending_13_6():
    """Table 13.1 note b: 13.6 mm/N (= 0.0136 m/N)."""
    assert close(ch13.tube_cantilever_compliance(), 0.0136, 0.01)


def test_table_13_1_total_0_04():
    """§13.4.1e: contributions + 4 mm/N drive -> 0.04 m/N (25 N/m). The printed 'Total 4.0'
    row and 'm/mN' header are transcription artefacts for ~40 mm/N."""
    assert close(ch13.table_13_1_total(), 0.04, 0.01)


def test_torsion_compliance_reproduces():
    """Note e: 640 contacts × 10 N/m per interface, two in series -> 0.31 mm/N."""
    assert close(ch13.ring_torsion_compliance(), 0.31e-3, 0.01)


def test_rocking_compliance_10x_book():
    """Note c: the book's ~3e-5 m/N for 650 contacts × 10 N/m; a ring of axial springs w.r.t.
    maximum stretch gives n k / 2 -> 3.1e-4 m/N. Spot check, not a verdict: with it the arm
    total is ~0.087 m/N (~11.5 N/m), and with 10.11's E factor of 0.5 also ~0.10 m/N."""
    assert close(ch13.ring_rocking_compliance(), 3.1e-4, 0.01)
    rock = (ch13.ring_rocking_compliance() + 2e-5) * 1e3
    assert close(ch13.table_13_1_total(rocking_mm_per_n=rock), 0.087, 0.02)
    tube = ch13.tube_cantilever_compliance(E=5e11) * 1e3
    assert close(ch13.table_13_1_total(rocking_mm_per_n=rock, tube_mm_per_n=tube), 0.10, 0.02)


def test_rocking_multiplier_and_scaling():
    """Note c multiplier (tip distance / joint radius)^2: J1 (100/13)^2 ≈ 59. Eq. 2.3 scaling:
    0.04 m/N at 100 nm -> 4e-9 m/N at 1 m."""
    assert round((100 / 13)**2) == 59
    assert close(ch13.scaled_compliance(0.04), 4e-9, 1e-9)


def test_manipulator_productivity_and_per_atom_cost():
    """§13.4.1f: ~5e6 atoms at 1e6 ops/s -> ~5 s; 100 maJ per 1-atom motion is ~5e6 J/kg,
    per 1000-atom cluster ~0.1 maJ/atom."""
    assert close(ch13.manipulator_self_mass_time(), 5.0, 1e-9)
    assert close(ch13.per_kg(100 * MAJ), 5e6, 0.01)


def test_footnote_34_mttf_at_1e4():
    """Fn. 34: 1e-15 at 1e4 /s -> ~3000 years; 1e3 in rate is < 30 maJ of barrier."""
    mttf_years = 1 / (1e-15 * 1e4) / ch13.ch06.YEAR
    assert close(mttf_years, 3000, 0.1)
    assert ch13.energy_for_probability(1e-3) < 30 * MAJ


def test_step_failures_at_1e6_hz():
    """Spot check, not a verdict: at 13.3.7a's 1e6 /s per mechanism (Table 14.1's reagent-prep
    rate), 1e-15 per op is ~0.32 failures per mechanism in 10 years, ~3.2 for a 10-step
    reagent-prep unit. Holding a 10-step unit to 0.01 needs ~3e-18 per op (~167 maJ vs 143)."""
    assert close(ch13.expected_step_failures(), 0.32, 0.02)
    assert close(ch13.expected_step_failures(steps=10), 3.2, 0.02)
    p = ch13.p_step_for_budget(steps=10)
    assert close(p, 3.2e-18, 0.02)
    assert close(ch13.energy_for_probability(p), 167 * MAJ, 0.01)
