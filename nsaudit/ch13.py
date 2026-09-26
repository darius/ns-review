"""Chapter 13: sorting, mills, manipulators (§13.2–13.4). SI throughout.

Reproduces the chapter's numbers from its stated inputs. The load-bearing ones for Ch. 14 are
the mill dissipation (§13.3.7), the reagent-processing mass (§13.3.5), the fail-stop unit mass
(§13.3.6c), the power-generation figures (§13.3.8) and the arm compliance (§13.4.1e, Table 13.1).
"""
import math

from . import ch06, ch10

K_B = 1.380649e-23
T300 = 300.0
KT = K_B * T300
MAJ = 1e-21
N_A = 6.02214076e23
C_ATOMS_PER_KG = N_A / 12.011e-3     # ~5.0e25; the book's per-kg conversions are carbon atoms


def boltzmann_factor(dE, T=T300) -> float:
    return math.exp(-dE / (K_B * T))


def energy_for_probability(p, T=T300) -> float:
    """kT ln(1/p): the free-energy gap giving occupancy odds p (equilibrium Boltzmann limit)."""
    return K_B * T * math.log(1 / p)


# ---- 13.2.1 modulated receptors ------------------------------------------------------------------

def concentration_work(fraction=1e-2, T=T300) -> float:
    """§13.2.1a: ~20 maJ to deliver a molecule from mole fraction 1e-2 to a pure compartment."""
    return energy_for_probability(fraction, T)


def rotor_viscous_drag(eta=1e-3, area=50e-18, shear_length=2.7e-9, v=0.0027) -> float:
    """§13.2.1e: Couette drag power eta A v^2 / L; ~1e-16 W at the stated values."""
    return eta * area * v**2 / shear_length


def rim_speed(receptor_pitch=2.7e-9, rate=1e6) -> float:
    """§13.2.1e: 1e6 receptor sites/s at 2.7 nm pitch -> 0.0027 m/s."""
    return receptor_pitch * rate


# ---- 13.2.2 cascades ---------------------------------------------------------------------------

def cascade_R(f_rat, alpha_rat) -> float:
    """Eq. 13.5: R = (f_rat alpha_rat)^-1."""
    return 1 / (f_rat * alpha_rat)


def cascade_stages(c0, c_target, R) -> int:
    """Eq. 13.6 inverted: smallest N with c0 R^N <= c_target."""
    return math.ceil(math.log(c_target / c0) / math.log(R) - 1e-12)


# ---- 13.2.3 ordered input ------------------------------------------------------------------------

def binding_potential_energy(p_empty=1e-15, dS_binding=6e-23, T=T300) -> float:
    """§13.2.3b: |ΔF| >= kT ln(1/P_empty) (~143 maJ) plus T ΔS of binding (~18 maJ) -> ~161 maJ."""
    return energy_for_probability(p_empty, T) + T * dS_binding


def molecular_volume(rho_liquid, molar_mass, compression=0.75) -> float:
    """§13.2.3b: volume per molecule at 1-2 GPa ~0.75 of the low-pressure value."""
    return compression * molar_mass / (N_A * rho_liquid)


def pressure_for_increment(dE, v_mol) -> float:
    """§13.2.3b: p V = ΔE."""
    return dE / v_mol


# ---- 13.3.1 reactive encounters ------------------------------------------------------------------

def t_trans_exact(v, r1, r2, delta) -> float:
    """Eq. 13.7, first form."""
    r_red = 1 / (1 / r1 + 1 / r2)
    return (2 / v) * r_red * math.acos(1 - 2 * delta / r_red)


def t_trans_approx(v, r1, r2, delta) -> float:
    """Eq. 13.7, small-delta form 4/v sqrt(delta r_red)."""
    r_red = 1 / (1 / r1 + 1 / r2)
    return (4 / v) * math.sqrt(delta * r_red)


# ---- 13.3.5 size and mass --------------------------------------------------------------------------

DENSITY = 2500.0        # kg/m^3, §13.3.5 standard density
ATOMS_PER_NM3 = 125.0

