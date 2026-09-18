"""Chapter 3: MM2 force field pieces, Morse bonds, nonbonded stiffness under load, Hamaker
constants and the transverse-continuum surface model (Eqs. 3.4–3.38).

All SI. MM2 parameters are the book's Tables 3.1–3.3 and 3.8 (Allinger 1986 as quoted), not
re-sourced; the point is to reproduce what Ch. 3 derives from them and what Ch. 7, 9, 10 read off.
"""
import math
from dataclasses import dataclass

from . import K_B

HBAR = 1.054571817e-34
AMU = 1.66053907e-27
E_CHARGE = 1.602176634e-19
MAJ = 1e-21
AJ = 1e-18

# Table 3.1 (subset): eps_vdw [J], r_vdw [m]
VDW = {
    "C1": (0.357 * MAJ, 1.90e-10),   # sp3 carbon
    "C2": (0.357 * MAJ, 1.94e-10),   # sp2 carbon
    "H5": (0.382 * MAJ, 1.50e-10),
    "N8": (0.447 * MAJ, 1.82e-10),
    "O6": (0.406 * MAJ, 1.74e-10),
    "F11": (0.634 * MAJ, 1.65e-10),
    "S15": (1.641 * MAJ, 2.11e-10),
    "Si19": (1.137 * MAJ, 2.25e-10),
    "LP20": (0.130 * MAJ, 1.20e-10),
}

# Table 3.2 / 3.8 (subset): k_s [N/m], r0 [m], D0 [J], D_e [J]
BONDS = {
    "C-C": (440.0, 1.523e-10, 0.545 * AJ, 0.556 * AJ),
    "C-H": (460.0, 1.113e-10, 0.642 * AJ, 0.671 * AJ),
    "C=C": (960.0, 1.337e-10, 1.190 * AJ, 1.207 * AJ),
    "N-N": (560.0, 1.381e-10, 0.405 * AJ, 0.417 * AJ),
    "C-N": (510.0, 1.438e-10, 0.498 * AJ, 0.509 * AJ),
    "Si-Si": (185.0, 2.332e-10, 0.555 * AJ, 0.559 * AJ),
}


def pair_params(a: str, b: str):
    """MM2 combination rules (§3.3.2e): eps = mean, r_vdw0 = sum."""
    ea, ra = VDW[a]; eb, rb = VDW[b]
    return 0.5 * (ea + eb), ra + rb


# ---- 3.3.2 bonded terms --------------------------------------------------------------------

def v_stretch(r, k_s, r0, k_cubic=2e10) -> float:
    """Eq. 3.4: (1/2) k_s (r-r0)^2 [1 - k_cubic (r-r0)]."""
    d = r - r0
    return 0.5 * k_s * d * d * (1 - k_cubic * d)


def v_bend(theta, k_theta, theta0, k_sextic=0.754) -> float:
    """Eq. 3.5: (1/2) k_theta (theta-theta0)^2 [1 + k_sextic (theta-theta0)^4]."""
    d = theta - theta0
    return 0.5 * k_theta * d * d * (1 + k_sextic * d**4)


def k_perp_from_bend(k_theta, r0) -> float:
    """Eq. 3.6: k_s,perp = k_theta / r0^2. C-C-C: 0.45 aJ/rad^2, 1.523 Å -> 19.4 N/m."""
    return k_theta / r0**2


def v_torsion(omega, V1, V2, V3) -> float:
    """Eq. 3.7: (1/2)[V1(1+cos w) + V2(1-cos 2w) + V3(1+cos 3w)]."""
    return 0.5 * (V1 * (1 + math.cos(omega)) + V2 * (1 - math.cos(2 * omega)) + V3 * (1 + math.cos(3 * omega)))


def torsional_stiffness_at_anti(V1, V2, V3, r0, theta0) -> float:
    """§3.3.2c: tangential stiffness of one terminal atom from a single four-atom term at the
    anti (w = pi) minimum: d2V/dw2 = (1/2)(V1 + 4 V2 + 9 V3), divided by the lever arm (r0 sin theta0)^2.
    C-C-C-C (1.39, 1.88, 0.65 maJ) -> ~0.36 N/m."""
    k_ang = 0.5 * (V1 + 4 * V2 + 9 * V3)
    return k_ang / (r0 * math.sin(theta0))**2


def dipole_partial_charge(mu, r) -> float:
    """§3.3.2d: atom-centred charge q = mu / r; C-F 4.7e-30 C·m over 1.392 Å -> ~0.2 e."""
    return mu / r / E_CHARGE


# ---- 3.3.2e / 3.3.3b nonbonded exp-6 --------------------------------------------------------

def v_vdw(r, eps, r0) -> float:
    """Eq. 3.8: eps [2.48e5 exp(-12.5 r/r0) - 1.924 (r/r0)^-6]. Minimum -eps at r = r0."""
    x = r / r0
    return eps * (2.48e5 * math.exp(-12.5 * x) - 1.924 * x**-6)


