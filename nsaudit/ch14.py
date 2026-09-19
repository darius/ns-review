"""Chapter 14: the exemplar manufacturing system's budgets (§14.2–14.5). SI throughout.

The point of this module is the energy budget of §14.4.8 and the Table 14.1 bookkeeping, since
everything else in the chapter is architecture. Thermochemistry uses standard tabulated values
(NIST/CRC) named in the docstrings; the book cites none for §14.4.8.
"""
import math

from . import ch06

YEAR = 3.15576e7
DIAMOND_RHO = 3500.0
BOND_DENSITY_111 = 1.8e19   # bonds/m^2, §6.4.4c
N_A = 6.02214076e23


# ---- 14.2.1c block-assembly energy ----------------------------------------------------------------

def surface_energy_per_kg(gamma=5.0, edge=1e-9, rho=DIAMOND_RHO, faces=6) -> float:
    """§14.2.1c: if joining dissipated the full surface energy of diamond (~5 J/m^2, Field 1979),
    1 nm cubes would cost gamma × 6 a^2 / (rho a^3) ≈ 9e6 J/kg."""
    return gamma * faces * edge**2 / (rho * edge**3)


def ethene_polymerisation_per_kg(dH_bond=93e3, edge=1e-9, rho=DIAMOND_RHO, faces_per_cube=3) -> float:
    """§14.2.1c: 'if adhesive interfaces were designed such that the exoergicity of C-C bond
    formation matches that in the polymerization of ethene' (ΔH ≈ -93 kJ/mol per C-C bond
    formed, NIST), assembling 1 nm cubes with (111)-density bonds across 3 owned faces gives
    ~1e6 J/kg."""
    bonds = BOND_DENSITY_111 * faces_per_cube * edge**2
    return bonds * dH_bond / N_A / (rho * edge**3)


# ---- 14.4.8 energy budget -------------------------------------------------------------------------

MILL_DISSIPATION = 1.5e6          # J/kg, §13.3.7 (imported)
BLOCK_ASSEMBLY = 5e5              # J/kg, §14.2.1c
INSTR_PER_BLOCK = 1e6
J_PER_INSTR = 1e-16               # §12.7.4 (imported): 74 aJ per clock ~ 1e-16
BLOCKS_PER_KG = 1e15              # cubic-micron blocks at 1000 kg/m^3


def computation_per_kg(instr_per_block=INSTR_PER_BLOCK, j_per_instr=J_PER_INSTR, blocks=BLOCKS_PER_KG) -> float:
    """§14.4.8: 1e6 instr/block × 1e-16 J × 1e15 blocks/kg = 1e5 J/kg."""
    return instr_per_block * j_per_instr * blocks


def dissipation_itemised() -> float:
    """Sum of the three itemised terms: 1.5e6 + 5e5 + 1e5 = 2.1e6 J/kg. The text then uses
    '~3.1e6 J/kg of free energy dissipated (see preceding paragraphs)'; the extra 1e6 is not
    itemised."""
    return MILL_DISSIPATION + BLOCK_ASSEMBLY + computation_per_kg()


DISSIPATION_USED = 3.1e6          # J/kg, the figure the text carries forward


def acetone_to_diamond_enthalpy_per_kg(dHf_acetone_l=-248.4e3, dHf_water_l=-285.8e3, dHf_diamond=1.9e3) -> float:
    """C3H6O(l) + 1.5 O2 -> 3 C(diamond) + 3 H2O(l): -ΔH per kg of diamond (NIST values, J/mol).
    Book: 'liberates a total energy equaling ~1.7e7 J/kg of useful output'."""
    dH = 3 * dHf_water_l + 3 * dHf_diamond - dHf_acetone_l
    return -dH / (3 * 0.012011)


def acetone_to_diamond_entropy_per_kg_K(S_acetone_l=200.4, S_O2=205.2, S_water_l=69.9, S_diamond=2.4, product_zero=True) -> float:
    """Local entropy decrease per kg of diamond, reactants (acetone l + 1.5 O2) minus products
    (3 H2O l + 3 C). With the book's 'approximating the entropy of the product object as zero'
    the diamond term drops; whether water and O2 are 'local' is the ambiguity. Book: ~5.7e3."""
    S_react = S_acetone_l + 1.5 * S_O2
    S_prod = 3 * S_water_l + (0 if product_zero else 3 * S_diamond)
    return (S_react - S_prod) / (3 * 0.012011)


