"""Chapter 12 §12.3–12.4, §12.7.4: the exemplar logic rod (Eqs. 12.1–12.25) and CPU power.

All inputs are the exemplar parameters stated in §12.3.3 (see `Exemplar`). h_rod is not stated
in the text; it is inferred from S_eff = 0.64 nm^2 with w_rod = 1 nm and delta_surf = 0.1 nm.
"""
import math
from dataclasses import dataclass

from . import K_B


@dataclass(frozen=True)
class Exemplar:
    w_rod: float = 1e-9        # m, §12.3.3a
    h_rod: float = 1e-9        # m, inferred from S_eff = 0.64 nm^2
    h_knob: float = 0.5e-9     # m
    d_knob: float = 2e-9       # m, from w_rod = d_knob/2 (Eq. 12.2)
    l_knob: float = 1e-9       # m, = d_knob/2
    n_in: int = 16
    n_out: int = 16
    F_al: float = 1e-9         # N, §12.3.3b
    delta_surf: float = 1e-10  # m, §12.3.3c
    E: float = 5e11            # Pa, "conservative", ~1/2 diamond
    rho: float = 3500.0        # kg/m^3
    t_switch: float = 1e-10    # s, §12.3.4a
    k_a: float = 1e19          # N/m^3  (= 10 N/m·nm^2, §12.3.4c)
    beta: float = 5e-6         # 1/K, §12.3.4e "will prove conservative"
    C_vol: float = 1.7e6       # J/(K m^3), §12.3.4e
    T: float = 300.0
    k_sp: float = 10.0         # N/m, probe knob transverse stiffness, §12.3.7b
    k_sg: float = 40.0         # N/m, gate knob longitudinal stiffness, "conservatively"
    r_eff: float = 0.15e-9     # m, §12.3.7a
    w_knob: float = 1e-9       # m, = w_rod

    @property
    def l_in(self): return self.d_knob * self.n_in
    @property
    def l_out(self): return self.d_knob * self.n_out
    @property
    def l_rod(self): return self.d_knob * (self.n_in + self.n_out + 1)          # Eq. 12.3
    @property
    def S_eff(self): return (self.w_rod - 2*self.delta_surf) * (self.h_rod - 2*self.delta_surf)  # Eq. 12.4


EX = Exemplar()


def k_s(p: Exemplar, l: float) -> float:
    """Eq. 12.5: stretching stiffness S_eff E / l."""
    return p.S_eff * p.E / l


def m_rod_eq12_6(p: Exemplar) -> float:
    """Eq. 12.6 (§12.3.3c): rho l_rod (w-2δ)[(h_rod-2δ) + h_knob (l_knob-2δ)/d_knob]. Book: 1.9e-22."""
    return p.rho * p.l_rod * (p.w_rod - 2*p.delta_surf) * (
        (p.h_rod - 2*p.delta_surf) + p.h_knob * (p.l_knob - 2*p.delta_surf) / p.d_knob)


def m_rod_eq12_8(p: Exemplar) -> float:
    """Eq. 12.8 (§12.3.4a): rho l_rod (w-2δ)(h_rod + h_knob/2 - 2δ). Book: 1.94e-22."""
    return p.rho * p.l_rod * (p.w_rod - 2*p.delta_surf) * (p.h_rod + p.h_knob/2 - 2*p.delta_surf)


def f_accel(p: Exemplar, m: float) -> float:
    """Eq. 12.9: m (π/t_switch)^2 d_knob/4."""
    return m * (math.pi / p.t_switch)**2 * p.d_knob / 4


def v_max(p: Exemplar) -> float:
    """Eq. 12.10: π d_knob / 4 t_switch."""
    return math.pi * p.d_knob / (4 * p.t_switch)


def kinetic_energy(p: Exemplar, m: float) -> float:
    return 0.5 * m * v_max(p)**2


def v_sound(p: Exemplar) -> float:
    """Eq. 12.13: sqrt(E / rho(1 + h_knob/2h_rod))."""
    return math.sqrt(p.E / (p.rho * (1 + p.h_knob / (2 * p.h_rod))))


def omega_0(p: Exemplar) -> float:
    """Eq. 12.14: π v_s / 2 l_rod."""
    return math.pi * v_sound(p) / (2 * p.l_rod)


def e_vib(p: Exemplar) -> float:
    """Eq. 12.15: 2 S_eff d^2 rho^2 l_rod^3 / (E t_switch^4) · (1 + h_knob/2h_rod)^2. Book: 0.56 maJ."""
    return (2 * p.S_eff * p.d_knob**2 * p.rho**2 * p.l_rod**3 / (p.E * p.t_switch**4)
            * (1 + p.h_knob / (2 * p.h_rod))**2)


def contact_area(p: Exemplar) -> float:
    """Eq. 12.16: l_rod (w_rod + 2 h_rod)."""
    return p.l_rod * (p.w_rod + 2 * p.h_rod)


