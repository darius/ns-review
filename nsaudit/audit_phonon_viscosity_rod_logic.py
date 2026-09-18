"""Audit of the edge 7.4.2/phonon-viscosity-small-except → 12.3.4 (mobile logic rod).

Question: §12.3.4's dissipation inventory (vibration, sliding drag, cam drag, thermoelastic,
"other") omits phonon viscosity. §7.4.2 says phonon-viscosity losses are small "save in systems
undergoing very high frequency motion or nearly pure shear", with no threshold. Is a rod
tensioned in 0.1 ns such a system, and what would including the term cost?

Method: apply Drexler's own §7.4.2 model (Eq. 7.53 and its relaxation-strength bound) to the
tensioning transition of the exemplar rod, with the shear stress taken as the deviatoric part of
the uniaxial tension (max shear = σ/2), for (a) the book's tau_relax = 1e-13 s, (b) the
inelastic thermalization time implied by the bulk-diamond f·Q ceiling that Prase (2026) cites
from Chandorkar et al. (2008), and (c) the τ-independent worst case.
"""
import math
from dataclasses import dataclass

from . import ch07, ch12
from .ch12 import EX, Exemplar

TAU_RELAX_BOOK = 1e-13          # s, 7.4.2/tau-relax-1e-13 (BARE)
FQ_DIAMOND_PRASE = 3.7e13       # Hz, Prase App. C.1 citing Chandorkar et al. 2008
V_S_DIAMOND = (1.2e4, 1.8e4)    # m/s, mean and longitudinal; brackets the tau backed out of f·Q
RHO_DIAMOND = 3500.0


@dataclass(frozen=True)
class Result:
    sigma: float                 # Pa, tensile stress in the input segment during tensioning
    dgamma: float                # Pa, max shear = sigma/2
    V: float                     # m^3, tensioned volume S_eff l_in
    t_cycle: float               # s, 2 t_switch (period of the Eq. 12.7 cosine motion)
    f_eff: float                 # Hz
    e_therm_bound: float         # J, Eq. 12.19 as printed (the book's own thermoelastic bound)
    e_shear_bound: float         # J, relaxation-strength bound for the shear part (tau-independent)
    tau_from_fq: float           # s, thermalization time implied by the f·Q ceiling (v = 1.8e4 m/s)
    tau_from_fq_low: float       # s, same with v = 1.2e4 m/s
    e_pv_book_tau: float         # J, Eq. 7.53 with tau = 1e-13
    e_pv_fq_tau: float           # J, Eq. 7.53 with tau from f·Q
    omega_tau_book: float
    omega_tau_fq: float
    omega_tau_fq_10ghz: float    # same at Prase's 10 GHz (1/t_switch)
    e_cycle_book: float          # J, §12.3.8b total per switching cycle incl. reset
    added_fraction_worst: float  # (2 × shear bound) / e_cycle_book
    added_fraction_fq: float     # (2 × e_pv_fq_tau) / e_cycle_book


def run(p: Exemplar = EX, gamma_G: float = 0.9) -> Result:
    sigma = 2 * p.F_al / p.S_eff
    dgamma = sigma / 2
    V = p.S_eff * p.l_in
    t_cycle = 2 * p.t_switch
    omega = 2 * math.pi / t_cycle

    e_therm_bound = ch12.e_therm_eq12_19(p)
    e_shear_bound = ch07.delta_w_shear(p.beta, p.T, p.C_vol, dgamma, V)

    tau_fq_low, tau_fq = (ch07.tau_from_fq_max(RHO_DIAMOND, v, p.C_vol, p.T, gamma_G, FQ_DIAMOND_PRASE)
                          for v in V_S_DIAMOND)

    def pv(tau):  # Eq. 7.53, capped at the worst-case cycle (2 × relaxation-strength bound)
        raw = ch07.cycle_loss_phonon_viscosity(p.beta, p.T, p.C_vol, dgamma, V, tau, t_cycle)
        return min(raw, 2 * e_shear_bound)

    e_cycle = ch12.e_switching_cycle(p)
    return Result(
        sigma=sigma, dgamma=dgamma, V=V, t_cycle=t_cycle, f_eff=1 / t_cycle,
        e_therm_bound=e_therm_bound, e_shear_bound=e_shear_bound, tau_from_fq=tau_fq, tau_from_fq_low=tau_fq_low,
        e_pv_book_tau=pv(TAU_RELAX_BOOK), e_pv_fq_tau=pv(tau_fq),
        omega_tau_book=omega * TAU_RELAX_BOOK, omega_tau_fq=omega * tau_fq,
        omega_tau_fq_10ghz=2 * math.pi / p.t_switch * tau_fq,
        e_cycle_book=e_cycle,
        added_fraction_worst=2 * e_shear_bound / e_cycle,
        added_fraction_fq=2 * pv(tau_fq) / e_cycle,
    )


def report(r: Result | None = None) -> str:
    r = r or run()
    maJ = 1e-21
    return "\n".join([
        f"tension sigma = {r.sigma/1e9:.2f} GPa; max shear = {r.dgamma/1e9:.2f} GPa; V = {r.V*1e27:.1f} nm^3",
        f"effective frequency 1/(2 t_switch) = {r.f_eff/1e9:.0f} GHz",
        f"book thermoelastic bound (Eq. 12.19)          = {r.e_therm_bound/maJ:.3f} maJ per transition",
        f"shear relaxation-strength bound (tau-indep.)  = {r.e_shear_bound/maJ:.3f} maJ per transition",
        f"tau from f·Q = {FQ_DIAMOND_PRASE:.1e} Hz: {r.tau_from_fq_low:.1e}-{r.tau_from_fq:.1e} s (book tau_relax {TAU_RELAX_BOOK:.0e} s)",
        f"omega·tau at 5 GHz: book {r.omega_tau_book:.1e}, f·Q-implied {r.omega_tau_fq:.2f}; at 10 GHz f·Q-implied {r.omega_tau_fq_10ghz:.2f}  (Akhiezer regime iff << 1; peak loss at 1)",
        f"Eq. 7.53 phonon-viscosity loss: book tau {r.e_pv_book_tau/maJ:.2e} maJ; f·Q tau {r.e_pv_fq_tau/maJ:.2e} maJ",
        f"book switching cycle total (§12.3.8b)         = {r.e_cycle_book/maJ:.2f} maJ",
        f"omitted term as fraction of cycle total: worst case {100*r.added_fraction_worst:.0f}%, f·Q tau {100*r.added_fraction_fq:.1f}%",
    ])


if __name__ == "__main__":
    print(report())
