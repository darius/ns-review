"""Chapter 10 §10.3.4–10.3.6, §10.4: sliding contacts and symmetrical sleeve bearings.

Every function names its equation. The §10.4.6 drag formulas are Ch. 7 results specialised to
diamond at 300 K; the specialisation constants (2.4e-37, 1.8e-33, 3.0e-33, 1.2e-31, 4.3e-27)
are re-derived here from the Ch. 7 functions so the chain of provenance is executable.
"""
import math

from . import ch07
from .ch07 import K_B

# Diamond inputs used by §10.4.6 ("modulus, atom number density, and Debye temperature of diamond")
DIAMOND_E = 1.05e12        # Pa, Table 9.1
DIAMOND_G = 0.5 * DIAMOND_E
DIAMOND_RHO = 3500.0
DIAMOND_N = 1.76e29        # m^-3 (Fig. 7.4 caption: 176/nm^3)
DIAMOND_TD_MEASURED = 2230.0   # K (Gray 1972, quoted in §7.3.2)
DIAMOND_TD_EQ7_29 = 1570.0     # K, from the printed Eq. 7.29
DIAMOND_V_S = 1.38e4       # m/s, Eq. 7.31 value quoted in §7.3.2
EPS_300 = 2e8              # J/m^3, the Ch. 7 working phonon energy density


# ---- 10.3.4 small sliding contacts -----------------------------------------------------------

def f_max_from_barrier(dV) -> float:
    """Eq. 10.6 (from Eq. 3.19): F_max ≈ 1.7e10 ΔV_barrier  [N per J]."""
    return 1.7e10 * dV


def p_rad_contact(dV, v, k, rho=DIAMOND_RHO, M=DIAMOND_E) -> float:
    """Eq. 10.7: P_rad ≈ 2.9e20 ΔV^2 v^2 k^2 sqrt(rho) / (8 pi M^{3/2}); omega = k v."""
    return ch07.p_rad_point_force(f_max_from_barrier(dV), k * v, rho, M)


def static_friction(dV, d_a) -> float:
    """Eq. 10.8: F_frict = 4 pi ΔV_barrier / d_a."""
    return 4 * math.pi * dV / d_a


def negative_stiffness_bound(dV1, d_a) -> float:
    """Eq. 10.9: |k_s| <= 3 ΔV_1 (pi/d_a)^2."""
    return 3 * dV1 * (math.pi / d_a)**2


# ---- 10.4.5 transverse-continuum stiffness -------------------------------------------------------

def k_s_bear(k_a, l, r_eff) -> float:
    """Eq. 10.15: k_s,bear = pi k_a l r_eff."""
    return math.pi * k_a * l * r_eff


def k_a_from_k_s(k_s, l, r_eff) -> float:
    return k_s / (math.pi * l * r_eff)


# ---- 10.4.6 dissipation ------------------------------------------------------------------------

def p_rad_torsional_bearing(dV, r_eff, v_inter, d_a, rho=DIAMOND_RHO, G=DIAMOND_G) -> float:
    """Eq. 10.16: torque amplitude pi ΔV r_eff / d_a at omega = 2 pi v / d_a into Eq. 7.15."""
    return ch07.p_rad_point_torque(math.pi * dV * r_eff / d_a, 2 * math.pi * v_inter / d_a, rho, G)


def p_rad_force_bearing(F_max, v_inter, d_a, rho=DIAMOND_RHO, M=DIAMOND_E) -> float:
    """Eq. 10.17: Eq. 7.8 at omega = 2 pi v / d_a."""
    return ch07.p_rad_point_force(F_max, 2 * math.pi * v_inter / d_a, rho, M)


def critical_sliding_speed(d_a, k_s_trans, m_rotor) -> float:
    """Eq. 10.18: v = (d_a / 2 pi) sqrt(k_s,trans / m_rotor)."""
    return d_a / (2 * math.pi) * math.sqrt(k_s_trans / m_rotor)


