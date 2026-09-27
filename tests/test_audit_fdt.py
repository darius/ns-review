"""Prase (2026) C.2 (fluctuation-dissipation) vs 12.3.7 (nsaudit/audit_fdt_rod_errors.py)."""
import math

from nsaudit import audit_fdt_rod_errors as a, ch12
from nsaudit.ch12 import EX

MAJ = 1e-21


def close(x, y, tol):
    return abs(x - y) <= tol * abs(y)


def test_prase_force_noise_reproduces():
    """Prase Eq. 2-4: σ_F ≈ 14 pN with the book's friction and bulk Akhiezer; ×1000 damping
    -> ~0.44 nN ('nearly 0.5 nN'). As a force criterion, P(F > 1 nN) would be ~1%."""
    assert close(a.prase_force_noise(), 14e-12, 0.03)
    s = a.prase_force_noise(1000)
    assert close(s, 0.44e-9, 0.02)
    assert 0.005 < 0.5 * math.erfc(EX.F_al / (s * math.sqrt(2))) < 0.02


def test_displacement_statistics_independent_of_damping():
    """Langevin dynamics at a hard stop under F_al: the time fraction beyond 5 and 10 pm matches
    exp(-F x0 / kT) (0.30, 0.089) at 1e4× and 1e5× the book's damping — 10-100× beyond Prase's
    scenario. Larger damping raises force noise and drag together (FDT); the displacement
    distribution, which is what an error requires, does not change."""
    for mult in (1e4, 1e5):
        r = a.langevin_exceedance(a.GAMMA_BOOK * mult, x0s=(5e-12, 10e-12), steps=1_000_000)
        assert close(r[5e-12], a.boltzmann_exceedance(5e-12), 0.1)
        assert close(r[10e-12], a.boltzmann_exceedance(10e-12), 0.2)


def test_error_requires_700_maj():
    """Lifting the alignment knob 0.7 nm against 1 nN takes 700 maJ (169 kT) in that coordinate:
    ~600× the exact residual vibration (1.2 maJ), ~50× Prase's lag estimate (14.5 maJ), ~3× the
    largest edge-slip event considered (216 maJ, coherent worst case)."""
    assert close(a.error_energy(), 700 * MAJ, 1e-9)
    assert close(a.error_energy() / a.KT, 169, 0.01)


def test_stiffness_margin():
    """A 1e-15 Gaussian tail beyond 0.7 nm (ignoring F_al) needs an effective probe-gate
    stiffness below ~0.53 N/m; the book's elastic path is 8 N/m (10 and 40 N/m in series,
    σ_el 0.023 nm): a 15× margin before any credit for the alignment force."""
    assert close(a.stiffness_for_tail(), 0.53, 0.01)
    k_series = 1 / (1 / EX.k_sp + 1 / EX.k_sg)
    assert close(k_series / a.stiffness_for_tail(), 15, 0.02)