def roller_pair_volume(r=5e-9, t=2e-9) -> float:
    """§13.3.5a: two discs r = 5 nm, t = 2 nm: ~310 nm^3 (axles not separately counted here)."""
    return 2 * math.pi * r**2 * t


def mechanism_volume(close_packed=True) -> float:
    """§13.3.5c totals: rollers 310 + encounter 64 + cam 80 + belts (1600 or 50) + struts 300 nm^3."""
    belts = 1600e-27 if close_packed else 50e-27
    return 310e-27 + 64e-27 + 80e-27 + belts + 300e-27


def mechanism_mass(close_packed=True) -> float:
    return DENSITY * mechanism_volume(close_packed)


def mechanism_atoms(close_packed=True) -> float:
    return ATOMS_PER_NM3 * mechanism_volume(close_packed) * 1e27


def self_mass_time(system_mass, rate=1e6, moiety_mass=12.011e-3 / N_A) -> float:
    """§13.3.5d: time to deliver the system's own mass at `rate` moieties/s of `moiety_mass`."""
    return system_mass / (rate * moiety_mass)


# ---- 13.3.6 fail-stop unit mass ----------------------------------------------------------------------

def p_unit_fail_10yr(m_kg, rad_per_year=0.5, years=10.0) -> float:
    """§13.3.6c via Eq. 6.53 (the mass term of Eq. 6.54 at this size): 1 - exp(-1e15 D m)."""
    return 1 - ch06.p_functional(rad_per_year * years, m_kg)


# ---- 13.3.7 dissipation --------------------------------------------------------------------------------

def roller_bearing_drag(belt_speed=0.004, roller_r=5e-9, bearing_r=2e-9, bearing_l=2e-9,
                        k_s=1000.0, R=10, dk_over_k=0.4) -> float:
    """§13.3.7a: Eq. 10.27 at the bearing surface speed (belt speed × r_bearing / r_roller),
    'more adverse' Δk_a/k_a = 0.4, R = 10 as in the 10.4.6 sample. Book: ~7e-20 W."""
    v = belt_speed * bearing_r / roller_r
    return ch10.p_drag_total(k_s, bearing_l, bearing_r, R, dk_over_k, v)


def per_kg(e_per_op, ops_per_atom=1.0, atoms_per_kg=C_ATOMS_PER_KG) -> float:
    """Energy per kg of carbon-rich product from energy per operation."""
    return e_per_op * ops_per_atom * atoms_per_kg


def conditional_repetition_modulation(N, bias=5 * MAJ, e_reliable=145 * MAJ) -> float:
    """§13.3.7b: modulation ~(5 + 145/N) maJ."""
    return bias + e_reliable / N


def conditional_repetition_exoergicity(N, p_target=1e-15, T=T300) -> float:
    """§13.3.7b: a simple conditional-repetition process with N tries needs per-try failure
    P with P^N <= p_target, i.e. ΔF = kT ln(1/P) = kT ln(1/p_target) / N (~14 maJ at N = 10)."""
    return energy_for_probability(p_target, T) / N


# ---- 13.3.8 power generation ---------------------------------------------------------------------------

H2O_DH_F = 285.83e3     # J/mol, liquid water, standard enthalpy of formation (NIST)
H2O_DG_F = 237.13e3     # J/mol, liquid water, standard Gibbs energy of formation (NIST)

def per_molecule(j_per_mol) -> float:
    return j_per_mol / N_A


def power_density(e_per_op=475 * MAJ, rate=1e6, mass=None, volume=None) -> tuple[float, float]:
    """§13.3.8: ~8e6 W/kg and ~2e9 W/m^3 for a 10-encounter system (§13.3.5d) at 1e6 /s."""
    mass = mass if mass is not None else 10 * mechanism_mass(True)
    volume = volume if volume is not None else 10 * 2e-23
    P = e_per_op * rate
    return P / mass, P / volume


# ---- 13.4.1 arm compliance (Table 13.1) ---------------------------------------------------------------