def t_trans_coefficient(M=DIAMOND_E, n=DIAMOND_N, T=300.0, T_D=DIAMOND_TD_MEASURED) -> float:
    """The constant c in Eq. 10.19-10.20, z = c k_a^1.7, obtained from Eq. 7.41 with
    d_n = n^{1/3} M / k_a (atomic layers of the medium with the interface's stiffness).

    NB: §7.3.5e prints d_n = n^{-1/3} M / k_a, which has units of m^2; the layer-count reading the
    text gives it, and the value 2.4e-37 printed in Eq. 10.19, both require n^{+1/3}.
    """
    T_prime = T / T_D
    return 0.6 * (n**(1 / 3) * M)**-1.7 * (1 + 0.075 * T_prime**-1.8)


def t_trans_bearing(k_a, c=None) -> float:
    """Eq. 10.19: T_trans ≈ z/(1+3z), z = 2.4e-37 k_a^1.7 (k_a in N/m^3)."""
    c = 2.4e-37 if c is None else c
    z = c * k_a**1.7
    return z / (1 + 3 * z)


def shear_reflection_coefficient(eps=EPS_300, v_s=DIAMOND_V_S, c_t=2.4e-37) -> float:
    """Constant in Eq. 10.21: (eps/2) c_t / v_s  -> 1.8e-33 (k_a^1.7 v^2 S)."""
    return 0.5 * eps * c_t / v_s


def cyl_conversion() -> float:
    """Factor turning a per-area k_a^1.7 law (Eq. 10.21/10.23) into the k_s,bear^1.7 (l r)^-0.7
    form (Eq. 10.22/10.24): S = 2 pi r l and k_a = k_s/(pi l r) give 2 pi · pi^-1.7 = 0.897."""
    return 2 * math.pi * math.pi**-1.7


def p_drag_shear_reflection(k_s, l, r_eff, v) -> float:
    """Eq. 10.22: P < 1.6e-33 k_s,bear^1.7 (l r_eff)^-0.7 v^2."""
    return 1.6e-33 * k_s**1.7 * (l * r_eff)**-0.7 * v**2


def p_drag_band_stiffness(k_s, l, r_eff, R, dk_over_k, v) -> float:
    """Eq. 10.24: P < 2.7e-33 k_s,bear^1.7 (l r_eff)^-0.7 R^2 (Δk_a/k_a) v^2."""
    return 2.7e-33 * k_s**1.7 * (l * r_eff)**-0.7 * R**2 * dk_over_k * v**2


def p_drag_band_flutter(k_s, l, r_eff, R, A_over_d, v) -> float:
    """Eq. 10.25: P < 1.2e-31 k_s,bear^1.7 (l r_eff)^-0.7 R^2 (A/d_a)^2 v^2."""
    return 1.2e-31 * k_s**1.7 * (l * r_eff)**-0.7 * R**2 * A_over_d**2 * v**2


def flutter_amplitude(k_a, dk_over_k, R, d_a, M=DIAMOND_E):
    """§10.4.6d: Δp <= 3e-11 Δk_a; w = R d_a / 2 pi; A ≈ w Δp / M. Returns (dp, w, A)."""
    dp = 3e-11 * dk_over_k * k_a
    w = R * d_a / (2 * math.pi)
    return dp, w, w * dp / M


def thermoelastic_coefficient(beta=3.5e-6, T=300.0, tau=1e-12, C_vol=1.7e6) -> float:
    """Constant in Eq. 10.26, 4.3e-27 = 2 beta^2 T tau / C_vol: Eq. 7.50 with t_cycle = d_a / v."""
    return 2 * beta**2 * T * tau / C_vol


def p_drag_thermoelastic(r_eff, l, w, dp, v, d_a) -> float:
    """Eq. 10.26: P ≈ 4.3e-27 · 2 pi r_eff l w (Δp v / d_a)^2."""
    return 4.3e-27 * 2 * math.pi * r_eff * l * w * (dp * v / d_a)**2


def p_drag_total(k_s, l, r_eff, R, dk_over_k, v) -> float:
    """Eq. 10.27: P < (2.0e-33 + 3.5e-33 (Δk_a/k_a) R^2) k_s^1.7 (l r)^-0.7 v^2 (×1.3 for axial stiffness)."""
    return (2.0e-33 + 3.5e-33 * dk_over_k * R**2) * k_s**1.7 * (l * r_eff)**-0.7 * v**2


def energy_per_rotation(P, r_eff, v) -> float:
    return P * 2 * math.pi * r_eff / v