def f_vdw(r, eps, r0) -> float:
    """Eq. 3.16: -dV/dr = eps [3.1e6/r0 exp(-12.5 r/r0) - 11.54/r (r/r0)^-6]. Positive = repulsive."""
    x = r / r0
    return eps * (2.48e5 * 12.5 / r0 * math.exp(-12.5 * x) - 1.924 * 6 / r * x**-6)


def k_vdw(r, eps, r0) -> float:
    """Eq. 3.17: d2V/dr2 = eps [3.88e7/r0^2 exp(-12.5 r/r0) - 80.81/r^2 (r/r0)^-6]."""
    x = r / r0
    return eps * (2.48e5 * 12.5**2 / r0**2 * math.exp(-12.5 * x) - 1.924 * 42 / r**2 * x**-6)


def r_at_force(F, eps, r0, lo=None, hi=None) -> float:
    """Separation at which the repulsive force equals F (bisection on the monotone branch)."""
    lo = lo or 0.4 * r0
    hi = hi or r0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f_vdw(mid, eps, r0) > F:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def k_over_f_strong_repulsion(r0) -> float:
    """Eq. 3.18: k ≈ (12.5 / r_vdw0) F; with r_vdw0 = 0.36 nm, 3.5e10 /m."""
    return 12.5 / r0


def v_over_f_strong_repulsion(r0) -> float:
    """Eq. 3.19: V ≈ (r_vdw0 / 12.5) F = 0.08 r_vdw0 F; with 0.36 nm, 2.9e-11 m."""
    return r0 / 12.5


def r_breakdown(r0) -> float:
    """§3.3.3b: below 0.323 r_vdw0 the r^-6 term overwhelms the exponential (nonphysical)."""
    return 0.323 * r0


def r_loaded(F, eps, r_vdw) -> float:
    """Eq. 3.20: summable loaded radius r_vdw/13.6 · ln(2.5e6 eps / (r_vdw F)). eps, r_vdw are the
    single-atom Table 3.1 values (not the pair sums)."""
    return r_vdw / 13.6 * math.log(2.5e6 * eps / (r_vdw * F))


# ---- 3.3.3a Morse ---------------------------------------------------------------------------

def morse_beta(k_s, D_e) -> float:
    """Eq. 3.13: beta = sqrt(k_s / 2 D_e)."""
    return math.sqrt(k_s / (2 * D_e))


def zero_point_correction(k_s, m1, m2) -> float:
    """Eq. 3.14: D_e - D0 ≈ (hbar/2) sqrt(k_s / mu)."""
    mu = m1 * m2 / (m1 + m2)
    return 0.5 * HBAR * math.sqrt(k_s / mu)


def v_morse(r, D_e, beta, r0) -> float:
    """Eq. 3.10: D_e ({1 - exp[-beta (r-r0)]}^2 - 1)."""
    return D_e * ((1 - math.exp(-beta * (r - r0)))**2 - 1)


def f_morse(r, D_e, beta, r0) -> float:
    """Eq. 3.11 (restoring force, positive = tension resisting extension)."""
    d = r - r0
    return 2 * beta * D_e * (math.exp(-beta * d) - math.exp(-2 * beta * d))


def k_morse(r, D_e, beta, r0) -> float:
    """Eq. 3.12."""
    d = r - r0
    return 2 * beta**2 * D_e * (2 * math.exp(-2 * beta * d) - math.exp(-beta * d))


def morse_inflection(r0, beta) -> float:
    """§3.3.3a: r0 + ln2/beta; a Morse bond stretched past this under constant force is unstable."""
    return r0 + math.log(2) / beta


def morse_most_negative_stiffness_point(r0, beta) -> float:
    """§3.4.2: r0 + ln4/beta, where k = -0.125 k_s."""
    return r0 + math.log(4) / beta


def v_lippincott(r, D_e, k_s, r0) -> float:
    """Eq. 3.15, r >= r0."""
    return D_e * (1 - math.exp(-k_s * r0 * (r - r0)**2 / (2 * D_e * r)))


# ---- 3.5.1 Hamaker ---------------------------------------------------------------------------

def dispersion_C(eps, r0) -> float:
    """Eq. 3.28: C = 1.924 eps r_vdw0^6."""
    return 1.924 * eps * r0**6


def hamaker_pairwise(C, n1, n2) -> float:
    """Eq. 3.29: A12 = pi^2 C n1 n2."""
    return math.pi**2 * C * n1 * n2


def hamaker_lifshitz(n1, eps1, n2=None, eps2=None, n3=1.0, eps3=1.0, T=300.0, hbar_omega=2e-18) -> float:
    """Eq. 3.32 (Israelachvili approximation)."""
    n2 = n1 if n2 is None else n2
    eps2 = eps1 if eps2 is None else eps2
    a = (n1**2 - n3**2) * (n2**2 - n3**2)
    b = (math.sqrt(n1**2 + n3**2) + math.sqrt(n2**2 + n3**2)) * math.sqrt((n1**2 + n3**2) * (n2**2 + n3**2))
    disp = 3 * hbar_omega / (8 * math.sqrt(2)) * a / b
    dip = 0.75 * K_B * T * ((eps1 - eps3) / (eps1 + eps3)) * ((eps2 - eps3) / (eps2 + eps3))
    return disp + dip


