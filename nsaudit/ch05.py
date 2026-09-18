"""Chapter 5: positional uncertainty of oscillators and rods (Eqs. 5.4–5.98).

Implements the classical and quantum variances, the discrete-rod exact sum (Eq. 5.37) and the
two engineering approximations (Eqs. 5.43–5.44), the cantilever results (Eqs. 5.53–5.65), the
entropic piston (Eq. 5.74) and the longitudinal-from-transverse bound (Eq. 5.98).
"""
import math

from . import K_B

HBAR = 1.054571817e-34


# ---- 5.3 harmonic oscillator -----------------------------------------------------------------

def var_classical(T, k_s) -> float:
    """Eq. 5.4: sigma^2 = kT / k_s."""
    return K_B * T / k_s


def mean_energy_quantum(omega, T) -> float:
    """Eq. 5.14: hbar omega {1/2 + [exp(hbar omega/kT) - 1]^-1}."""
    x = HBAR * omega / (K_B * T)
    return HBAR * omega * (0.5 + (1 / math.expm1(x) if x < 700 else 0.0))


def var_quantum(k_s, m, T) -> float:
    """Eq. 5.16: sigma^2 = (hbar omega / k_s) {1/2 + [exp(hbar omega/kT) - 1]^-1}, omega = sqrt(k_s/m)."""
    omega = math.sqrt(k_s / m)
    return mean_energy_quantum(omega, T) / k_s


def quantum_to_classical_ratio(k_s, m, T) -> float:
    """Eq. 5.18: sigma^2 / sigma_class^2 = E_mean / kT."""
    return var_quantum(k_s, m, T) / var_classical(T, k_s)


# ---- 5.4 longitudinal rod modes ---------------------------------------------------------------

def omega_0(l, E_l, rho_l) -> float:
    """Eq. 5.20: fundamental of a clamped-free rod, (pi / 2 l) sqrt(E_l / rho_l)."""
    return math.pi / (2 * l) * math.sqrt(E_l / rho_l)


def rod_modal_stiffness(n, l, E_l) -> float:
    """Eq. 5.22: k_n = (E_l / l)(pi^2 / 8)(2n + 1)^2, effective stiffness of mode n at the free end."""
    return E_l / l * math.pi**2 / 8 * (2 * n + 1)**2


def var_rod_longitudinal_classical(T, l, E_l) -> float:
    """Eq. 5.26: kT l / E_l (= kT / k_s of the whole rod)."""
    return K_B * T * l / E_l


def var_rod_exact(l, E_l, rho_l, T, N) -> float:
    """Eq. 5.37 (dispersive discrete rod, N masses), returned in m^2."""
    w0 = omega_0(l, E_l, rho_l)
    a = HBAR * w0 / (K_B * T)
    s = 0.0
    for n in range(N):
        th = (2 * n + 1) / (2 * N + 1)
        num = math.sin(th * math.pi * N)**2 / math.sin(th * math.pi / 2)
        x = 4 * N / math.pi * a * math.sin(th * math.pi / 2)
        s += num * (0.5 + 1 / math.expm1(x))
    return s * 2 / (2 * N + 1) * HBAR / math.sqrt(E_l * rho_l)


def var_rod_approx_5_43(l, E_l, rho_l, T, N) -> float:
    """Eq. 5.43: hbar [0.54 + ln(2N+1)] / (pi sqrt(E_l rho_l)) + kT l / E_l. Conservative."""
    return HBAR * (0.54 + math.log(2 * N + 1)) / (math.pi * math.sqrt(E_l * rho_l)) + K_B * T * l / E_l


def var_rod_approx_5_44(l, E_l, rho_l, T, N) -> float:
    """Eq. 5.44: as 5.43 with the classical term damped by exp[-(0.7 - 0.39/sqrt N) pi hbar v_s / (2 l kT)]."""
    zp = HBAR * (0.54 + math.log(2 * N + 1)) / (math.pi * math.sqrt(E_l * rho_l))
    damp = math.exp(-(0.7 - 0.39 / math.sqrt(N)) * math.pi * HBAR / (2 * l * K_B * T) * math.sqrt(E_l / rho_l))
    return zp + K_B * T * l / E_l * damp


