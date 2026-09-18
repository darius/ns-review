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


# =====================================================================================
# §7.2 Acoustic radiation from forced oscillations
# =====================================================================================

HBAR = 1.054571817e-34
K_B = 1.380649e-23


def p_rad_point_force(F_max, omega, rho, M) -> float:
    """Eq. 7.8: P_rad = F_max^2 omega^2 sqrt(rho) / (8 pi M^{3/2}). Equal-speed approximation."""
    return F_max**2 * omega**2 * math.sqrt(rho) / (8 * math.pi * M**1.5)


def tau_osc_linear(m, k_s, rho, M) -> float:
    """Eq. 7.10: radiative decay time of an embedded linear oscillator, 4 pi m M^{3/2} / (k_s^2 sqrt(rho))."""
    return 4 * math.pi * m * M**1.5 / (k_s**2 * math.sqrt(rho))


def frac_loss_linear(m, k_s, rho, M) -> float:
    """Eq. 7.11: fractional energy loss per cycle, (1/2) sqrt(rho/m) (k_s/M)^{3/2}, for f << 1."""
    return 0.5 * math.sqrt(rho / m) * (k_s / M)**1.5


def p_rad_point_torque(T_max, omega, rho, G) -> float:
    """Eq. 7.15: P_rad = T_max^2 omega^4 rho^{3/2} / (48 pi G^{5/2})."""
    return T_max**2 * omega**4 * rho**1.5 / (48 * math.pi * G**2.5)


def frac_loss_torsional(I, k_theta, rho, G) -> float:
    """Eq. 7.17: (1/12) (rho/I)^{3/2} (k_theta/G)^{5/2}."""
    return (rho / I)**1.5 * (k_theta / G)**2.5 / 12


def p_rad_pressure_in_volume(F_max, omega, rho, M, r0) -> float:
    """Eq. 7.21: oscillating pressure in a spherical cavity of radius r0 (nu = 0, M = E)."""
    x = rho * omega**2 * r0**2 / (2 * M)
    return F_max**2 * omega**2 * math.sqrt(rho) / (16 * math.pi * M**1.5) / (x + 1 / x)


def band_velocity_ratio(k1, k2) -> float:
    """Eq. 7.22: R = |k1| / |k2 - k1| for collinear rows."""
    return abs(k1) / abs(k2 - k1)


def p_rad_piston_limit_per_area(A, omega, M, rho, k_a=None) -> float:
    """Eq. 7.24 per unit area (k_a given) or Eq. 7.25 (k_a None, 'always conservative'):
    radiation from an interface entering/leaving alignment as a whole (R -> infinity)."""
    base = A**2 * omega**2 * math.sqrt(M * rho)
    if k_a is None:
        return base / 4
    return base / (M * rho * omega**2 / k_a**2 + 4)


def soreff_nonadiabatic_probability(v_s, v) -> float:
    """§7.2.6d: exp(-2 omega tau) with omega tau ≈ v_s / v (Soreff 1991; Kogan & Galitskiy 1963)."""
    return math.exp(-2 * v_s / v)


# =====================================================================================
# §7.3 Phonons and phonon scattering
# =====================================================================================

def k_debye_book(n_v) -> float:
    """Eq. 7.29 AS PRINTED: k_D = (6 pi n_v)^{1/3}. Matches the Figure 7.3 caption (1.24e10 for
    n = 100/nm^3) and the 1570 K Debye temperature quoted in §7.3.2."""
    return (6 * math.pi * n_v)**(1 / 3)


def k_debye_standard(n_v) -> float:
    """Standard Debye cutoff (Ashcroft & Mermin ch. 23): k_D = (6 pi^2 n_v)^{1/3}, one factor of pi
    larger inside the root than Eq. 7.29."""
    return (6 * math.pi**2 * n_v)**(1 / 3)


def debye_temperature(k_D, v_s) -> float:
    """Eq. 7.30: T_D = hbar k_D v_s / k."""
    return HBAR * k_D * v_s / K_B


def debye_mean_sound_speed(v_l, v_t) -> float:
    """Eq. 7.31: v_s = ((1/3) v_l^-3 + (2/3) v_t^-3)^{-1/3}."""
    return ((v_l**-3) / 3 + 2 * (v_t**-3) / 3)**(-1 / 3)


def debye_energy_density(v_s, n_v, T, k_D=None, steps=20000) -> float:
    """Eq. 7.28: eps = (3 hbar v_s / 2 pi^2) ∫_0^{k_D} k^3 / (exp(hbar k v_s / kT) - 1) dk  [J/m^3].
    k_D defaults to the book's Eq. 7.29. Simple midpoint quadrature."""
    kD = k_D if k_D is not None else k_debye_book(n_v)
    h = kD / steps
    s = 0.0
    for i in range(steps):
        k = (i + 0.5) * h
        x = HBAR * k * v_s / (K_B * T)
        s += k**3 / math.expm1(x)
    return 3 * HBAR * v_s / (2 * math.pi**2) * s * h


