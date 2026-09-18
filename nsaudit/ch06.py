"""Chapter 6: transition state theory, placement errors, thermomechanical damage, radiation
(Eqs. 6.1–6.59). SI throughout."""
import math

from . import K_B

HBAR = 1.054571817e-34
E_CHARGE = 1.602176634e-19
EPS0 = 8.8541878128e-12
H_PLANCK = 2 * math.pi * HBAR
C_LIGHT = 299792458.0
MAJ = 1e-21
AJ = 1e-18
YEAR = 3.15576e7


# ---- 6.2 TST -----------------------------------------------------------------------------------

def tst_prefactor(T) -> float:
    """kT / (2 pi hbar): 6.25e12 /s at 300 K."""
    return K_B * T / (2 * math.pi * HBAR)


def tst_rate(T, dV, q_ratio=1.0, gamma=1.0) -> float:
    """Eq. 6.1 / 6.16: Gamma (kT/2 pi hbar) (q_trans/q_1) exp(-dV/kT)."""
    return gamma * tst_prefactor(T) * q_ratio * math.exp(-dV / (K_B * T))


def barrier_for_rate(T, k, q_ratio=1.0) -> float:
    """Invert Eq. 6.1: dV = kT ln(q_ratio kT / (2 pi hbar k))."""
    return K_B * T * math.log(q_ratio * tst_prefactor(T) / k)


def v_mean_probability_gas(T) -> float:
    """Eq. 6.3 (mass-weighted): sqrt(kT / 2 pi)."""
    return math.sqrt(K_B * T / (2 * math.pi))


def effective_width(T, k_s) -> float:
    """Eq. 6.5: sqrt(2 pi kT / k_s)."""
    return math.sqrt(2 * math.pi * K_B * T / k_s)


def effective_volume(T, freqs) -> float:
    """Eq. 6.7: (kT/2 pi)^{N/2} prod 1/f_i, in mass-weighted coordinates."""
    N = len(freqs)
    v = (K_B * T / (2 * math.pi))**(N / 2)
    for f in freqs:
        v /= f
    return v


def q_classical(omega, T) -> float:
    """Eq. 6.9: kT / hbar omega."""
    return K_B * T / (HBAR * omega)


def q_quantum(omega, T, zero_at_minimum=True) -> float:
    """Eq. 6.12 (zero at well minimum) or Eq. 6.11 (zero at ground state)."""
    x = HBAR * omega / (K_B * T)
    q = 1 / (1 - math.exp(-x))
    return q * math.exp(-x / 2) if zero_at_minimum else q


def wigner_tunneling(omega_rc, T) -> float:
    """Eq. 6.14: 1 + (1/24)|hbar omega_rc / kT|^2."""
    return 1 + (HBAR * omega_rc / (K_B * T))**2 / 24


def wkb_transmittance(V, E, m_eff, x0, x1, n=2000) -> float:
    """Eq. 6.17 with midpoint quadrature over [x0, x1] where V(x) > E."""
    h = (x1 - x0) / n
    s = 0.0
    for i in range(n):
        x = x0 + (i + 0.5) * h
        s += math.sqrt(max(0.0, 2 * m_eff * (V(x) - E))) / HBAR
    return math.exp(-2 * s * h)


# ---- 6.3 placement errors ------------------------------------------------------------------------

def sinusoidal_well(x, t, k_s, d_err, A) -> float:
    """Eq. 6.21: (1/2) k_s x^2 + [1 - cos(2 pi x / d_err)] A t."""
    return 0.5 * k_s * x * x + (1 - math.cos(2 * math.pi * x / d_err)) * A * t


def p_err_total_equilibrium(T, k_s, d_err, n_max=200) -> float:
    """Eq. 6.22: 2 sum_{n>=1} exp(-k_s (n d)^2 / 2kT) / sum_{all n} ..."""
    a = k_s * d_err**2 / (2 * K_B * T)
    tail = sum(math.exp(-a * n * n) for n in range(1, n_max))
    return 2 * tail / (1 + 2 * tail)


def p_err_instantaneous(T, k_s, d_err) -> float:
    """Eq. 6.23: probability mass of the harmonic Gaussian beyond |x| = d_err/2."""
    sigma = math.sqrt(K_B * T / k_s)
    return math.erfc(d_err / 2 / (sigma * math.sqrt(2)))


def t_crit_first_barrier(k_s, d_err, A) -> float:
    """Time at which Eq. 6.21 first develops a local maximum: V' = V'' = 0 simultaneously gives
    u = tan u (u = 4.4934) and A t = k_s d^2 / (4 pi^2 |cos u|) = 0.1166 k_s d^2 / A.

    The printed Eq. 6.24 says t_crit = 0.2332 d_err^2 / A: twice this coefficient and with no
    k_s, so it is dimensionally a time only if k_s is taken as 1 N/m, and it matches a sinusoid
    of amplitude A t / 2 rather than the A t of Eq. 6.21 as printed."""
    u = 4.493409457909064
    return k_s * d_err**2 / (4 * math.pi**2 * abs(math.cos(u)) * A)


# ---- 6.4 thermomechanical damage -----------------------------------------------------------------

def q_long(k_s, mu, T) -> float:
    """Eq. 6.29: longitudinal-vibration partition function of a bond (zero at the minimum)."""
    x = HBAR * math.sqrt(k_s / mu) / (K_B * T)
    return math.exp(-x) / (1 - math.exp(-x))


def k_cleave_thermal(T, dV, k_s=None, mu=None) -> float:
    """Eq. 6.28: (kT/2 pi hbar)(1/q_long) exp(-dV/kT); q_long = 1 if k_s, mu omitted."""
    q = 1.0 if k_s is None else q_long(k_s, mu, T)
    return tst_prefactor(T) / q * math.exp(-dV / (K_B * T))


