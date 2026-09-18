"""nsaudit — reproducible calculations for the Nanosystems audit.

Conventions
-----------
* Plain SI floats everywhere (m, s, kg, N, Pa, J, K, W). Every function's docstring names the
  book equation it implements. Values are returned in SI; the tests compare against Drexler's
  published figures converted to SI (1 maJ = 1e-21 J, 1 aJ = 1e-18 J).
* Each test that reproduces a published number is simultaneously a verification, a regression
  guard, and provenance for the `spot_check` field of the corresponding export.
* Nothing here is a verdict. Verdicts live in chapters/chNN.yaml and cite these functions.
"""

K_B = 1.380649e-23  # J/K, exact (SI 2019)
MAJ = 1e-21         # J per milli-attojoule, the book's working unit
AJ = 1e-18