def f_sphere_sphere(A, r1, r2, s) -> float:
    """Fig. 3.10 (Israelachvili): F = A r1 r2 / (6 s^2 (r1 + r2)); equal spheres A r / (12 s^2)."""
    return A * r1 * r2 / (6 * s**2 * (r1 + r2))


def p_plane_plane(A, s) -> float:
    """Fig. 3.10: force per unit area A / (6 pi s^3)."""
    return A / (6 * math.pi * s**3)


# ---- 3.5.2 transverse-continuum surface model -------------------------------------------------

@dataclass(frozen=True)
class Surface:
    """One side of a Fig. 3.12 interface: explicit outer plane (n_a, atom type) over a continuum
    (n_v, atom type) whose Hamaker surface sits d_g behind the plane."""
    n_a: float
    a_type: str
    n_v: float
    v_type: str
    d_g: float


FIG_3_12 = {
    "a": Surface(0.9e19, "C1", 1.50e29, "C1", 0.09e-9),
    "b": Surface(0.9e19, "C1", 0.75e29, "C1", 0.09e-9),
    "c": Surface(1.8e19, "C1", 1.50e29, "C1", 0.09e-9),
    "d": Surface(1.8e19, "C1", 0.75e29, "C1", 0.09e-9),
    "e": Surface(1.4e19, "Si19", 1.50e29, "C1", 0.13e-9),
}


def v_plane_plane_per_area(s, n_a1, n_a2, eps, r0) -> float:
    """Eq. 3.34 with Eq. 3.36: n1 n2 pi [2A/b^2 (b s + 1) exp(-b s) - C/(2 s^4)]."""
    A = 2.48e5 * eps
    b = 12.5 / r0
    C = dispersion_C(eps, r0)
    return n_a1 * n_a2 * math.pi * (2 * A / b**2 * (b * s + 1) * math.exp(-b * s) - C / (2 * s**4))


def v_plane_volume_per_area(s, n_a, n_v, C) -> float:
    """Eq. 3.37: -n_a n_v pi C / (6 s^3)."""
    return -n_a * n_v * math.pi * C / (6 * s**3)


def v_volume_volume_per_area(s, n_v1, n_v2, C) -> float:
    """Eq. 3.38: -n_v1 n_v2 pi C / (12 s^2)."""
    return -n_v1 * n_v2 * math.pi * C / (12 * s**2)


def v_surface_per_area(s, S1: Surface, S2: Surface) -> float:
    """Eq. 3.33 for two surfaces whose outer planes are s apart; continuum surfaces sit d_g
    behind each plane (the reading of §3.5.2 adopted here)."""
    eps_aa, r0_aa = pair_params(S1.a_type, S2.a_type)
    eps_av, r0_av = pair_params(S1.a_type, S2.v_type)
    eps_va, r0_va = pair_params(S1.v_type, S2.a_type)
    eps_vv, r0_vv = pair_params(S1.v_type, S2.v_type)
    return (v_plane_plane_per_area(s, S1.n_a, S2.n_a, eps_aa, r0_aa)
            + v_plane_volume_per_area(s + S2.d_g, S1.n_a, S2.n_v, dispersion_C(eps_av, r0_av))
            + v_plane_volume_per_area(s + S1.d_g, S2.n_a, S1.n_v, dispersion_C(eps_va, r0_va))
            + v_volume_volume_per_area(s + S1.d_g + S2.d_g, S1.n_v, S2.n_v, dispersion_C(eps_vv, r0_vv)))


def surface_curve(S1: Surface, S2: Surface, s_lo=0.15e-9, s_hi=0.6e-9, n=451):
    """Energy, force (per area; positive = repulsive) and stiffness (per area) vs separation, by
    finite differences of Eq. 3.33. Returns list of (s, V/S, F/S, k_a)."""
    out = []
    h = 1e-13
    for i in range(n):
        s = s_lo + (s_hi - s_lo) * i / (n - 1)
        v = v_surface_per_area(s, S1, S2)
        vp = v_surface_per_area(s + h, S1, S2)
        vm = v_surface_per_area(s - h, S1, S2)
        F = -(vp - vm) / (2 * h)
        k = (vp - 2 * v + vm) / h**2
        out.append((s, v, F, k))
    return out


def interface_summary(curve):
    """Max tensile stress (most negative F/S), its separation, the zero-force separation, the
    stiffness there, and the separation where k_a crosses zero."""
    s_eq = min(curve, key=lambda t: abs(t[2]))[0]
    k_eq = min(curve, key=lambda t: abs(t[0] - s_eq))[3]
    tmax = min(curve, key=lambda t: t[2])
    kzero = min((t for t in curve if t[0] > s_eq), key=lambda t: abs(t[3]))
    return {"s_eq": s_eq, "k_a_eq": k_eq, "tensile_max": -tmax[2], "s_tensile_max": tmax[0],
            "s_k_zero": kzero[0], "tension_at_k_zero": -kzero[2]}
