"""Audit of the 14.3.3 / 14.4.5 lifetime model against 13.3.6's 1e-15 error rate per operation.

14.3.3 takes Eq. 6.54 (radiation) as the damage model because 13.3.6 assumes step errors are
"dominated by radiation damage", and checks that assumption only at 1e4 operations/s per unit
(mill stages: a set's 1e6 /s over 100 units). Table 14.1's input-ordering and reagent-preparation
stages run at 1e6 Hz per unit, and 14.4.5 does not analyse them ("Earlier stages are massively
redundant"). Two readings of the per-step rate: fn. 34 (one weak step at 1e-15, the rest
<= 1e-18) and uniform (every step at 1e-15). Survivors absorb failed units' load (fn. 36), so
a stage keeps full throughput while its surviving capacity exceeds demand.
"""
import math

from . import ch06, ch13

YEAR = ch06.YEAR
THROUGHPUT = 1e-3                     # kg/s, Table 14.1 note a ("~1 gm/s")
DEMAND = THROUGHPUT * ch13.C_ATOMS_PER_KG   # moieties/s, ~1 carbon atom per moiety
PREP_UNITS, PREP_HZ, PREP_STEPS = 1e17, 1e6, 10      # Table 14.1; 13.3.3
PREP_MASS = 6e-20                     # kg per unit (Table 14.1: 0.06 fg)


def capacity_headroom() -> float:
    """Installed prep capacity / demand (~2)."""
    return PREP_UNITS * PREP_HZ / DEMAND


def unit_failure_rate(reading: str = "fn34", hz: float = PREP_HZ, steps: int = PREP_STEPS) -> float:
    """Step-error failures per second per unit."""
    if reading == "fn34":
        per_op = 1e-15 + (steps - 1) * 1e-18
    elif reading == "uniform":
        per_op = steps * 1e-15
    else:
        raise ValueError(reading)
    return per_op * hz


def radiation_failure_rate(m_kg: float = PREP_MASS, rad_per_year: float = 0.5) -> float:
    """Eq. 6.53 hazard: 1e15 × dose rate × mass, per second."""
    return 1e15 * rad_per_year * m_kg / YEAR


def years_until_capacity_short(rate: float, headroom: float | None = None) -> float:
    """Survivors fall to demand when headroom × exp(-rate t) = 1."""
    h = capacity_headroom() if headroom is None else headroom
    return math.log(h) / rate / YEAR


def per_op_for_lifetime(years: float, hz: float = PREP_HZ, headroom: float | None = None) -> float:
    """Per-operation rate of the weakest step that keeps capacity above demand for `years`."""
    h = capacity_headroom() if headroom is None else headroom
    return math.log(h) / (years * YEAR * hz)
