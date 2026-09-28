"""Audit of the §14.4.8 energy budget as a unit: dissipation terms, free energy, surplus, waste heat.

Question: does "~3.1e6 J/kg dissipated ... ~1.2e7 J/kg of surplus ... 1.3 kW of waste heat"
survive when each imported term is carried as an interval set by what its source chapter
actually establishes?

Method: each term is taken from its source module (ch13, ch12, ch14) under three scenarios for
the dominant term, the mill dissipation of §13.3.7, which turns on how reagent-preparation
steps achieve 1e-15 reliability:
  A  near-reversible (8.5.2b well-depth modulation, ~1 maJ per preparation step), as the book
     intends; demonstrated in Ch. 8 only for tensile C-C cleavage (8.5.3b-d, 1.5× margin);
  B  conditional repetition at N = 10 (8.3.4f, 13.3.7b: ~14 maJ per step) with no well-depth
     modulation — the book's own mechanism that does not need 8.5.2b;
  C  single-step reliability (route 1, ~145 maJ per step), the book's "naive" estimate.
Application steps keep the book's ~30 maJ mean in all three. Thermochemistry is the Ch. 14
spot-check version (NIST ΔH, entropy counting acetone, O2 and liquid water).

Terms the book calls negligible are given numbers: sorting (13.2.2c) and manipulators (13.4.1f,
13.4.4). The computation term uses Ch. 12's own per-interlock energies in place of 12.7.4's 0.03
maJ, with the 7.4.2 -> 12.3.4 verdict's +15% worst case. Prase's collective-mode claim on rod
logic is not adjudicated here.
"""
from dataclasses import dataclass

from . import ch12, ch13, ch14
from .ch12 import EX

MAJ = 1e-21
AJ = 1e-18
T = 300.0
PREP_STEPS = 10                   # §13.3.3
APPLICATION_MEAN = 30 * MAJ       # §13.3.7b


# ---- mill term (13.3.7) ---------------------------------------------------------------------------

PREP_PER_STEP = {
    "A": 1 * MAJ,                                           # 8.5.2b near-reversible class
    "B": ch13.conditional_repetition_exoergicity(10),        # 14.3 maJ, simple CR at N = 10
    "C": ch13.energy_for_probability(1e-15),                 # 143 maJ, route (1)
}


def mill_term(scenario) -> float:
    """J/kg: one application at the ~30 maJ mean plus ~10 preparation steps per atom."""
    return ch13.per_kg(APPLICATION_MEAN + PREP_STEPS * PREP_PER_STEP[scenario])


# ---- block assembly (14.2.1c <- 9.7.3) ------------------------------------------------------------

BLOCK = {
    "A": 5e5,                                      # the book's allowance (recovery "almost all")
    "B": ch14.ethene_polymerisation_per_kg(),      # 2.4e6, the book's own ethene-matched recipe
    "C": ch14.surface_energy_per_kg(),             # 8.6e6, no recovery
}


# ---- computation (14.4.8 <- 12.7.4) ----------------------------------------------------------------

REGISTER_TERM = 1e4 * 4.4 * MAJ                   # §12.7.4, per clock
INSTR_PER_BLOCK = 1e6
BLOCKS_PER_KG = 1e15


def energy_per_instruction(interlock_term) -> float:
    """J per instruction (one clock) with a given total interlock term per clock."""
    return interlock_term + REGISTER_TERM


def interlock_terms() -> dict:
    """Per-clock interlock term by the three counts available in Ch. 12 (J):
    book (12.7.4: 1e6 × 0.03 maJ), per-interlock (12.3.8b's cycle / 16), per-rod (1e5 rods ×
    the cycle), each worst case ×1.15 for the 7.4.2 verdict. The cycle uses the exact rod
    vibration (audit_prase_rod_logic: 3.45 maJ, vs the book's 2.17)."""
    from .audit_prase_rod_logic import cycle_with_exact_vibration
    e_cycle = cycle_with_exact_vibration(EX)
    return {
        "book": 1e6 * 0.03 * MAJ,
        "per-interlock": 1e6 * e_cycle / 16 * 1.15,
        "per-rod": 1e5 * e_cycle * 1.15,
    }


def computation_term(interlock_term) -> float:
    return energy_per_instruction(interlock_term) * INSTR_PER_BLOCK * BLOCKS_PER_KG


COMPUTATION = {"A": computation_term(interlock_terms()["per-interlock"]),
               "B": computation_term(interlock_terms()["per-rod"]),
               "C": computation_term(interlock_terms()["per-rod"])}


