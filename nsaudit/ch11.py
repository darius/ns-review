"""Chapter 11 (partial: 11.2-11.5, 11.7): measurement, drives, seals and pumps, cooling, motors.

Reproduces the chapter's worked numbers, and checks the two claims Ch. 14 leans on: convective
cooling capacity (11.5.3) against the heat densities of the 14.4.8 scenarios, and electrostatic
power conversion (11.7) as "negligible mass and volume". SI throughout.
"""
import math

from . import ch06, ch10

K_B = 1.380649e-23
T300 = 300.0
KT = K_B * T300
E_CHARGE = 1.602176634e-19
EPS0 = 8.8541878128e-12
M_E = 9.1093837015e-31
MAJ = 1e-21


# ---- 11.2 measurement --------------------------------------------------------------------------

def force_discrimination_error(ell=1e-9, dF=1e-9, T=T300) -> float:
    """Eq. 11.1 (full form). Book: 6e-27 at 1 nm, 1 nN."""
    a = math.exp(-ell * dF / (4 * K_B * T))
    b = math.exp(-ell * dF / (2 * K_B * T))
    return (a - b) / (1 - b)


def shape_discrimination_gaussian(dx=0.1e-9, k=50.0, T=T300) -> float:
    """11.2.3 by a thermal-Gaussian model with the threshold midway: one-sided tail beyond dx/2
    at σ = √(kT/k). (Book gives ~1e-5 from an unstated model.)"""
    sigma = math.sqrt(K_B * T / k)
    return 0.5 * math.erfc(dx / 2 / (sigma * math.sqrt(2)))


def iterated_measurements_needed(p_single, p_target=1e-15) -> int:
    """11.2.4: a ±1 counter over n measurements (random walk with bias 1-2p) errs if more than
    half the steps err; Chernoff-style bound (4p(1-p))^(n/2)."""
    n = 1
    while (4 * p_single * (1 - p_single))**(n / 2) > p_target:
        n += 1
    return n


# ---- 11.3.2 toroidal worm drive ------------------------------------------------------------------

def torus_spatial_frequency(minor_diameter=2e-9, n_seg=50) -> float:
    """Period 2π/N_seg in the inverting coordinate, measured at the sliding interface
    (circumference π d): N_seg / (π d)... the book's ~8 nm^-1 matches N_seg / (2π r) with r = d/2."""
    return n_seg / (math.pi * minor_diameter)


# ---- 11.4 fluids and seals ------------------------------------------------------------------------

def stokes_speed(F=1e-9, r=100e-9, eta=1e-3) -> float:
    """Eq. 11.3: v = F / 6π r η. Book: ~0.5 m/s."""
    return F / (6 * math.pi * r * eta)


def reynolds(r, rho, v, eta) -> float:
    """Eq. 11.2."""
    return r * rho * v / eta


def poiseuille_flow(r=100e-9, dp=1e6, ell=1000e-9, eta=1e-3) -> float:
    """Eq. 11.4: π r⁴ Δp / 8 ℓ η. Book: ~4e-14 m^3/s, mean speed 1.25 m/s."""
    return math.pi * r**4 * dp / (8 * ell * eta)


def seal_leak_rate_per_length(E=170 * MAJ, k=150.0, n=1e20, m=4.0026e-3 / 6.02214076e23, T=T300) -> float:
    """11.4.2a: aperture of width (Eq. 6.5 effective width) × Boltzmann factor, effusion flux
    n v̄/4. Book: ~1e-15 atoms per nm per s (He, 170 maJ, 150 N/m)."""
    width = ch06.effective_width(T, k) * math.exp(-E / (K_B * T))
    v_mean = math.sqrt(8 * K_B * T / (math.pi * m))
    return n * v_mean / 4 * width          # per metre per second


# ---- 11.5 cooling ------------------------------------------------------------------------------------

ICE_LATENT_VOL = 334e3 * 917.0     # J/m^3 of ice (CRC)


def suspension_viscosity_ratio(f_vol=0.4) -> float:
    """Eq. 11.7: (1 - f)^-2.5. Book: ~3.6 at 0.4."""
    return (1 - f_vol)**-2.5


def slurry_heat_per_volume(f_vol=0.4) -> float:
    """11.5.2: ~1.2e8 J/m^3 of coolant at 40% encapsulated ice."""
    return f_vol * ICE_LATENT_VOL


def cooling_pump_fraction(power=1e5, dp=20e6, f_vol=0.4) -> float:
    """11.5.3: pumping power Δp Q with Q = P / (heat per coolant volume); as a fraction of the
    heat removed. ~0.17 for the 1e5 W, 20 MPa design."""
    Q = power / slurry_heat_per_volume(f_vol)
    return dp * Q / power


def conduction_rise(q_vol, distance, k_thermal) -> float:
    """Temperature rise ~ q L² / 2k across the distance to the nearest coolant tube."""
    return q_vol * distance**2 / (2 * k_thermal)


# ---- 11.7 electrostatic motors --------------------------------------------------------------------

def rim_charge_density(E_field=0.2e9) -> float:
    """11.7.1: ε0 E. Book: 0.0018 C/m^2 at 0.2 V/nm."""
    return EPS0 * E_field


def electrode_charge(d=3e-9, length=20e-9, E_field=0.2e9) -> float:
    """11.7.1: ~3.3e-19 C (~2 e) on a 3 nm × 20 nm cylinder."""
    return rim_charge_density(E_field) * math.pi * d * length


def motor_current(rim_speed=1000.0, pitch=6e-9, **kw) -> float:
    """11.7.3: 2 × rim speed × charge per length (electrodes at 6 nm pitch). Book: ~110 nA."""
    return 2 * rim_speed * electrode_charge(**kw) / pitch


def motor_power(volts=10.0, **kw) -> float:
    return motor_current(**kw) * volts


def motor_volume(r=50e-9, t=25e-9) -> float:
    """11.7.3: 'a motor radius of 50 nm is generous'; thickness 25 nm -> ~2e-22 m^3."""
    return math.pi * r**2 * t


def lead_loss(current=None, j=1e-9 / 1e-18, length=390e-9, rho=2.7e-8) -> float:
    """11.7.4a: two leads, each one motor diameter long, at 1 nA/nm^2. Book: ~200 Ω, ~2.4 pW."""
    I = motor_current() if current is None else current
    R = 2 * rho * length / (I / j)
    return I * I * R


def tunnel_loss(current=None, r_contact=1e4, contacts_per_dee=80) -> float:
    """11.7.4b: contacts in parallel in each of two dees. Book: < 250 Ω, < 3 pW."""
    I = motor_current() if current is None else current
    return I * I * 2 * r_contact / contacts_per_dee


def bearing_loss(k_s=500.0, r_eff=10e-9, l=20e-9, v=50.0, R=10, dk=0.4) -> float:
    """11.7.4c: Eq. 10.27 on the axle bearing. Book: ~1.3 pW."""
    return ch10.p_drag_total(k_s, l, r_eff, R, dk, v)


def electron_contact_energy(v=1000.0) -> float:
    """11.7.4d: ½ m_e v² ≈ 5e-25 J per electron transfer."""
    return 0.5 * M_E * v**2
