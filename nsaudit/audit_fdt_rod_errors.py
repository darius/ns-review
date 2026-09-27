"""Audit of Prase (2026) App. C.2 (fluctuation-dissipation) against 12.3.7's error model.

Prase: by FDT, force noise S_FF = 2 m γ kT; with the book's damping, σ_F ≈ 14 pN over 10 ps
(fine), but with damping "a conservative three orders of magnitude larger", σ_F ≈ 0.5 nN
against the 1 nN alignment force, "enough to cause an error in 0.1-1% of cycles". Against this,
12.3.7 uses the equilibrium PDF (Eq. 12.21-12.25): a hard stop held by F_al = 1 nN, error beyond
0.7 nm, P ≈ 1.3e-67, and 5.3.1 says bath coupling does not change the statistics.

Checks:
1. Stationary statistics: Langevin dynamics of the alignment coordinate (rod mass against a
   hard stop under constant force F_al, damping γ, FDT noise). P(x > x0) should equal
   exp(-F_al x0 / kT) for every γ. Simulated at small x0 (measurable probabilities) across 1e5
   in γ.
2. Energy bound: non-thermal excitation must put F_al Δx_thresh (700 maJ, ~169 kT) into the
   alignment coordinate to cause an error; compare the largest identified single excitations.
3. Stiffness bound: coupling to other modes enters equilibrium statistics only through the
   potential of mean force, i.e. the effective stiffness between probe and gate knobs. The
   stiffness at which a Gaussian tail beyond 0.7 nm reaches 1e-15 (ignoring F_al) bounds how
   soft the assembly must be for errors to matter.
"""
import math
import random

from . import ch12
from .ch12 import EX

K_B = 1.380649e-23
T = 300.0
KT = K_B * T
MAJ = 1e-21
GAMMA_BOOK = 2 * math.pi * 4e6      # s^-1, Prase's damping rate from 12.3.4c's sliding friction


# ---- 1. Langevin at a hard stop -------------------------------------------------------------------

def langevin_exceedance(gamma: float, x0s=(5e-12, 10e-12, 20e-12), m: float | None = None,
                        F: float | None = None, dt: float = 2e-15, steps: int = 400_000,
                        seed: int = 1) -> dict:
    """Fraction of time the alignment coordinate x >= 0 (distance from the stop) exceeds each x0.
    Constant force -F toward the stop, reflecting wall at x = 0, velocity-Verlet-like
    integrator with exact Ornstein-Uhlenbeck velocity update (BAOAB-style)."""
    rng = random.Random(seed)
    m = ch12.m_rod_eq12_8(EX) if m is None else m
    F = EX.F_al if F is None else F
    c1 = math.exp(-gamma * dt)
    c2 = math.sqrt((1 - c1 * c1) * KT / m)
    a = -F / m
    x, v = KT / F, 0.0
    counts = [0] * len(x0s)
    for _ in range(steps):
        v += 0.5 * dt * a
        x += 0.5 * dt * v
        v = c1 * v + c2 * rng.gauss(0.0, 1.0)
        x += 0.5 * dt * v
        if x < 0:
            x, v = -x, -v
        v += 0.5 * dt * a
        for i, x0 in enumerate(x0s):
            if x > x0:
                counts[i] += 1
    return {x0: c / steps for x0, c in zip(x0s, counts)}


def boltzmann_exceedance(x0: float, F: float | None = None) -> float:
    F = EX.F_al if F is None else F
    return math.exp(-F * x0 / KT)


def prase_force_noise(damping_multiplier: float = 1.0, bandwidth: float = 2 * math.pi * 100e9) -> float:
    """Prase Eq. 2-4: σ_F over ±100 GHz from friction and bulk-diamond Akhiezer (f·Q = 3.7e13 Hz)
    terms, the whole spectrum scaled by `damping_multiplier`. Book damping -> ~14 pN; ×1000 ->
    ~0.44 nN ("nearly 0.5 nN")."""
    m = ch12.m_rod_eq12_8(EX)
    wq = 2 * math.pi * 3.7e13
    # (1/2π) ∫_{-W}^{W} 2 m kT (γ + ω²/wq) dω
    var = (1 / (2 * math.pi)) * 2 * m * KT * (2 * GAMMA_BOOK * bandwidth + 2 * bandwidth**3 / (3 * wq))
    return math.sqrt(var * damping_multiplier)


# ---- 2. energy bound ----------------------------------------------------------------------------------

def error_energy(p=EX) -> float:
    """Work to lift the alignment knob Δx_thresh against F_al."""
    return p.F_al * ch12.dx_thresh(p)


# ---- 3. stiffness bound -------------------------------------------------------------------------------

def stiffness_for_tail(p_err: float = 1e-15, dx: float | None = None) -> float:
    """Effective probe-gate stiffness at which a Gaussian tail beyond dx equals p_err
    (one-sided), ignoring the alignment force entirely."""
    dx = ch12.dx_thresh(EX) if dx is None else dx
    lo, hi = 0.0, 10.0
    for _ in range(200):                           # z with ½ erfc(z/√2) = p_err
        z = (lo + hi) / 2
        if 0.5 * math.erfc(z / math.sqrt(2)) > p_err:
            lo = z
        else:
            hi = z
    sigma = dx / z
    return KT / sigma**2
