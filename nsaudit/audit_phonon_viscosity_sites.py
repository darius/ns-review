"""The 7.4.2 phonon-viscosity exception at its remaining unevaluated use sites: 10.4.6 (sample
bearing), 13.3.7a (mill roller bearings) and 13.4.1f (manipulator worm-drive interfaces).

Method as in audit_phonon_viscosity_rod_logic (the 12.3.4 spike): Eq. 7.53 with the shear part
of the stress (taken as Δp/2) over the 10.4.6d band-flutter stress region, capped by the
relaxation-strength bound; compared with 10.4.6e's thermoelastic term and 10.4.6's total drag.
Cycle frequency v/d_a. τ from the book (1e-13 s) or from the bulk-diamond f·Q ceiling
(1.2e-11 s, v = 1.8e4 m/s, γ = 0.9, as in the spike).
"""
import math

from . import ch07, ch10

TAU_BOOK = 1e-13
TAU_FQ = ch07.tau_from_fq_max(3500, 1.8e4, 1.7e6, 300, 0.9, 3.7e13)
TAU_THERM_10_4_6 = 1e-12          # s, Eq. 10.26's asserted τ_therm
D_A = 0.25e-9


def omega_tau(v: float, tau: float, d_a: float = D_A) -> float:
    return 2 * math.pi * (v / d_a) * tau


def bearing_phonon_viscosity(v: float, dk_over_k: float, tau: float, k_a: float = 8e19,
                             k_s: float = 1000.0, r_eff: float = 2e-9, l: float = 2e-9,
                             R: float = 10, d_a: float = D_A) -> dict:
    """Power (W) of the omitted term vs the book's thermoelastic term and total drag."""
    dp, w, _ = ch10.flutter_amplitude(k_a, dk_over_k, R, d_a)
    te = ch10.p_drag_thermoelastic(r_eff, l, w, dp, v, d_a)
    total = ch10.p_drag_total(k_s, l, r_eff, R, dk_over_k, v)
    # Eq. 7.53 has the thermoelastic form with (3/2) τ_relax and shear dγ = dp/2 in place of
    # 2 τ_therm and dp: PV/TE = 1.5 τ (1/2)^2 / (2 τ_therm).
    pv = te * 1.5 * tau * 0.25 / (2 * TAU_THERM_10_4_6)
    V = 2 * math.pi * r_eff * l * w
    cap = 2 * ch07.delta_w_shear(3.5e-6, 300, 1.7e6, dp / 2, V) * (v / d_a)
    pv = min(pv, cap)
    return {"pv": pv, "te": te, "total": total, "fraction": pv / total,
            "omega_tau": omega_tau(v, tau, d_a)}
