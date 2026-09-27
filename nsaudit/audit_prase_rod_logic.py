"""Audit of Prase (2026) Appendix C against Ch. 12 rod logic, and its propagation into §14.4.8.

Three of Prase's arguments are checked quantitatively here:

1. Molecular relaxation (C.1): the rod's centre of mass sees the drive with a lag
   τ = ℓ_rod / v_s ≈ 6 ps; a lumped delayed-force model gives net work ≈ 0.6 × ½ m v_max² per
   switch. For a linear elastic rod the net work over a rest-to-rest motion equals the
   vibrational energy left in it, which is computed exactly below by modal superposition
   (fixed-free rod in the frame of a stiffly driven end, Eq. 12.7 motion). This is the same
   physics as the book's Eq. 12.15.
2. Eq. 7.40's sin 2θ (C.3): Prase reads it as sin θ, raising T_trans 10-100×. Both weightings
   are evaluated. Eq. 7.40 is stated as a mean *power* transmission coefficient; power incident
   from direction θ carries the flux factor cos θ, so sin θ cos θ = ½ sin 2θ is the standard
   (acoustic-mismatch-model) weighting.
3. Propagation into 14.4.8's computation term: Ch. 14 needs ~1e18 instructions/s, not GHz
   clocks. Every rod-logic loss mechanism in the book and in Prase's C.1 (drag, cam drag,
   Akhiezer/phonon viscosity, thermoelastic, vibrational excitation) falls at least as
   1/t_switch; the register's ln(2) kT per cell per cycle (12.4.3) does not. Slowing the clock
   by s costs s× more CPUs.

Not checked here: the collective-mode version of (1) (Prase fn. 32 vs 12.3.4h), which neither
party quantifies; edge friction (Qu et al. 2020, not read); the FDT error argument (C.2), a
separate edge at 12.3.7.
"""
import cmath
import math

from . import ch12
from .ch12 import EX, Exemplar

MAJ = 1e-21
AJ = 1e-18


# ---- 1. molecular relaxation ------------------------------------------------------------------

def lag_time(p: Exemplar = EX) -> float:
    """Prase: τ = ℓ_rod / v_s (6 ps)."""
    return p.l_rod / ch12.v_sound(p)


def prase_lag_work(p: Exemplar = EX) -> float:
    """Prase's lumped delayed-force model: ∫_0^π m v² sin φ cos(φ + δ) dφ with δ = π τ / t_switch;
    magnitude (π/2) sin δ · m v_max² (≈ 0.6 × ½ m v_max²)."""
    m = ch12.m_rod_eq12_8(p)
    delta = math.pi * lag_time(p) / p.t_switch
    return math.pi / 2 * math.sin(delta) * m * ch12.v_max(p)**2


def residual_vibration(p: Exemplar = EX, t_switch: float | None = None, nmodes: int = 60,
                       steps: int = 4000) -> float:
    """Exact energy left in the elastic rod after the Eq. 12.7 motion imposed at one end.

    Fixed-free modes in the moving frame: φ_n = sin β_n x, β_n = (2n-1)π/2ℓ, ω_n = v_s β_n,
    modal mass m/2, participation Γ_n = 4/((2n-1)π); q̈ + ω² q = -Γ ü_end. After the motion,
    E_n = ½ (m/2) Γ_n² |∫ ü_end e^{iωs} ds|². Stiff end drive (a soft drive spring filters more).
    """
    T = t_switch if t_switch is not None else p.t_switch
    m, L, v, d = ch12.m_rod_eq12_8(p), p.l_rod, ch12.v_sound(p), p.d_knob
    a = math.pi / T
    h = T / steps
    E = 0.0
    for n in range(1, nmodes + 1):
        w = v * (2 * n - 1) * math.pi / (2 * L)
        G = 4 / ((2 * n - 1) * math.pi)
        I = sum((d / 4) * a * a * math.cos(a * (i + 0.5) * h) * cmath.exp(1j * w * (i + 0.5) * h)
                for i in range(steps)) * h
        E += 0.5 * (m / 2) * G * G * abs(I)**2
    return E


def cycle_with_exact_vibration(p: Exemplar = EX) -> float:
    """12.3.8b's 2 × (vib + drag + cam + therm) with the exact residual in place of Eq. 12.15."""
    return 2 * (residual_vibration(p) + ch12.e_drag(p) + ch12.e_cam(p) + ch12.e_therm_eq12_19(p))


# ---- 2. Eq. 7.40 angular weighting ----------------------------------------------------------------

