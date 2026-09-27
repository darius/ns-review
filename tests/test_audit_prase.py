"""Prase (2026) Appendix C vs Ch. 12 rod logic (nsaudit/audit_prase_rod_logic.py)."""
from nsaudit import audit_prase_rod_logic as a, ch12
from nsaudit.ch12 import EX

MAJ = 1e-21


def close(x, y, tol):
    return abs(x - y) <= tol * abs(y)


def test_prase_lag_model_reproduces():
    """C.1: τ = ℓ/v_s ≈ 6 ps; lumped delayed-force work ≈ 0.6 × ½ m v_max² ≈ 14 maJ per switch."""
    assert close(a.lag_time(), 6e-12, 0.05)
    ke = ch12.kinetic_energy(EX, ch12.m_rod_eq12_8(EX))
    assert close(a.prase_lag_work() / ke, 0.6, 0.02)


def test_exact_residual_vs_prase_and_book():
    """Exact continuum residual (stiff end drive) 1.2 maJ per switch: Prase's 14.5 maJ is 12×
    too high; the book's phase-averaged Eq. 12.15 (0.56 maJ) is 2.1× low for this geometry."""
    r = a.residual_vibration()
    assert close(r, 1.20 * MAJ, 0.01)
    assert close(a.prase_lag_work() / r, 12.0, 0.02)
    assert close(r / ch12.e_vib(EX), 2.14, 0.02)


def test_residual_scales_as_fourth_power():
    """Residual ∝ t_switch^-4.2: at 0.3 ns it is ~1/100 of the 0.1 ns value (Prase's lag model
    would fall only as 1/t)."""
    assert close(a.residual_vibration() / a.residual_vibration(t_switch=3e-10), 103, 0.03)


def test_cycle_with_exact_vibration():
    """12.3.8b's ~2.17 maJ per switching cycle becomes ~3.45 maJ with the exact residual."""
    assert close(a.cycle_with_exact_vibration(), 3.45 * MAJ, 0.01)


def test_eq_7_40_weighting():
    """C.3: reading sin 2θ as sin θ raises T_trans 7.5× at the 10.4.6 bearing (d_n ≈ 74) and 35×
    at the rod interfaces (d_n ≈ 588) — Prase's '10 to 100' is right arithmetically. Both
    weightings give 1/3 in the stiff limit; sin 2θ = 2 sin θ cos θ is the power-flux weighting
    the text's 'mean power transmission coefficient' calls for."""
    assert close(a.d_n_of(8e19), 73.6, 0.01) and close(a.d_n_of(1e19), 588, 0.01)
    r74 = a.t_trans_eq7_40(73.6, 0.1345, "sin", nk=80, nt=4000) / a.t_trans_eq7_40(73.6, 0.1345, "sin2", nk=80, nt=4000)
    r588 = a.t_trans_eq7_40(588, 0.1345, "sin", nk=80, nt=4000) / a.t_trans_eq7_40(588, 0.1345, "sin2", nk=80, nt=4000)
    assert close(r74, 7.5, 0.03) and close(r588, 35.4, 0.03)
    for w in ("sin", "sin2"):
        assert close(a.t_trans_eq7_40(1e-3, 0.1345, w, nk=80, nt=4000), 1 / 3, 1e-4)


def test_ch14_needs_no_ghz_clock():
    """14.4.8 needs 1e18 instructions/s: 1e9 CPUs at 1e9/s (2e-7 kg), 1e12 at 1e6/s (2e-4 kg at
    2000 kg/m^3) — negligible against a ~kg-scale system either way."""
    assert close(a.instructions_per_second(), 1e18, 1e-9)
    assert close(a.cpu_volume(1000) * 2000, 2e-4, 1e-6)


def test_prase_penalty_absorbed_by_clock():
    """With the book's per-rod cycle ×100 (Prase's '>= 2 OOM'), the computation term at GHz is
    2.2e7 J/kg (more than ΔG ≈ 1.43e7); at a 100× slower clock 2.5e5, at 1000× 5e4. The floor is
    the register's ln 2 kT: 2.9e4 J/kg. Valid for every mechanism scaling as 1/t_switch or
    steeper; not for a speed-independent edge friction."""
    rod = 1e5 * ch12.e_switching_cycle(EX)
    assert close(a.computation_term(100 * rod, 1), 2.18e7, 0.01)
    assert close(a.computation_term(100 * rod, 100), 2.46e5, 0.01)
    assert close(a.computation_term(100 * rod, 1000), 5.05e4, 0.01)
    assert close(a.REGISTER_FLOOR * a.INSTR_PER_KG, 2.87e4, 0.01)


def test_edge_stick_slip_not_excluded():
    """Open item, not a verdict: with 10.3.4's 'several N/m per atom' (1-5 N/m -> 2-11 maJ of
    corrugation by Eq. 10.9) and ~36 uncompensated edge atoms, the edge's negative stiffness is
    ~6-110 N/m (random to coherent phase), against 4.9 N/m holding the rod's far end (Eq. 12.5;
    the drive end is held by a constant-force spring). If unstable: ~50-900 maJ per switch,
    speed-independent — 20-400× the book's whole cycle, and not removed by a slower clock."""
    assert close(ch12.k_s(EX, EX.l_rod), 4.85, 0.01)
    n = round(a.rod_edge_atoms())
    assert n == 36
    dV_lo, dV_hi = a.corrugation_from_stiffness(1.0), a.corrugation_from_stiffness(3.0)
    assert close(dV_lo, 2.1 * MAJ, 0.02) and close(dV_hi, 6.3 * MAJ, 0.02)
    k_lo = a.edge_negative_stiffness(n, dV_lo)
    k_hi = a.edge_negative_stiffness(n, dV_hi, coherent=True)
    assert k_lo > ch12.k_s(EX, EX.l_rod) and close(k_hi, 107, 0.02)
    assert close(a.stick_slip_energy_per_switch(n, dV_lo), 51 * MAJ, 0.02)
    assert close(a.stick_slip_energy_per_switch(n, dV_hi, coherent=True), 900 * MAJ, 0.02)
