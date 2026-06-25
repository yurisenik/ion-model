"""
Backward-compatible re-exports from the ``ion_model`` package.

Prefer ``from ion_model import ...`` in new code.
"""

from ion_model import *  # noqa: F403
from ion_model import __all__  # noqa: F401

if __name__ == "__main__":
    from ion_model import COMPONENT_NAMES, equilibrium_calc, equilibrium_conductivity

    c0 = [0.0] * 11
    n = [0.0] * 11
    n[0], n[1], n[3], n[10], n[5], n[8] = 0.003, 0.0024, 0.0011, 0.0003, 0.0065, 0.0061
    result = equilibrium_calc(1.0, 18.0, n, c0)
    kappa = equilibrium_conductivity(result.concentrations, 18.0, excel_vba_mapping=True)
    print(f"success: {result.success}")
    print(f"pH = {result.ph:.6f}  (Excel: 7.579402)")
    print(f"kappa = {kappa:.6f} S/m  (Excel: 0.063526)")
    for name, value in zip(COMPONENT_NAMES, result.concentrations):
        print(f"  {name:8s} {value:.6e}")
