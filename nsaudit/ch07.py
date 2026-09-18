"""Chapter 7 §7.4: thermoelastic damping and phonon viscosity (Eqs. 7.47–7.54).

Drexler's model is phenomenological: both mechanisms are written as the adiabatic/isothermal
work difference of a cycle, scaled by (relaxation time / cycle time) when the relaxation is
fast. The same structure is the low-frequency limit of the standard Akhiezer/Zener relaxation
form, which is also provided here (`akhiezer_q_inverse`, `fq_max`) so the two can be compared
on one footing.
"""
import math

# Diamond inputs as stated in §7.4.1 (book values; vintage flags live in chapters/ch07.yaml).
DIAMOND_BETA = 3.5e-6      # 1/K, volumetric CTE (Gray 1972)
DIAMOND_K = 4.4e11         # Pa, bulk modulus
DIAMOND_C_VOL = 1.7e6      # J/(K m^3)
T300 = 300.0


def grueneisen(beta: float, K: float, C_vol: float) -> float:
    """Eq. 7.47: gamma_G = beta K / C_vol."""
    return beta * K / C_vol


def delta_w_thermoelastic(beta: float, T: float, C_vol: float, dp: float, V: float) -> float:
    """Eq. 7.49: adiabatic-minus-isothermal work of compression, (1/2) beta^2 (T/C_vol) dp^2 V.

    Drexler's "worst-case thermodynamic cycle" dissipates 2× this (adiabatic compression,
    nonequilibrium cooling, adiabatic expansion, nonisothermal warming).
    """
    return 0.5 * beta**2 * (T / C_vol) * dp**2 * V


def worst_case_cycle_thermoelastic(beta, T, C_vol, dp, V) -> float:
    """§7.4.1 text: worst-case cycle loss = 2 ΔW of Eq. 7.49."""
    return 2.0 * delta_w_thermoelastic(beta, T, C_vol, dp, V)


def cycle_loss_thermoelastic(beta, T, C_vol, dp, V, tau_therm, t_cycle) -> float:
    """Eq. 7.50: ΔW_cycle ≈ 2 beta^2 (T/C_vol) dp^2 (tau_therm / t_cycle) V.

    Valid in the nearly-isothermal regime tau_therm << t_cycle. Not capped; callers wanting a
    bound should take min(this, worst_case_cycle_thermoelastic).
    """
    return 2.0 * beta**2 * (T / C_vol) * dp**2 * (tau_therm / t_cycle) * V


def tau_therm(C_vol: float, K_T: float, l: float, v_s: float | None = None) -> float:
    """Eq. 7.51: tau_therm ≈ max(C_vol l^2 / K_T, l / v_s).

    The ballistic floor l/v_s is in the printed equation but omitted from the prose; pass
    v_s=None to get the diffusive term alone, which is what the worked example uses.
    """
    diffusive = C_vol * l**2 / K_T
    return diffusive if v_s is None else max(diffusive, l / v_s)


def eta_phonon(tau_relax: float, gamma_G: float, T: float, C_vol: float) -> float:
    """Eq. 7.52: effective phonon viscosity, tau_relax (3/2) gamma_G^2 T C_vol."""
    return tau_relax * 1.5 * gamma_G**2 * T * C_vol


def delta_w_shear(beta, T, C_vol, dgamma, V) -> float:
    """Adiabatic-minus-isothermal work of shear, by Drexler's 'within a factor of 3/2' analogy:
    (3/2) × Eq. 7.49 with shear stress in place of pressure.

    The book gives only the fast-relaxation form (Eq. 7.53); this is the corresponding
    relaxation-strength bound, an extrapolation of the same analogy. Its worst-case cycle
    is 2× this, by the §7.4.1 argument.
    """
    return 1.5 * delta_w_thermoelastic(beta, T, C_vol, dgamma, V)


def cycle_loss_phonon_viscosity(beta, T, C_vol, dgamma, V, tau_relax, t_cycle) -> float:
    """Eq. 7.53: ΔW_cycle ≈ (3/2) beta^2 (T/C_vol) dgamma^2 (tau_relax / t_cycle) V."""
    return 1.5 * beta**2 * (T / C_vol) * dgamma**2 * (tau_relax / t_cycle) * V


def p_drag_per_area(beta, T, K_T, l, dp, R, v) -> float:
    """Eq. 7.54 per unit band area: P_drag / S ≈ beta^2 (T/K_T) l dp^2 R^2 v^2  [W/m^2].

    Assumes phonon mean free paths shorter than l (7.4.3/mfp-shorter-than-l).
    """
    return beta**2 * (T / K_T) * l * dp**2 * R**2 * v**2


# ---- Standard relaxation (Akhiezer / Zener) form, for comparison ------------------------

def relaxation_strength(gamma: float, C_vol: float, T: float, modulus: float) -> float:
    """Δ = gamma^2 C_vol T / M: fractional adiabatic-isothermal modulus difference.

    With gamma = beta M / C_vol this equals beta^2 T M / C_vol, so Drexler's Eq. 7.49 is
    ΔW = Δ × (elastic energy ½ dp^2 V / M): the same quantity.
    """
    return gamma**2 * C_vol * T / modulus


def akhiezer_q_inverse(delta: float, omega: float, tau: float) -> float:
    """Q^-1 = Δ · ωτ / (1 + ω²τ²). Peak Δ/2 at ωτ = 1; ∝ ωτ below (Drexler's regime)."""
    x = omega * tau
    return delta * x / (1.0 + x * x)


def fq_max(rho: float, v: float, C_vol: float, T: float, gamma: float, tau: float) -> float:
    """(f·Q)_max ≈ rho v^2 / (2π gamma^2 C_vol T tau): the Akhiezer ceiling as quoted by
    Prase (2026) Eq. 1 after Cleland (2013) ch. 8. Equals 1/(2π tau Δ)."""
    return rho * v**2 / (2.0 * math.pi * gamma**2 * C_vol * T * tau)


def tau_from_fq_max(rho, v, C_vol, T, gamma, fq) -> float:
    """Invert fq_max for the thermalization time implied by a quoted f·Q ceiling."""
    return rho * v**2 / (2.0 * math.pi * gamma**2 * C_vol * T * fq)
