# `ion_model` documentation (English)

Python port of the **ECS_model3_3 N.xls** workbook (Senik Yu.V., 2005 dissertation).

**Russian version:** [../README.md](../README.md)

## Topics

| Document | Python | VBA / Excel sheet |
|----------|--------|-----------------|
| [equilibrium.md](equilibrium.md) | `equilibrium.py`, `carbon.py` | `equilibrium_calc`, `carbon_calc`, `pure_water` — *Ion Equlibrium* |
| [conductivity.md](conductivity.md) | `conductivity.py` | `el_conduct` — *Ion Equlibrium* K13 |
| [electrodialysis.md](electrodialysis.md) | `transport.py`, `ecs.py`, `constants.py` | `T_calc*`, *ECS*, *pH(L)*, *pH(i)*, *pH(b)* |

## Quick start

```bash
pip install -r requirements.txt
pytest
```

```python
from ion_model import equilibrium_calc, simulate_channel, load_membrane_constants
```

Backward compatibility: `from ion_equilibrium import equilibrium_calc` still works.

## Package layout

```
ion_model/
  equilibrium.py    # equilibrium, pH, activity coefficients
  carbon.py         # carbonate speciation at fixed pH
  conductivity.py   # κ (S/m)
  constants.py      # Constants sheet
  transport.py      # transport numbers
  ecs.py            # layer step, channel, parameter scans
  types.py          # dataclass API
```

## Verification

Regression tests in `tests/` read reference values from `ECS_model3_3 N.xls` (xlrd). Typical tolerances: pH ±10⁻³, κ ±10⁻⁴ S/m, transport numbers ±10⁻⁴.

## Legacy file

[model.md](model.md) redirects here; content is split across the three topic files above.
