# Ionic equilibrium and electrodialysis model

**Documentation:** [English](docs/en/README.md) · [русская](docs/README.md) · [README.md](README.md)

Python port of `ECS_model3_3 N.xls` — ionic equilibrium and compartment electrodialysis model from the [dissertation by Senik Yu.V., 2005](https://www.dissercat.com/content/teoreticheskoe-i-eksperimentalnoe-issledovanie-elektromembrannykh-protsessov-pererabotki-pri).

License: [MIT](LICENSE).

## Features

| Scenario | Module | VBA |
|----------|--------|-----|
| Equilibrium composition and pH | `ion_model.equilibrium` | `equilibrium_calc` |
| Carbonate at fixed pH | `ion_model.carbon` | `carbon_calc`, `pure_water` |
| Specific conductivity κ | `ion_model.conductivity` | `el_conduct` |
| Membrane transport numbers | `ion_model.transport` | `T_calc_no_counterions` |
| ED layer, pH(L) profile, scans | `ion_model.ecs` | `CommandButton3`–`5`, `6`, `9` |

## Installation

```bash
pip install -r requirements.txt
pytest
```

Requires **Python 3.10+**. Tests use `xlrd` and `pytest`.

## Layout

```
programm/
  ion_model/           # model package
  ion_equilibrium.py   # backward-compatible re-export
  tests/               # regression vs ECS_model3_3 N.xls
  docs/                # documentation (ru + en/)
  ECS_model3_3 N.xls   # original Excel model
```

## Quick start

### Equilibrium

```python
from ion_model import equilibrium_calc, equilibrium_conductivity

c0 = [0.0] * 11
n = [0.0] * 11
n[0], n[1], n[3], n[10], n[5], n[8] = 0.003, 0.0024, 0.0011, 0.0003, 0.0065, 0.0061

result = equilibrium_calc(1.0, 18.0, n, c0)
kappa = equilibrium_conductivity(result.concentrations, 18.0, excel_vba_mapping=True)
```

### Mineral water + CO₂

```python
from ion_model import StrongIonInput, equilibrium_calc

strong = StrongIonInput(na=0.004, ca=0.00175, mg=0.00041, cl=0.0049, hco3=0.0098, so4=0.0001)
c0 = [strong.na, strong.ca, strong.mg, strong.cl, 0, 0, strong.hco3, 0, 0, 1e-7, strong.so4]
r = equilibrium_calc(1.0, 25.0, [0.0]*11, c0)  # pH ~8.35 without CO2
```

### Electrodialysis simulation

```python
from ion_model import (
    load_membrane_constants,
    load_ecs_geometry_from_workbook,
    simulate_channel,
)

membrane = load_membrane_constants("ECS_model3_3 N.xls")
geometry = load_ecs_geometry_from_workbook("ECS_model3_3 N.xls")
dc_in = [...]  # 10 concentrations, ECS row 17
cc_in = [...]  # row 22

channel = simulate_channel(dc_in, cc_in, geometry, membrane, n_layers=18)
for pt in channel.points:
    print(pt.length_cm, pt.ph_dc)
```

## VBA → Python

| VBA | Python |
|-----|--------|
| `equilibrium_calc` | `equilibrium_calc()` |
| `el_conduct` | `el_conduct()`, `equilibrium_conductivity()` |
| `kw`, `calculate_f`, `fun_no_precip` | `kw()`, `calculate_activity_coefficients()`, `fun_no_precip()` |
| `carbon_calc` | `carbon_speciation()` |
| `pure_water` | `pure_water_composition()` |
| `T_calc_no_counterions` | `t_calc_no_counterions()`, `transport_numbers_from_ecs_state()` |
| `Tw_func` | `tw_func()` |
| ECS `CommandButton4` | `ecs_layer_step()` |
| ECS `CommandButton5` | `simulate_channel()` |
| ECS `CommandButton6` | `scan_current_density()` |
| ECS `CommandButton9` | `scan_mixing_ratio()` |

## Documentation

**English:**

- [docs/en/README.md](docs/en/README.md) — index
- [docs/en/equilibrium.md](docs/en/equilibrium.md) — equilibrium, carbonate
- [docs/en/conductivity.md](docs/en/conductivity.md) — κ
- [docs/en/electrodialysis.md](docs/en/electrodialysis.md) — ED, transport numbers, channel

**Russian:**

- [docs/README.md](docs/README.md) — оглавление
- [docs/equilibrium.md](docs/equilibrium.md), [conductivity.md](docs/conductivity.md), [electrodialysis.md](docs/electrodialysis.md)

## Verification

Tests compare Python to saved Excel values (*Ion Equlibrium*, *ECS*, *pH(L)*). Critical check: pH profile along the channel (19 points, ±0.001 pH).

## Reference

Senik Yu.V. Theoretical and experimental study of electrodialysis processing of natural waters. Krasnodar, 2005.

Also used: Lurie Yu.Yu. Handbook of analytical chemistry. Moscow, 1971 (pK_w table); Larin B.M., Lukomskaya N.D. Calculation of ion concentrations from measured solution conductivity. *Izvestiya vuzov. Energetika*, 1986.

## License

Released under the [MIT License](LICENSE).

© 2005–2026 Yury V. Senik. Original model: Excel workbook `ECS_model3_3 N.xls` (VBA) and the 2005 dissertation; the Python port is a reimplementation of the same computational core.

The software is provided “as is”, without warranty of fitness for any particular engineering or industrial use.

## Citation

If you use this code in a publication, please cite:

> Senik Yu.V. Ionic equilibrium and electrodialysis model (Python port of ECS_model3_3). 2005–2026. URL: https://github.com/yurisenik/ion-model

```bibtex
@misc{senik_ion_model,
  author       = {Senik, Yury V.},
  title        = {Ionic equilibrium and electrodialysis model},
  note         = {Python port of ECS\_model3\_3 N.xls},
  year         = {2005--2026},
  howpublished = {\url{https://github.com/yurisenik/ion-model}}
}
```