def tube_cantilever_compliance(L=100e-9, r_in=11.5e-9, r_out=15e-9, surf=0.1e-9, E=1e12) -> float:
    """Table 13.1 note b: L^3 / (3 E I), I = pi/4 (r2^4 - r1^4) on the structural section
    (0.1 nm surface correction on each face). Book: 13.6 mm/N."""
    r1, r2 = r_in + surf, r_out - surf
    I = math.pi / 4 * (r2**4 - r1**4)
    return L**3 / (3 * E * I)


def ring_rocking_compliance(n_contacts=650, k_contact=10.0) -> float:
    """Rocking of a ring of n axial springs, measured w.r.t. the maximum local stretch δ:
    stretch at angle θ is δ cos θ, so U = ½ δ² Σ k cos²θ = ½ δ² (n k / 2). Book (note c):
    ~0.00003 m/N for 650 contacts at 10 N/m."""
    return 1 / (n_contacts * k_contact / 2)


def ring_torsion_compliance(n_contacts=640, k_contact=10.0, interfaces=2) -> float:
    """Torsion across a threaded torus, w.r.t. the (uniform) local shear: n k per interface,
    interfaces in series. Book (note e): 0.31 mm/N for the two interfaces together."""
    return interfaces / (n_contacts * k_contact)


TABLE_13_1 = {  # source: (magnitude mm/N, multiplier (v2/v1)^2, contribution mm/N) as printed
    "tube bending": (13.60, 1, 13.6),
    "J1 rocking": (0.05, 59, 3.0), "J2 rocking": (0.05, 45, 2.3), "J3 rocking": (0.05, 32, 1.6),
    "J4a rocking": (0.05, 19, 1.0), "J4b rocking": (0.05, 9, 0.5), "J5 rocking": (0.05, 4, 0.2),
    "J6 rocking": (0.07, 3, 0.2),
    "J1 torsion": (0.31, 25, 7.8), "J2 torsion": (0.31, 7, 2.2), "J3 torsion": (0.31, 1, 0.3),
    "J5 torsion": (0.31, 0.5, 0.2), "S1 torsion": (0.11, 25, 2.8),
}
DRIVE_SYSTEM_MM_PER_N = 4.0     # §13.4.1e: drive contributions total <= 0.004 m/N


def table_13_1_total(rocking_mm_per_n=None, tube_mm_per_n=None) -> float:
    """Sum of Table 13.1 contributions plus the drive system, in m/N. Optional overrides replace
    the 0.05 mm/N rocking magnitude (J6 scaled in proportion) or the tube-bending term."""
    total = 0.0
    for k, (mag, mult, contrib) in TABLE_13_1.items():
        if k == "tube bending" and tube_mm_per_n is not None:
            contrib = tube_mm_per_n
        elif "rocking" in k and rocking_mm_per_n is not None:
            contrib = rocking_mm_per_n * (mag / 0.05) * mult
        total += contrib
    return (total + DRIVE_SYSTEM_MM_PER_N) * 1e-3


def scaled_compliance(C, L_from=100e-9, L_to=1.0) -> float:
    """Eq. 2.3 scaling cited in §13.4.1: compliance ∝ 1/L at fixed shape and material."""
    return C * L_from / L_to


def manipulator_self_mass_time(atoms=5e6, rate=1e6, atoms_per_op=1.0) -> float:
    """§13.4.1f: ~5e6 atoms at 1e6 ops/s, ~1 atom per op -> ~5 s."""
    return atoms / (rate * atoms_per_op)


def expected_step_failures(p_step=1e-15, rate=1e6, steps=1, years=10.0) -> float:
    """Expected failed operations in `years` for a device of `steps` encounter mechanisms each
    at `rate` /s. Footnote 34: 1e-15 at 1e4 /s -> MTTF ~3000 years."""
    return p_step * rate * steps * years * ch06.YEAR


def p_step_for_budget(p_budget=0.01, rate=1e6, steps=1, years=10.0) -> float:
    """Per-operation error rate at which step failures stay within `p_budget` in `years`."""
    return p_budget / (rate * steps * years * ch06.YEAR)