def e_drag(p: Exemplar) -> float:
    """Eq. 12.17: 3.3e-32 · l_rod (w_rod + 2h_rod) · d_knob^2 k_a^1.7 / t_switch, k_a in N/m^3.
    Book: 0.052 maJ. (Eq. 10.23 with Δk_a/k_a = 0.4, R = 10; the 3.3e-32 carries the units.)"""
    return 3.3e-32 * contact_area(p) * p.d_knob**2 * p.k_a**1.7 / p.t_switch


def e_drag_per_area_speed(p: Exemplar, S: float, v_rms_sq: float, duration: float) -> float:
    """Eq. 12.17 re-expressed per unit area and mean-square speed, for the cam surface (§12.3.4d).
    Eq. 12.17 = c S k_a^1.7 <v^2> t_switch with <v^2> = v_max^2/2 and v_max = π d/4t, so
    c = 3.3e-32 · 32/π^2."""
    c = 3.3e-32 * 32 / math.pi**2
    return c * S * p.k_a**1.7 * v_rms_sq * duration


def v_cam(p: Exemplar) -> float:
    """Eq. 12.18: 2 v_max (1 + 4 F_al l_in / d_knob S_eff E). Book: 38 m/s."""
    return 2 * v_max(p) * (1 + 4 * p.F_al * p.l_in / (p.d_knob * p.S_eff * p.E))


def e_cam(p: Exemplar, S_cam: float = 4e-18, duty_factor: float = 5.0) -> float:
    """§12.3.4d: cam drag per rod per 0.1 ns (~0.012 maJ) × reciprocal duty fraction (~5) → ~0.06 maJ."""
    return e_drag_per_area_speed(p, S_cam, v_cam(p)**2, p.t_switch) * duty_factor


def e_therm_eq12_19(p: Exemplar) -> float:
    """Eq. 12.19 as printed: 8.2e-5 beta^2 (2F_al)^2 / S_eff · l_in. Book: < 0.41 maJ."""
    return 8.2e-5 * p.beta**2 * (2 * p.F_al)**2 / p.S_eff * p.l_in


def e_therm_from_eq7_49(p: Exemplar) -> float:
    """Eq. 7.49 applied to the tensioning transition with dp = 2F_al/S_eff, V = S_eff l_in:
    (1/2) beta^2 (T/C_vol) dp^2 V. This is what Eq. 12.19 should reduce to; the printed
    coefficient 8.2e-5 vs (1/2)(T/C_vol) = 8.8e-5 differ by ~7%."""
    dp = 2 * p.F_al / p.S_eff
    V = p.S_eff * p.l_in
    return 0.5 * p.beta**2 * (p.T / p.C_vol) * dp**2 * V


def e_switching_cycle(p: Exemplar) -> float:
    """§12.3.8b: losses per switching cycle including reset ≈ 2 × (vib + drag + cam + therm). Book: ~2 maJ."""
    return 2 * (e_vib(p) + e_drag(p) + e_cam(p) + e_therm_eq12_19(p))


def e_state(p: Exemplar) -> float:
    """Eq. 12.20: F_al (d_knob/2 + 2 F_al l_in / E S_eff). Book: 1.2 aJ."""
    return p.F_al * (p.d_knob / 2 + 2 * p.F_al * p.l_in / (p.E * p.S_eff))


def q_implied(p: Exemplar) -> float:
    """Prase (2026) App. C: Q = 2π × (energy stored) / (energy lost per cycle), with the switching
    loss (§12.3.8b) against the state energy (Eq. 12.20). Not a book number."""
    return 2 * math.pi * e_state(p) / e_switching_cycle(p)


def sigma_el(p: Exemplar) -> float:
    """Eq. 12.21: sqrt(kT (1/k_sp + 1/k_sg)). Book: 0.023 nm."""
    return math.sqrt(K_B * p.T * (1 / p.k_sp + 1 / p.k_sg))


def dx_thresh(p: Exemplar) -> float:
    """§12.3.7a: w_knob - 2 r_eff. Book: 0.7 nm."""
    return p.w_knob - 2 * p.r_eff


def p_err_disp(p: Exemplar) -> float:
    """Eq. 12.25: exp[(1/2)(σ F_al/kT)^2 − Δx_thresh F_al/kT]. Book: 1.3e-67."""
    kT = K_B * p.T
    a = sigma_el(p) * p.F_al / kT
    return math.exp(0.5 * a * a - dx_thresh(p) * p.F_al / kT)


def cpu_energy_per_clock(n_interlocks=1e6, e_interlock=0.03e-21, n_registers=1e4, e_register=4.4e-21) -> float:
    """§12.7.4: 1e6 interlocks × 0.03 maJ + 1e4 register cells × 4.4 maJ per clock. Book: 74 aJ."""
    return n_interlocks * e_interlock + n_registers * e_register


def cpu_power(t_clock=1.2e-9, **kw) -> float:
    """§12.7.4: energy per clock / 1.2 ns. Book: ~60 nW."""
    return cpu_energy_per_clock(**kw) / t_clock