def t_trans_eq7_40(d_n: float, T_prime: float, weight: str = "sin2", nk: int = 200, nt: int = 20000) -> float:
    """Eq. 7.40 with d' = (6π²)^{1/3} d_n (standard Debye cutoff), weight 'sin2' (as printed)
    or 'sin' (Prase's reading). Grid refined toward grazing incidence."""
    dp = d_n * (6 * math.pi**2)**(1 / 3)
    num = den = 0.0
    for i in range(nk):
        k = (i + 0.5) / nk
        b = k**3 / math.expm1(k / T_prime)
        den += b
        s = 0.0
        for j in range(nt):
            u = (j + 0.5) * (math.pi / 2) / nt          # u = π/2 - θ
            w = math.sin(2 * u) if weight == "sin2" else math.cos(u)
            s += w / ((dp * k * math.sin(u))**2 + 4)
        num += b * s * (math.pi / 2) / nt
    return 4 / 3 * num / den


def d_n_of(k_a: float, M: float = 1.05e12, n: float = 1.76e29) -> float:
    """d_n = n^{+1/3} M / k_a (the dimensionless form; see the 7.3.5e sign note)."""
    return n**(1 / 3) * M / k_a


# ---- 3. clock-rate scaling of the 14.4.8 computation term -----------------------------------------

INSTR_PER_KG = 1e6 * 1e15            # §14.4.8: 1e6 instructions per block × 1e15 blocks
THROUGHPUT = 1e-3                    # kg/s, 14.4.3
CPU_DENSITY = 1e19                   # CPUs/m^3, §12.7 via 14.5.5g
CPU_RATE_BOOK = 1e9                  # instructions/s at the 1.2 ns-class clock (12.5.2c)
REGISTER_FLOOR = 1e4 * math.log(2) * ch12.K_B * 300.0     # J per clock: 1e4 cells × ln2 kT (12.4.3)
REGISTER_SPEED_DEP = 1e4 * 1.59 * MAJ                      # J per clock, 12.4.3's design-dependent part


def instructions_per_second() -> float:
    return INSTR_PER_KG * THROUGHPUT


def cpu_volume(slowdown: float) -> float:
    """m^3 of CPUs to supply the instruction rate at clock rate CPU_RATE_BOOK / slowdown."""
    return instructions_per_second() / (CPU_RATE_BOOK / slowdown) / CPU_DENSITY


def energy_per_instruction(rod_term_at_ghz: float, slowdown: float) -> float:
    """Rod (interlock) losses and the register's design-dependent part scale as 1/slowdown (all
    identified mechanisms are ∝ v or steeper); the ln 2 kT register floor does not."""
    return (rod_term_at_ghz + REGISTER_SPEED_DEP) / slowdown + REGISTER_FLOOR


def computation_term(rod_term_at_ghz: float, slowdown: float) -> float:
    return energy_per_instruction(rod_term_at_ghz, slowdown) * INSTR_PER_KG


# ---- 4. edge friction as a Prandtl-Tomlinson question ----------------------------------------------
# Superlubric edge friction (Qu et al. 2020, unread; Gao et al. arXiv:2411.04609, Wang, Ma and
# Tosatti arXiv:2306.00205) is stick-slip at incompletely compensated edges: speed-independent
# when present. The book's smooth-sliding licence (10.12) rests on symmetry cancellation, which
# rod ends and knob edges break. Stick-slip occurs if the edge corrugation's maximum negative
# stiffness (Eq. 10.9: 3 ΔV (π/d_a)²) exceeds the stiffness holding the edge.

D_A = 0.25e-9                 # m, typical d_a (10.3.5)
SURFACE_ATOM_DENSITY = 1.8e19  # m^-2, (111)-like (6.4.4c)


def corrugation_from_stiffness(k_atom: float, d_a: float = D_A) -> float:
    """Per-atom corrugation ΔV1 whose Eq. 10.9 bound equals k_atom (10.3.4's 'several N/m per
    atom' read as a corrugation curvature; an interpretation, not a book number)."""
    return k_atom / (3 * (math.pi / d_a)**2)


def edge_negative_stiffness(n_edge: int, dV1: float, coherent: bool = False, d_a: float = D_A) -> float:
    """Eq. 10.9 for the summed edge corrugation: amplitudes add as n (coherent) or √n (random phase)."""
    dV = (n_edge if coherent else math.sqrt(n_edge)) * dV1
    return 3 * dV * (math.pi / d_a)**2


def rod_edge_atoms(p: Exemplar = EX, edge_fraction: float = 0.01) -> float:
    """Interface atoms on the rod's sliding area (Eq. 12.16) × Prase's optimistic 1% edge share."""
    return ch12.contact_area(p) * SURFACE_ATOM_DENSITY * edge_fraction


def stick_slip_energy_per_switch(n_edge: int, dV1: float, coherent: bool = False,
                                 travel: float = 1e-9, d_a: float = D_A) -> float:
    """If unstable, ~ΔV_edge dissipated per d_a of travel, independent of speed."""
    dV = (n_edge if coherent else math.sqrt(n_edge)) * dV1
    return dV * travel / d_a
