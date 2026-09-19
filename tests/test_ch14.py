"""Reproduce the §14.2–14.5 numbers, and record the ones that do not reproduce."""
import math
import pytest
from nsaudit import ch14


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


# ---- 14.2 ------------------------------------------------------------------------------------

def test_14_2_1c_surface_energy_9e6():
    assert close(ch14.surface_energy_per_kg(), 9e6, 0.05)          # 8.6e6


def test_14_2_1c_ethene_1e6_is_low_by_2x():
    """(111) bond density × 3 owned faces × 93 kJ/mol per C-C bond gives 2.4e6 J/kg for 1 nm cubes;
    the book's '~1e6' corresponds to ~23 bonds per cube. Either way it is the 5e5 'estimate used
    here' that carries forward, and that rests on the recovery hypothesis, not on this number."""
    assert close(ch14.ethene_polymerisation_per_kg(), 2.4e6, 0.05)


def test_14_2_2a_scaled_manipulator():
    """10 cm arm scaled from 100 nm: '~10 nm under terrestrial gravity', 'lowest resonant frequency
    > 1e4 Hz'. A diamond cantilever with L/t = 10 sags 50 nm and rings at 2.7 kHz; L/t = 5 gives
    12 nm and 5.4 kHz. Order-of-magnitude statements; the > 1e4 Hz needs L/t < ~4."""
    assert 1e-8 < ch14.cantilever_sag(0.1, 0.02) < 5e-8
    assert ch14.cantilever_f0(0.1, 0.02) > 3e3
    assert ch14.cantilever_f0(0.1, 0.03) > 1e4 * 0.8


def test_14_2_2b_strain_falloff():
    assert close(0.2e-9 * (0.2 / 2)**2, 0.002e-9, 1e-9)


# ---- 14.3 ------------------------------------------------------------------------------------

def test_14_3_1_serial_assembly_exceeds_age_of_universe():
    assert 1e25 / 1e6 > 4.4e17


def test_14_3_1_construction_times():
    assert 3e7 < ch14.construction_time() < 3e8
    assert 300 < ch14.construction_time(unit_volume=1e-24) < 3000


def test_14_3_3_lifetime_numbers():
    assert close(ch14.p_unit_10yr(2e-18), 0.99, 0.002)
    assert close(ch14.p_fail_from_steps(), 0.003, 0.06)
    p = ch14.p_syst(0.99, 10, 1e15)
    assert 1 - p < 2e-5


# ---- 14.4 ------------------------------------------------------------------------------------

def test_14_4_4_volume_omits_the_stage_1_mill_mass():
    """§14.4.4: 'applying an estimated mean density [100 kg/m^3] to the tabulated masses' of the
    input-ordering, reagent-preparation and mill stages 'yields a volume of ~1.8e-4 m^3'. The
    tabulated masses sum to ~0.09 kg -> 9e-4 m^3; 1.8e-4 corresponds to 0.018 kg, i.e. the
    0.06 kg stage-1 mill entry (the largest in the table) is omitted. Low impact: the 0.05 m^3
    total is set by the manipulator workspaces."""
    assert close(ch14.early_stage_mass(), 0.09, 0.05)
    assert close(ch14.early_stage_volume(), 9e-4, 0.05)
    assert close((0.002 + 0.006 + 0.01) / 100, 1.8e-4, 0.01)
    assert ch14.total_mechanism_mass() < 0.12


def test_table_14_1_masses_consistent():
    for level in ("input ordering", "reagent prep", "stage 1 mill"):
        assert close(ch14.table_mass_from_units(level), ch14.TABLE_14_1[level][3], 0.01), level
    assert ch14.table_mass_from_units("stage 2 mill") < 0.01
    assert ch14.table_mass_from_units("stage 3 mill") < 0.01


def test_14_4_8_computation_term():
    assert close(ch14.computation_per_kg(), 1e5, 1e-9)


def test_14_4_8_dissipation_itemised_vs_used():
    """Itemised: 1.5e6 (13.3.7) + 5e5 (14.2.1c) + 1e5 (computation) = 2.1e6 J/kg. The text carries
    forward '~3.1e6 J/kg ... (see preceding paragraphs)'. The extra 1e6 J/kg is not itemised."""
    assert close(ch14.dissipation_itemised(), 2.1e6, 1e-9)
    assert close(ch14.DISSIPATION_USED - ch14.dissipation_itemised(), 1.0e6, 1e-9)


def test_14_4_8_acetone_thermochemistry():
    """ΔH: -604 kJ per mol acetone -> 1.68e7 J/kg diamond (book 1.7e7). Entropy: with liquid
    acetone, O2 and liquid water counted and product entropy zero, 8.2e3 J/kg K (book 5.7e3);
    the book's figure equals the acetone term alone (200 J/mol K / 0.036 kg). Not resolvable
    from the text."""
    assert close(ch14.acetone_to_diamond_enthalpy_per_kg(), 1.7e7, 0.03)
    dS = ch14.acetone_to_diamond_entropy_per_kg_K()
    assert 7e3 < dS < 9e3
    assert close(200.4 / (3 * 0.012011), 5.6e3, 0.02)


def test_14_4_8_budget_chain():
    assert close(ch14.free_energy_available(), 1.5e7, 0.02)
    assert close(ch14.surplus_work(), 1.2e7, 0.02)
    assert close(ch14.waste_heat_per_kg(), 4.8e6, 0.01)
    assert close(ch14.waste_power(), 1.33e3, 0.01)          # §14.4.8 says 1.3 kW; §14.7 says 1.1 kW
    assert ch14.air_cooling_capacity() > 1.33e3


def test_14_4_9_information():
    assert close(1e15 * 100, 1e17, 1e-9)
    assert close(1e6 * 1e17 / 1e28, 1e-5, 1e-9)


# ---- 14.5 ------------------------------------------------------------------------------------

def test_14_5_5b_specific_strength_ratios():
    """Diamond 50 GPa / 3500 vs AISI 9255 hardest temper (~2.1 GPa, 7850) and 7178-T6 (~540 MPa, 2830):
    ~53 and ~75 (book 55, 75). E/rho: 12 (book 12) and ~12 (book 15)."""
    d = 50e9 / 3500
    assert close(d / (2.1e9 / 7850), 55, 0.06)
    assert close(d / (540e6 / 2830), 75, 0.03)
    assert close((1050e9 / 3500) / (200e9 / 7850), 12, 0.05)
    assert close((1050e9 / 3500) / (71e9 / 2830), 12, 0.05)     # not 15


def test_14_5_5f_butane_storage():
    """Butane combustion -2877 kJ/mol (HHV): 5.0e7 J/kg butane, 1.1e7 J/kg of reactants (book 4e7, 9e6:
    consistent with the LHV -2657 kJ/mol: 4.6e7 and 1.0e7)."""
    assert close(2657e3 / 0.058, 4.6e7, 0.02)
    assert close(2657e3 / (0.058 + 6.5 * 0.032), 1.0e7, 0.02)


def test_14_5_6g_capital_cost():
    c, r = 1.0, 0.1
    assert close(c / (1 - r * 1.0), 1.11, 0.01)
    assert close(c / (1 - r * 1e-4), 1.0, 1e-4)
