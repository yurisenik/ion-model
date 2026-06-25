# Electrodialysis (ECS sheet)

Port of **ECS** sheet macros from `ECS_model3_3 N.xls`: transport numbers (`T_calc_no_counterions`), compartment layer step (`CommandButton4`), channel simulation (`CommandButton5`), parameter scans (`CommandButton6`, `CommandButton9`).

**Implementation:** [ion_model/transport.py](../../ion_model/transport.py), [ion_model/ecs.py](../../ion_model/ecs.py), [ion_model/constants.py](../../ion_model/constants.py).

**Source:** Senik Yu.V. *Theoretical and experimental study of electrodialysis processing of natural waters.* Krasnodar, 2005 (Ch. 4).

---

## 1. Geometry and flows (`ECSGeometry`)

| Python field | ECS cell | Unit | Description |
|--------------|----------|------|-------------|
| `area_cm2` | B2 | cm² | Membrane area *a* |
| `layer_thickness_cm` | B3 | cm | Layer thickness *L* |
| `channel_height_cm` | B4 | cm | Channel height *h* |
| `flow_dc_ml_s` | B5 | mL/s | Desalinating compartment flow W_DC |
| `flow_cc_ml_s` | B6 | mL/s | Concentrating compartment flow W_CC |
| `current_density_ma_cm2` | B7 | mA/cm² | Current density *i* (updated to *i_tot* when computing TN) |
| `delta_cm` | B9 | cm | DBL thickness at CEM |
| `delta0_cm` | I9 | cm | Reference DBL thickness |
| `tw` | B10 | — | H⁺/OH⁻ generation fraction at CEM |
| `twa` | B11 | — | Generation fraction at AEM |
| `mixing_ratio` | J6 | — | b = W_DC/(W_DC+W_CC) |

Membrane constants come from the **Constants** sheet (`MembraneConstants`, `load_membrane_constants()`).

---

## 2. Transport numbers (`T_calc_no_counterions`)

The ECS sheet uses the **no-counterions** variant (`CommandButton3`):

1. `T_calc_lim_current_no_counterions` — limiting TN as *i* → *i_lim*; iteration over *i_tot* including H⁺/OH⁻ generation (Tw) at the CEM.
2. For *i* ≥ *i_lim,MA* (= 0 in this model), AEM transport numbers equal the limiting values.
3. CEM transport numbers always equal the limiting values (`T_MC_c_lim`, `T_MC_a` = 0).

VBA side effect: `Worksheets(2).Range("B7") = i_tot` — in Python use `TransportNumbers.i_total`.

### 2.1. `Tw_func`

$$
T_w(i) = B\,\bigl(\exp(A\, i/i_{lim}) - 1\bigr)
$$

Parameters *A*, *B* are on the Constants sheet (B25, C25).

### 2.2. Ion order in transport

**Anions (6):** Cl⁻, NO₃⁻, SO₄²⁻, HCO₃⁻, CO₃²⁻, OH⁻ — ECS columns C, D, E, G, H, I.

**Cations (3):** Na⁺, Ca²⁺, H⁺ — columns A, B, J.

ECS rows **28** (AEM) and **30** (CEM) are the reference TN values for regression tests.

---

## 3. Layer material balance (`ecs_layer_step`)

For each ion (except H₂CO₃), flux through the membrane stack:

$$
n_k = -\mathrm{desalination}\,\frac{(T_{\mathrm{MC},k} - T_{\mathrm{MA},k})\, i\, A\, L}{|z_k|\, F}
$$

- **DC:** `desalination = +1`, volumetric flow `V = W_DC` (mL/s) → `equilibrium_calc` receives `V/1000` (L/s).
- **CC:** `desalination = -1`, `V = W_CC`.

Faraday constant in VBA: **F = 96 500 000** mC/mol (`FARADAY_MCS`).

After computing *n*, `equilibrium_calc` is called at **T = 25 °C** (as in VBA `CommandButton4`).

### ECS → 11-component mapping

Na, Ca, Cl, NO₃, SO₄, H₂CO₃, HCO₃⁻, CO₃²⁻, OH⁻, H⁺ (Mg = 0).

---

## 4. Channel simulation (`simulate_channel`)

Equivalent to `CommandButton5`:

1. Record initial point *L* = 0, DC pH.
2. Loop `n_layers` times: `compute_transport` → update *i* = `i_total` → `ecs_layer_step` → copy output to inlet.
3. Profile: *L*, pH, T(Na), T(Ca), T(H), *i*, integrals N(Na), N(Ca).

Reference: **pH(L)** sheet (19 pH points, tolerance ±10⁻³).

---

## 5. Parameter scans

| Python | VBA | Sheet | Parameter |
|--------|-----|-------|-----------|
| `scan_current_density` | CommandButton6 | pH(i) | *i* from G45 step to G46; reset DC/CC from Ion Equilibrium before each point |
| `scan_mixing_ratio` | CommandButton9 | pH(b) | *b* = W_DC/(W_DC+W_CC); W_CC = W_DC·(1/*b* − 1) |

Both return `list[ScanPoint]` with outlet DC and CC pH after a full channel pass.

---

## 6. API

```python
from ion_model import (
    load_membrane_constants,
    load_ecs_geometry_from_workbook,
    compute_transport,
    ecs_layer_step,
    simulate_channel,
    scan_current_density,
    scan_mixing_ratio,
)

membrane = load_membrane_constants("ECS_model3_3 N.xls")
geometry = load_ecs_geometry_from_workbook("ECS_model3_3 N.xls")

channel = simulate_channel(dc_in, cc_in, geometry, membrane, n_layers=18)
profile = channel.points  # ChannelPoint: length_cm, ph_dc, t_na, t_ca, t_h, ...
```

---

## 7. Limitations and notes

- The branch *i* < *i_lim,MA* with *i_lim,MA* = 0 is unused (VBA MsgBox is commented out).
- `T_calc_zero_current` is **commented out** in VBA for ECS — not called.
- Counter-compartment concentrations `Cb_*` are passed in VBA but do not affect TN in `T_calc_no_counterions`.
- VBA typo: `D_c_MC(3)` for H⁺ uses **J5**, not J7 — reproduced in `membrane_diffusion()`.

---

## 8. Related files

- [equilibrium.md](equilibrium.md) — `equilibrium_calc` after each layer
- [conductivity.md](conductivity.md) — solution κ
- [README.md](README.md) — documentation index
