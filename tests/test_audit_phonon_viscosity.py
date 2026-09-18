"""Sanity and regression for the 7.4.2 -> 12.3.4 edge audit. Numbers here are ours, not the book's."""
from nsaudit import audit_phonon_viscosity_rod_logic as A

maJ = 1e-21


def test_regime_and_magnitudes():
    r = A.run()
    assert r.omega_tau_book < 1e-2                  # book tau: deep in the Akhiezer (omega tau << 1) regime
    assert r.omega_tau_fq < 1                       # f·Q-implied tau: still below the peak at 5 GHz
    assert r.e_pv_book_tau < r.e_pv_fq_tau < 2 * r.e_shear_bound
    assert 0.1 * maJ < r.e_shear_bound < 0.3 * maJ  # tau-independent bound per transition
    assert r.added_fraction_worst < 0.25            # worst case adds < 25% to the 2 maJ cycle
    assert r.added_fraction_fq < 0.02               # with the f·Q tau, < 2%


def test_report_runs():
    assert "omitted term" in A.report()