def free_energy_available(dH=1.7e7, dS=5.7e3, T=300.0) -> float:
    """§14.4.8: ΔG ≈ 1.7e7 - 300 × 5.7e3 = 1.5e7 J/kg."""
    return dH - T * dS


def surplus_work(dG=1.5e7, dissipated=DISSIPATION_USED) -> float:
    """§14.4.8: ~1.2e7 J/kg delivered as electrical energy."""
    return dG - dissipated


def waste_heat_per_kg(dissipated=DISSIPATION_USED, dS=5.7e3, T=300.0) -> float:
    """§14.4.8: dissipation + T ΔS = 3.1e6 + 1.7e6 = 4.8e6 J/kg."""
    return dissipated + T * dS


def waste_power(kg_per_hour=1.0, **kw) -> float:
    """§14.4.8: 1 kg/hr -> ~1.3 kW (§14.7 says ~1.1 kW)."""
    return waste_heat_per_kg(**kw) * kg_per_hour / 3600


def air_cooling_capacity(flow_m3_s=0.1, dT=15.0, rho_cp=1.2 * 1005) -> float:
    return flow_m3_s * rho_cp * dT


# ---- Table 14.1 / 14.4.4 bookkeeping ----------------------------------------------------------------

TABLE_14_1 = {   # level: (sets, units per set, unit radiation-sensitive mass kg or None, stated total mass kg)
    "input ordering": (1, 1e17, 0.02e-18, 0.002),
    "reagent prep": (1, 1e17, 0.06e-18, 0.006),
    "stage 1 mill": (1e15, 100, 0.60e-18, 0.06),
    "stage 2 mill": (1e13, 100, 0.60e-18, 0.01),
    "stage 3 mill": (1e11, 100, 0.50e-18, 0.01),
    "stage 4 mill": (1e9, 100, None, 0.001),
    "stage 5 mill": (1e6, 100, None, 0.001),
    "stage 1 manip": (1e9, 2, None, 0.001),
    "stage 2 manip": (1e4, 2, None, 0.001),
    "stage 3 manip": (1, 2, None, 0.020),
}


def table_mass_from_units(level) -> float:
    sets, units, m, _ = TABLE_14_1[level]
    return sets * units * m


def early_stage_mass() -> float:
    """§14.4.4: 'input ordering, reagent preparation, and mill mechanisms' masses summed from Table 14.1."""
    return sum(v[3] for k, v in TABLE_14_1.items() if "manip" not in k)


def early_stage_volume(density=100.0) -> float:
    """§14.4.4 divides the tabulated masses by 100 kg/m^3 and gets ~1.8e-4 m^3."""
    return early_stage_mass() / density


def total_mechanism_mass() -> float:
    return sum(v[3] for v in TABLE_14_1.values())


# ---- 14.3.3 / 14.4.5 lifetimes ----------------------------------------------------------------------

def p_unit_10yr(m_kg, years=10.0, rad_per_year=0.5) -> float:
    """Eq. 6.53 over `years` of background: exp(-1e15 D m)."""
    return ch06.p_functional(rad_per_year * years, m_kg)


def p_fail_from_steps(step_fail=1e-15, hz=1e4, years=10.0) -> float:
    """§14.3.3: a step with failure rate 1e-15 at 1e4 /s contributes ~0.003 over 10 years."""
    return step_fail * hz * years * YEAR


def p_syst(p_unit, n_unit, n_set) -> float:
    """Eq. 14.1."""
    return (1 - (1 - p_unit)**n_unit)**n_set


# ---- 14.2.2a, 14.3.1 scaling ---------------------------------------------------------------------

def cantilever_sag(L, t, rho=DIAMOND_RHO, E=1e12, g=9.81) -> float:
    """Uniform cantilever of length L, thickness t under its own weight: 3 rho g L^4 / (2 E t^2)."""
    return 1.5 * rho * g * L**4 / (E * t**2)


def cantilever_f0(L, t, rho=DIAMOND_RHO, E=1e12) -> float:
    """First bending mode of a rectangular cantilever: 0.1615 (t/L^2) sqrt(E/rho)."""
    return 0.1615 * t / L**2 * math.sqrt(E / rho)


def construction_time(thickness=0.1, footprint=(100e-9)**2, rate=1e6, unit_volume=1e-29) -> float:
    """§14.3.1a: column volume / (unit volume × rate). Moiety volume ~1e-29 m^3 gives ~1e8 s;
    10 nm blocks (1e-24 m^3) give 1e3 s."""
    return thickness * footprint / (unit_volume * rate)