def n_planes(l) -> int:
    """Eq. 5.28: N = 1e10 l, 'a conservatively generous estimate'."""
    return max(1, int(round(1e10 * l)))


# ---- 5.5 transverse (cantilever) ----------------------------------------------------------------

def cantilever_roots(n_roots=8):
    """R_n solving cos R cosh R = -1 (Eq. 5.46), by bisection near (n + 1/2) pi."""
    roots = []
    f = lambda R: math.cos(R) * math.cosh(R) + 1
    for n in range(n_roots):
        lo, hi = (n + 0.5) * math.pi - 0.5, (n + 0.5) * math.pi + 0.5
        if n == 0:
            lo, hi = 1.0, 2.5
        flo = f(lo)
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if (f(mid) > 0) == (flo > 0):
                lo, flo = mid, f(mid)
            else:
                hi = mid
        roots.append(0.5 * (lo + hi))
    return roots


def var_cantilever_bending_classical(T, l, k_b) -> float:
    """Eq. 5.53: kT l^3 / 3 k_b (= kT / k_t,b with k_t,b = 3 k_b / l^3)."""
    return K_B * T * l**3 / (3 * k_b)


def k_b_tube(E, r1, r2) -> float:
    """Eq. 5.55: E (pi/4)(r2^4 - r1^4)."""
    return E * math.pi / 4 * (r2**4 - r1**4)


def discrete_bending_factor_exact(N) -> float:
    """Eq. 5.58 sum: (1/N) sum_{n=0}^{N-1} (1 - n/N)^2."""
    return sum((1 - n / N)**2 for n in range(N)) / N


def discrete_bending_factor_approx(N) -> float:
    """Eq. 5.58 approximation: (3N + 4)/(9N - 2), exact for N = 1, 2, inf, else high by < 1%."""
    return (3 * N + 4) / (9 * N - 2)


def var_transverse_classical(T, l, k_b, N, G_l) -> float:
    """Eq. 5.59: kT [ l^3/k_b (3N+4)/(9N-2) + l/G_l ]."""
    return K_B * T * (l**3 / k_b * discrete_bending_factor_approx(N) + l / G_l)


def var_transverse_bending_5_64(T, l, k_b, rho_l, N) -> float:
    """Eq. 5.64: 0.76 hbar l / sqrt(k_b rho_l) + kT l^3/k_b (3N+4)/(9N-2)."""
    return 0.76 * HBAR * l / math.sqrt(k_b * rho_l) + K_B * T * l**3 / k_b * discrete_bending_factor_approx(N)


def var_transverse_bending_5_65(T, l, k_b, rho_l) -> float:
    """Eq. 5.65: 0.76 hbar l / sqrt(k_b rho_l) + kT l^3/(3 k_b) exp(-1.97 sqrt(k_b/rho_l) hbar / (l^2 kT))."""
    return (0.76 * HBAR * l / math.sqrt(k_b * rho_l)
            + K_B * T * l**3 / (3 * k_b) * math.exp(-1.97 / l**2 * math.sqrt(k_b / rho_l) * HBAR / (K_B * T)))


def two_source_overestimate(k1, k2) -> float:
    """Eq. 5.70: (sqrt(k1/k2) + 1) / sqrt(k1/k2 + 1), between 1 and sqrt 2."""
    r = k1 / k2
    return (math.sqrt(r) + 1) / math.sqrt(r + 1)


# ---- 5.6 entropic piston ------------------------------------------------------------------------

def piston_mean_and_variance(N, T, F_c):
    """Eq. 5.74: mean (N+1) kT/F_c, variance (N+1)(kT/F_c)^2."""
    a = K_B * T / F_c
    return (N + 1) * a, (N + 1) * a * a


# ---- 5.7 longitudinal variance from transverse modes ------------------------------------------------

def var_longitudinal_from_transverse_free(T, l, k_b, n_max=1000) -> float:
    """Eq. 5.98 (one polarization, free ends, no constraint): (1/2)(kT/k_b)^2 (l/pi)^4 sum 1/n^4."""
    s = sum(1 / n**4 for n in range(1, n_max + 1))
    return 0.5 * (K_B * T / k_b)**2 * (l / math.pi)**4 * s
