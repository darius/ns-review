"""Chapter 11 (partial): reproduce 11.2-11.5, 11.7 numbers; check 14.4.1's supporting systems."""
from nsaudit import audit_14_4_8_budget as b, ch11

MAJ = 1e-21


def close(x, y, tol):
    return abs(x - y) <= tol * abs(y)


def test_force_discrimination():
    assert close(ch11.force_discrimination_error(), 6e-27, 0.03)


def test_shape_discrimination_and_iteration():
    """11.2.3: a Gaussian reading gives 2e-8 (book ~1e-5, unstated model); 11.2.4 reaches 1e-15
    in 7 iterations from 1e-5, 5 from 2e-8."""
    p = ch11.shape_discrimination_gaussian()
    assert close(p, 2e-8, 0.05)
    assert ch11.iterated_measurements_needed(1e-5) == 7
    assert ch11.iterated_measurements_needed(p) == 5


def test_worm_drive_spatial_frequency():
    assert close(ch11.torus_spatial_frequency() * 1e-9, 8.0, 0.01)


def test_fluid_examples():
    v = ch11.stokes_speed()
    assert close(v, 0.53, 0.01) and close(1e-9 * v, 0.53e-9, 0.01)
    assert close(ch11.reynolds(1e-7, 1000, v, 1e-3), 0.053, 0.01)
    q = ch11.poiseuille_flow()
    assert close(q, 3.9e-14, 0.02) and close(q / (3.14159265 * 1e-14), 1.25, 0.01)


def test_seal_leak():
    """11.4.2a: ~1e-15 He atoms per nm·s (6e-16 computed); > 1e4 years per atom through 1000 nm."""
    rate = ch11.seal_leak_rate_per_length()
    assert close(rate * 1e-9, 6.2e-16, 0.02)
    assert 1 / (rate * 1e-6) / 3.156e7 > 1e4


def test_coolant_and_cooling_design():
    """11.5.2: 3.6x viscosity, 1.2e8 J/m^3; 11.5.3: pumping 16% of the heat at 1e5 W, 20 MPa;
    conduction over 5 µm at 1e11 W/m^3 and 100 W/m·K is ~0.01 K."""
    assert close(ch11.suspension_viscosity_ratio(), 3.6, 0.01)
    assert close(ch11.slurry_heat_per_volume(), 1.2e8, 0.03)
    assert close(ch11.cooling_pump_fraction(), 0.163, 0.01)
    assert ch11.conduction_rise(1e11, 5e-6, 100.0) < 0.02


def test_motor_numbers():
    """11.7: 0.0018 C/m^2, ~2 e, ~110 nA, 1.1 µW, ~2e-22 m^3, > 1e15 W/m^3; losses 2.4, < 3,
    1.3 pW; contact electron energy 5e-25 J (3e-7 of 10 eV)."""
    assert close(ch11.rim_charge_density(), 1.8e-3, 0.02)
    assert close(ch11.electrode_charge() / 1.602e-19, 2.0, 0.05)
    assert close(ch11.motor_current(), 110e-9, 0.02)
    assert close(ch11.motor_power(), 1.1e-6, 0.02)
    assert close(ch11.motor_volume(), 2e-22, 0.02)
    assert ch11.motor_power() / ch11.motor_volume() > 1e15
    assert close(ch11.lead_loss(), 2.4e-12, 0.03)
    assert close(ch11.tunnel_loss(), 3.0e-12, 0.05)
    assert close(ch11.bearing_loss(), 1.3e-12, 0.05)
    assert close(ch11.electron_contact_energy(), 5e-25, 0.1)


def test_cooling_capacity_vs_14_4_8_scenarios():
    """Reagent-prep heat density 21 / 300 / 3000 W/cm^3 in scenarios A / B / C against 11.5.3's
    1e5 W/cm^3: margins ~4800 / 330 / 33. Stage-1 mills ~6 W/cm^3 in all three."""
    for s, prep, margin in (("A", 20.9, 4790), ("B", 299, 335), ("C", 2990, 33.5)):
        h = b.heat_density(s)
        assert close(h["prep"] * 1e-6, prep, 0.02)
        assert close(b.COOLING_CAPACITY / h["prep"], margin, 0.02)
        assert close(h["stage1"] * 1e-6, 6.3, 0.02)


def test_waste_heat_at_design_throughput():
    """At Table 14.1's ~1 g/s (3.6 kg/hr) the book's own 4.8e6 J/kg is 4.8 kW, against 14.4.1's
    '~1 kW cooling system' and 14.4.8's 1.8 kW of air at 0.1 m^3/s, ΔT 15 K (its 1.3 kW is for
    1 kg/hr). Scenarios: 5.4 / 14.1 / 84.8 kW."""
    assert close((3.1e6 + 1.7e6) * 1e-3, 4800, 1e-9)
    for s, kw in (("A", 5.4), ("B", 14.1), ("C", 84.8)):
        x = b.budget(s)
        assert close((x.dissipated + 300 * b.DS) * 1e-3 / 1e3, kw, 0.02)