def phonon_pressure(eps) -> float:
    """Eq. 7.27: p = eps / 3 on a surface able to move relative to the medium."""
    return eps / 3


def p_drag_scattering(eps, sigma_therm, v, v_s) -> float:
    """Eq. 7.32: P_drag ≈ (4/3) eps sigma_therm v^2 / v_s (isotropic scatterer, v << v_s)."""
    return 4 / 3 * eps * sigma_therm * v**2 / v_s


def sigma_oscillator_offresonance(k_s, M, m, omega) -> float:
    """Eq. 7.34: sigma ≈ (1/2pi) (k_s/M)^2 (k_s/(m omega^2) + 1)^-2, far from resonance."""
    return (k_s / M)**2 / (2 * math.pi) / (k_s / (m * omega**2) + 1)**2


def p_drag_band_stiffness_per_area(eps, T_trans, dk_over_k, R, v, v_s) -> float:
    """Eq. 7.35 per unit area: P < 0.85 eps T_trans (dk_a/k_a) R^2 v^2 / v_s. Upper bound."""
    return 0.85 * eps * T_trans * dk_over_k * R**2 * v**2 / v_s


def p_drag_band_flutter_per_area(eps, T_trans, A_over_d, R, v, v_s) -> float:
    """Eq. 7.37 per unit area: P < eps T_trans (2 pi A/d)^2 R^2 v^2 / v_s. Upper bound."""
    return eps * T_trans * (2 * math.pi * A_over_d)**2 * R**2 * v**2 / v_s


def t_trans_rod(E_l, k, k_s) -> float:
    """Eq. 7.38: 1-D rod interrupted by a spring, [1 + (E_l k / 2 k_s)^2]^-1."""
    return 1 / (1 + (E_l * k / (2 * k_s))**2)


def t_trans_fit(d_n, T_prime) -> float:
    """Eq. 7.41: T_trans ≈ z/(1+3z), z = 0.6 d_n^-1.7 (1 + 0.075 T'^-1.8). d_n = n^{-1/3} M / k_a,
    T' = T/T_D. Stated to overestimate transmission (conservative for drag)."""
    z = 0.6 * d_n**-1.7 * (1 + 0.075 * T_prime**-1.8)
    return z / (1 + 3 * z)


def p_drag_shear_reflection_per_area(eps, T_trans, v, v_s, D_sr=1.0) -> float:
    """Eq. 7.46 per unit area: P ≈ (eps/2) T_trans D_sr v^2 / v_s, D_sr ≈ 1 'appears conservative'."""
    return 0.5 * eps * T_trans * D_sr * v**2 / v_s


# =====================================================================================
# §7.5 Compression of potential wells
# =====================================================================================

def r_temp_square_well(f, alpha) -> float:
    """Eq. 7.58: T_g/T_s = [1 + f^2/4 - f sqrt(2/pi) (2/alpha - 1)]^-1."""
    return 1 / (1 + f**2 / 4 - f * math.sqrt(2 / math.pi) * (2 / alpha - 1))


def w_isothermal_compression(T, l1, l2) -> float:
    """Eq. 7.60: kT ln(l1/l2)."""
    return K_B * T * math.log(l1 / l2)


def dw_square_well_compression(m, T_s, alpha, l1_over_l2, v_total) -> float:
    """Eq. 7.62: ΔW ≈ sqrt(2 m k T_s / pi) (2/alpha - 1) ln(l1/l2) v_total."""
    return math.sqrt(2 * m * K_B * T_s / math.pi) * (2 / alpha - 1) * math.log(l1_over_l2) * v_total


def k_s1_nonbonded_contact(m, rho_c, k_per_area=3e19) -> float:
    """Eq. 7.66-7.67: k_s,1 ≈ 3e19 (m/rho_c)^{2/3}  [N/m], graphite interlayer stiffness × contact area."""
    return k_per_area * (m / rho_c)**(2 / 3)


def dw_harmonic_well_compression(T, m, M, rho, k_ext, v_ext, k_s1, c_load=3.5e10) -> float:
    """Eq. 7.68: ΔW ≈ kT (pi m M^{3/2} / 3 sqrt(rho)) · 3.5e10 · k_ext v_ext / k_s1^3
    (k_s ≈ 3.5e10 F_load from Eq. 3.18; k_ext substantially less than k_s1; large compression ratio)."""
    return K_B * T * math.pi * m * M**1.5 / (3 * math.sqrt(rho)) * c_load * k_ext * v_ext / k_s1**3


# =====================================================================================
# §7.6 Transitions among time-dependent wells
# =====================================================================================

def f_diss_symmetric_merge(T) -> float:
    """Eq. 7.78: symmetric well merging (bit erasure) dissipates kT ln 2."""
    return K_B * T * math.log(2)


def f_diss_asymmetric_reverse(T, dF) -> float:
    """Eq. 7.80: starting in the upper well's empty state, |ΔF_diss| ≈ kT exp(-dF/kT) << kT."""
    return K_B * T * math.exp(-dF / (K_B * T))