def barrier_for_stressed_morse(D_e, beta, F) -> float:
    """Eq. 6.34 (Kauzmann & Eyring 1940): barrier of a Morse bond under constant force F."""
    s = math.sqrt(1 - 2 * F / (beta * D_e))
    return D_e * s + F / beta * math.log((1 - s) / (1 + s))


def omega_well_stressed(D_e, beta, mu, F) -> float:
    """Eq. 6.36."""
    r = math.sqrt(beta**2 - 2 * beta * F / D_e)
    return math.sqrt(D_e * beta / mu * (beta - 2 * F / D_e + r))


def omega_rc_stressed(D_e, beta, mu, F) -> float:
    """Eq. 6.37 (magnitude of the imaginary barrier-top frequency)."""
    r = math.sqrt(beta**2 - 2 * beta * F / D_e)
    return math.sqrt(D_e * beta / mu * abs(beta - 2 * F / D_e - r))


def q_stressed(omega, T) -> float:
    """Eq. 6.35: exp(-hbar omega/kT)[1 - exp(-hbar omega/kT)]^-1."""
    x = HBAR * omega / (K_B * T)
    return math.exp(-x) / (1 - math.exp(-x))


def tau_cleave_stressed(T, D_e, beta, mu, F) -> float:
    """§6.4.4a: 1/k with k = Gamma* (kT/2 pi hbar) (1/q) exp(-dV/kT), dV from Eq. 6.34, q from
    Eq. 6.35-6.36, Gamma* from Eq. 6.14 with Eq. 6.37. The 1-D quantum TST of the text."""
    dV = barrier_for_stressed_morse(D_e, beta, F)
    om = omega_well_stressed(D_e, beta, mu, F)
    om_rc = omega_rc_stressed(D_e, beta, mu, F)
    k = wigner_tunneling(om_rc, T) * tst_prefactor(T) / q_stressed(om, T) * math.exp(-dV / (K_B * T))
    return 1 / k


def critical_force(D_e, beta) -> float:
    """Force at which the Morse barrier vanishes: beta D_e / 2."""
    return beta * D_e / 2


def force_for_lifetime(T, D_e, beta, mu, tau_target=1e20) -> float:
    """Largest F with tau_cleave_stressed >= tau_target (bisection)."""
    lo, hi = 0.0, critical_force(D_e, beta) * 0.999
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if tau_cleave_stressed(T, D_e, beta, mu, mid) >= tau_target:
            lo = mid
        else:
            hi = mid
    return lo


def ion_pair_separation_energy(r1, r2, eps_r=1.0) -> float:
    """§6.4.5a: e^2/(4 pi eps0 eps_r) (1/r1 - 1/r2)."""
    return E_CHARGE**2 / (4 * math.pi * EPS0 * eps_r) * (1 / r1 - 1 / r2)


def rate_at_T2_from_T1(k1, T1, T2) -> float:
    """§6.4.5b: scale a rate between temperatures with Eq. 6.28 at constant partition ratio."""
    dV = barrier_for_rate(T1, k1)
    return tst_rate(T2, dV)


def photon_wavelength_for_energy(E) -> float:
    return H_PLANCK * C_LIGHT / E


# ---- 6.5 shielding --------------------------------------------------------------------------------

def al_transmittance(d, lam, n, k, n1=1.5, n2=1.5) -> float:
    """Eq. 6.52 single-path transmittance of a metal layer of thickness d."""
    pre = 16 * n1 * n2 * (n * n + k * k) / (((n + n1)**2 + k * k) * ((n + n2)**2 + k * k))
    return pre * math.exp(-4 * math.pi * k * d / lam)


AL_UV = {120e-9: (0.057, 1.15), 160e-9: (0.080, 1.73), 200e-9: (0.110, 2.20),
         320e-9: (0.280, 3.56), 400e-9: (0.400, 4.45)}   # Table 6.3 (Gray 1972)


def al_thickness_for_transmittance(T_target, lam) -> float:
    n, k = AL_UV[lam]
    pre = 16 * 1.5 * 1.5 * (n * n + k * k) / (((n + 1.5)**2 + k * k) * ((n + 1.5)**2 + k * k))
    return math.log(pre / T_target) * lam / (4 * math.pi * k)


# ---- 6.6, 6.7 radiation and lifetimes ---------------------------------------------------------------

RAD = 1e-2            # J/kg
HIT_ENERGY = 10.6e-18  # J per inactivating hit (Kepner & Macey 1968)


def hits_per_kg_rad() -> float:
    return RAD / HIT_ENERGY


def p_functional(D_rad, m_kg) -> float:
    """Eq. 6.53: exp(-1e15 D m)."""
    return math.exp(-1e15 * D_rad * m_kg)


def p_functional_track(D_rad, m_kg, rho) -> float:
    """Eq. 6.54."""
    a = 1e15 * D_rad * m_kg
    b = 1e11 * D_rad * (m_kg / rho)**(2 / 3)
    return math.exp(-1 / (1 / a + 1 / b))


def p_system_redundant(D_rad, m_kg, n, N) -> float:
    """Eq. 6.58: {1 - [1 - exp(-1e15 D m)]^n}^N."""
    p_fail = 1 - p_functional(D_rad, m_kg)
    return (1 - p_fail**n)**N


def p_system_redundant_approx(D_rad, m_kg, n, N) -> float:
    """Eq. 6.59."""
    p_fail = 1 - p_functional(D_rad, m_kg)
    return math.exp(-N * p_fail**n)