# ---- terms called negligible -----------------------------------------------------------------------

def sorting_term(per_molecule=0.5 * MAJ + 0.1 * 20 * MAJ, molecules_per_c=1 / 3 + 0.5) -> float:
    """§13.2.2c: ~0.5 maJ drag plus entropy-of-mixing loss ~10% of the ~20 maJ concentration work
    per molecule sorted; acetone (1 per 3 C) and O2 (1.5 per acetone) -> ~0.83 molecules per C."""
    return ch13.per_kg(per_molecule * molecules_per_c)


def manipulator_term(per_motion=100 * MAJ, atoms_per_motion=1000, levels=3) -> float:
    """§13.4.1f: ~100 maJ per motion placing a ~1000-atom cluster (~0.1 maJ/atom); §13.4.4:
    energy per mass delivered is scale-independent; three manipulator levels (Table 14.1)."""
    return ch13.per_kg(per_motion / atoms_per_motion) * levels


# ---- the budget ---------------------------------------------------------------------------------------

DH = ch14.acetone_to_diamond_enthalpy_per_kg()                 # 1.68e7 J/kg
DS = ch14.acetone_to_diamond_entropy_per_kg_K()                # 8.2e3 J/kg K
DG = DH - T * DS                                               # 1.43e7 J/kg


@dataclass(frozen=True)
class Budget:
    mill: float
    block: float
    computation: float
    sorting: float
    manipulators: float

    @property
    def dissipated(self) -> float:
        return self.mill + self.block + self.computation + self.sorting + self.manipulators

    @property
    def surplus(self) -> float:
        return DG - self.dissipated

    @property
    def waste_heat(self) -> float:
        return self.dissipated + T * DS

    def waste_power(self, kg_per_hour=1.0) -> float:
        return self.waste_heat * kg_per_hour / 3600


def budget(scenario) -> Budget:
    return Budget(mill_term(scenario), BLOCK[scenario], COMPUTATION[scenario],
                  sorting_term(), manipulator_term())


BOOK = Budget(1.5e6, 5e5, 1e5, 0.0, 0.0)   # the book's itemised terms (sum 2.1e6; carried as 3.1e6)
AIR_COOLING = ch14.air_cooling_capacity()   # 1.8 kW at 0.1 m^3/s, ΔT = 15 K


def report() -> str:
    lines = [f"ΔH {DH:.3g}  TΔS {T * DS:.3g}  ΔG {DG:.3g} J/kg; air cooling {AIR_COOLING:.0f} W"]
    for s in "ABC":
        b = budget(s)
        lines.append(
            f"{s}: mill {b.mill:.2g} block {b.block:.2g} comp {b.computation:.2g} sort {b.sorting:.2g} "
            f"manip {b.manipulators:.2g} -> dissipated {b.dissipated:.3g}, surplus {b.surplus:.3g}, "
            f"waste {b.waste_power():.0f} W per kg/hr")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())


# ---- where the heat is produced, and whether it can be removed (11.5) ---------------------------

DEMAND = 1e-3 * ch13.C_ATOMS_PER_KG                # moieties/s at ~1 g/s (Table 14.1 note a)
PREP_MASS, STAGE1_MASS = 0.006, 0.06               # kg, Table 14.1
MECH_DENSITY, FILL = 2500.0, 0.1                   # kg/m^3 and filled fraction, 13.3.5
COOLING_CAPACITY = 1e5 / 1e-6                      # W/m^3, 11.5.3 (1 cm slab)


def mechanism_volume(mass: float) -> float:
    return mass / MECH_DENSITY / FILL


def heat_density(scenario: str) -> dict:
    """W/m^3 in the reagent-preparation stage (10 steps per moiety) and in stage 1 mills
    (application at the ~30 maJ mean)."""
    prep = PREP_STEPS * PREP_PER_STEP[scenario] * DEMAND / mechanism_volume(PREP_MASS)
    app = APPLICATION_MEAN * DEMAND / mechanism_volume(STAGE1_MASS)
    return {"prep": prep, "stage1": app}


def air_flow_needed(scenario: str, dT: float = 15.0, rho_cp: float = 1.2 * 1005) -> float:
    """m^3/s of air at ΔT for the scenario's waste heat at ~1 kg/hr (14.4.8's framing)."""
    return budget(scenario).waste_power() / (rho_cp * dT)
