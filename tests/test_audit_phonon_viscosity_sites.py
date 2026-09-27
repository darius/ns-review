"""7.4.2 exception at 10.4.6, 13.3.7a, 13.4.1f (nsaudit/audit_phonon_viscosity_sites.py)."""
from nsaudit import audit_phonon_viscosity_sites as a


def test_tau_from_fq():
    assert abs(a.TAU_FQ - 1.18e-11) / 1.18e-11 < 0.01


def test_sample_bearing_high_drag_case():
    """10.4.6, Δk/k = 0.4, 1 m/s: modern τ puts the band stress at ωτ ≈ 0.3 (the exception's
    regime); the omitted term is ~1.4e-15 W, +5% on the 2.7e-14 W total. Book τ: negligible."""
    r = a.bearing_phonon_viscosity(1.0, 0.4, a.TAU_FQ)
    assert 0.25 < r["omega_tau"] < 0.35
    assert 0.04 < r["fraction"] < 0.06
    assert a.bearing_phonon_viscosity(1.0, 0.4, a.TAU_BOOK)["fraction"] < 1e-3


def test_sample_bearing_low_drag_case():
    """Δk/k = 0.003: band stress scales with Δk, so the term is ~1e-4 of total even at modern τ."""
    assert a.bearing_phonon_viscosity(1.0, 0.003, a.TAU_FQ)["fraction"] < 1e-3


def test_mill_bearings_outside_regime():
    """13.3.7a: bearing surface at 0.004 × 2/5 = 0.0016 m/s: ωτ ≈ 5e-4 at modern τ; the
    exception is not triggered and the term is ~5% of an already negligible drag."""
    r = a.bearing_phonon_viscosity(0.0016, 0.4, a.TAU_FQ)
    assert r["omega_tau"] < 1e-3
    assert r["fraction"] < 0.06


def test_manipulator_worm_drive():
    """13.4.1f: J2 drive ring ~1 m/s, the 'nearly pure shear' branch; same regime as the sample
    bearing, so <= ~5% on the ~10 maJ per motion."""
    assert a.bearing_phonon_viscosity(1.0, 0.4, a.TAU_FQ)["fraction"] < 0.06
