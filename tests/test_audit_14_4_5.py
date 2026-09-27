"""14.3.3 / 14.4.5 lifetime model vs 13.3.6's 1e-15 per operation (nsaudit/audit_14_4_5_lifetime.py)."""
import math

from nsaudit import audit_14_4_5_lifetime as a, ch13

MAJ = 1e-21


def close(x, y, tol):
    return abs(x - y) <= tol * abs(y)


def test_prep_headroom_2x():
    """Table 14.1: 1e17 prep units × 1e6 Hz against ~1 g/s (5e22 carbon moieties/s): ~2x."""
    assert close(a.capacity_headroom(), 2.0, 0.01)


def test_step_errors_outrun_radiation_at_1e6_hz():
    """fn. 34 reading (one step at 1e-15, nine at 1e-18): MTTF 31 yr, P_fail 0.27 in 10 yr, ~1000x
    the radiation hazard of a 6e-20 kg unit (MTTF 3.3e4 yr). Uniform reading: MTTF 3.2 yr."""
    fn34, uni = a.unit_failure_rate("fn34"), a.unit_failure_rate("uniform")
    assert close(1 / fn34 / a.YEAR, 31.4, 0.01)
    assert close(1 - math.exp(-fn34 * 10 * a.YEAR), 0.27, 0.02)
    assert close(fn34 / a.radiation_failure_rate(), 1060, 0.01)
    assert close(1 / uni / a.YEAR, 3.17, 0.01)


def test_capacity_shortfall_times():
    """With survivors absorbing load (fn. 36), prep capacity falls below demand after ~22 years
    (fn. 34 reading) or ~2.2 years (uniform reading)."""
    assert close(a.years_until_capacity_short(a.unit_failure_rate("fn34")), 21.7, 0.01)
    assert close(a.years_until_capacity_short(a.unit_failure_rate("uniform")), 2.19, 0.01)


def test_remedy_is_cheap():
    """A 100-year stage needs the weakest step at ~2.2e-16 (149 maJ vs 143 in the equilibrium
    reading, +6 maJ); 1000 years ~2.2e-17 (+16 maJ)."""
    p100, p1000 = a.per_op_for_lifetime(100), a.per_op_for_lifetime(1000)
    assert close(p100, 2.2e-16, 0.01) and close(p1000, 2.2e-17, 0.01)
    assert close(ch13.energy_for_probability(p100), 149 * MAJ, 0.01)
    assert close(ch13.energy_for_probability(p1000), 159 * MAJ, 0.01)
