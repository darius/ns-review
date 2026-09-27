"""Chapter 8 (partial: §8.3.3-8.3.4, §8.5): reliability and dissipation of mechanosynthetic steps.

The chapter's role in the audit is to supply what Ch. 13's mill-dissipation mix assumes: the
reliability conditions (8.3.3f, 8.3.4e-g), conditional repetition (8.3.4f), the route to
near-reversible reliable operations (8.5.2b), and the one worked low-dissipation case, tensile
C-C cleavage (8.5.3b-d). SI throughout.
"""
import math

from . import ch06

K_B = 1.380649e-23
T300 = 300.0
KT = K_B * T300
MAJ = 1e-21


def energy_for_ratio(r, T=T300) -> float:
    """kT ln r."""
    return K_B * T * math.log(r)


# ---- 8.3.3a effective concentration --------------------------------------------------------------

def effective_concentration(k_s=20.0, T=T300) -> float:
    """§8.3.3a: 1 / (Eq. 6.5 effective width)^3 at k_s in each of three dimensions (m^-3).
    Book: ~2e4 nm^-3 at 20 N/m."""
    return 1 / ch06.effective_width(T, k_s)**3


# ---- 8.3.3b-c electrostatics and piezochemistry ---------------------------------------------------

def dipole_field_energy(dipole=2.5e-29, field=2e9) -> float:
    """§8.3.3b: ~50 maJ for one electron-charge over one bond length in 2e9 V/m."""
    return dipole * field


def piezo_rate_factor(p, dV_act, T=T300) -> float:
    """Eq. 8.7 at constant ΔV‡: k(p)/k(0) = exp(-p ΔV‡ / kT). 2 GPa, -0.02 nm^3 -> 1.6e4."""
    return math.exp(-p * dV_act / (K_B * T))


def per_bond_load(p, bond_density=1.8e19) -> float:
    """§8.3.3c: 550 GPa over the (111) bond density -> >= 30 nN per bond."""
    return p / bond_density


def instability_load_limit(k_perp=20.0, r1=0.1e-9, r2=0.1e-9) -> float:
    """Eq. 8.9-8.10: F_compr < k_perp (r1 + r2) -> ~4 nN."""
    return k_perp * (r1 + r2)


# ---- 8.3.3f misreactions ----------------------------------------------------------------------------

def elastic_energy(k_s, d) -> float:
    return 0.5 * k_s * d**2


def yield_after_steps(per_step, n) -> float:
    """§8.3.3f: 95% per step -> ~0.6% after 100 steps, ~1e-45 after 2000."""
    return per_step**n


# ---- 8.3.4 reliability ----------------------------------------------------------------------------

def max_barrier_single_trial(t_react=1e-7, f_tst=1e12, p_err=1e-15, T=T300) -> float:
    """Eq. 8.11: ΔV‡ <= kT ln(t f_TST / -ln P_err) -> ~33 maJ."""
    return K_B * T * math.log(t_react * f_tst / -math.log(p_err))


def trials_needed(dF, p_err=1e-15, T=T300) -> tuple[float, int, float]:
    """§8.3.4f: per-trial success at equilibrium with ΔF (negative = exoergic), the number of
    conditional repetitions for failure <= p_err, and the mean trials to success."""
    p_fail = 1 / (1 + math.exp(-dF / (K_B * T)))
    n = math.ceil(math.log(p_err) / math.log(p_fail))
    return 1 - p_fail, n, 1 / (1 - p_fail)


def stability_barrier(t_between=1e-4, f=1e13, p_err=1e-15, T=T300) -> float:
    """§8.3.4g: f exp(-E/kT) t <= p_err -> E >= ~230 maJ."""
    return K_B * T * math.log(f * t_between / p_err)


def instability_rate(E, t_between=1e-4, f=1e13, T=T300) -> float:
    """§8.3.4g: error per reaction at barrier E (~1e-20 at 275 maJ)."""
    return f * math.exp(-E / (K_B * T)) * t_between


# ---- 8.5.3 tensile cleavage ------------------------------------------------------------------------

def barrier_for_rate(rate=1e9, f=1e13, T=T300) -> float:
    """§8.5.3b: transition rate 1e9 /s at f = 1e13 needs barriers <= ~38 maJ."""
    return K_B * T * math.log(f / rate)


def k_sz_estimate(k_mm2=153.0, load_factor=1.05, mm3_factor=1.14) -> float:
    """§8.5.3d: 153 N/m (MM2 cluster fit) × 1.05 (load) × 1.14 (MM3 bending) ≈ 183 N/m."""
    return k_mm2 * load_factor * mm3_factor


def k_struct(k_sz) -> float:
    """§8.5.3d: compliances of the two bonded atoms add: k_sz / 2."""
    return k_sz / 2


# ---- 8.5.4 hydrogen transfer tools --------------------------------------------------------------------

E_CH_ALKYNE = 915 * MAJ      # §8.5.4c
E_CH_DONOR_MAX = 530 * MAJ   # §8.5.4d: donors below ~530 maJ donate reliably to sp3 carbon radicals
E_RELIABLE = 145 * MAJ       # §8.3.3f / 8.3.4e


def abstract_donate_exoergicity(e_abstractor=E_CH_ALKYNE, e_donor=E_CH_DONOR_MAX) -> float:
    """Net exoergicity of moving one H from a donor-grade site, via a workpiece sp3 site, to an
    alkynyl tool: independent of the sp3 C-H energy, = E(abstractor) - E(donor). With the book's
    bounds it is >= 385 maJ per H moved in a single-step (route 1) abstraction-donation pair.
    The implied sp3 C-H energy for reliable donation is >= E_donor + 145 = 675 maJ."""
    return e_abstractor - e_donor


# ---- 8.5.5a stiffness and misreaction ------------------------------------------------------------------

def radical_addition_bias(k_s=6.0, d_alt=0.177e-9, bias=0.1e-9) -> tuple[float, float]:
    """§8.5.5a: biasing the approach by `bias` away from the alternative site raises the favoured
    transition state by ½ k bias² and the alternative's by ½ k (d + bias)². Returns
    (favoured-TS cost, alternative-minus-favoured difference). Book: ~25 and ~200 maJ."""
    fav = elastic_energy(k_s, bias)
    alt = elastic_energy(k_s, d_alt + bias)
    return fav, alt - fav


# ---- 8.5.6 pi-bond torsion ----------------------------------------------------------------------------

def torsion_cycle_gain(bond_weakening=410 * MAJ, exo_each=145 * MAJ, steps=2) -> float:
    """§8.5.6: energy raise of the transferred moiety when steps 1 and 2 must each be exoergic
    by 145 maJ: the torsion weakening less the two exoergicities (>= ~120 maJ at 410)."""
    return bond_weakening - steps * exo_each
