# Ionic equilibrium and carbonate system

Technical description of `equilibrium_calc` — ported from VBA module `model.bas` in `ECS_model3_3 N.xls`.

**Source:** Senik Yu.V. *Theoretical and experimental study of electrodialysis processing of natural waters.* Krasnodar, 2005 (Ch. 2).

**Implementation:** `ion_model/` package ([equilibrium.py](../../ion_model/equilibrium.py), [carbon.py](../../ion_model/carbon.py))

---

## 1. Purpose and scope

The model computes **composition and pH** of an aqueous solution at chemical equilibrium given:

- initial component concentrations;
- amounts of added (or removed) substances;
- solution volume and temperature.

It is intended for **dilute multicomponent** natural and industrial waters (mmol/L to g/L), including Na⁺, Ca²⁺, Mg²⁺, Cl⁻, NO₃⁻, SO₄²⁻, and the carbonate system.

According to dissertation verification, pH, component concentrations, and (in the full Excel model) specific conductivity are reproduced within acceptable error up to **~0.05 eq/L**, using the **Debye–Hückel extended approximation** for activity coefficients.

---

## 2. Chemical system

### 2.1. Components

11 components. Indexing in Python (0-based) and VBA (1-based):

| Python | VBA | Symbol | Charge *z* |
|--------|-----|--------|------------|
| 0 | 1 | Na⁺ | +1 |
| 1 | 2 | Ca²⁺ | +2 |
| 2 | 3 | Mg²⁺ | +2 |
| 3 | 4 | Cl⁻ | −1 |
| 4 | 5 | NO₃⁻ | −1 |
| 5 | 6 | H₂CO₃* | 0 |
| 6 | 7 | HCO₃⁻ | −1 |
| 7 | 8 | CO₃²⁻ | −2 |
| 8 | 9 | OH⁻ | −1 |
| 9 | 10 | H⁺ | +1 |
| 10 | 11 | SO₄²⁻ | −2 |

\* H₂CO₃ — total dissolved CO₂ (H₂CO₃ + CO₂(aq)).

### 2.2. Reactions included

**First dissociation of carbonic acid:**

$$
\mathrm{H_2CO_3 \rightleftharpoons H^+ + HCO_3^-}
\qquad K_1(T)
$$

**Second dissociation:**

$$
\mathrm{HCO_3^- \rightleftharpoons H^+ + CO_3^{2-}}
\qquad K_2(T)
$$

**Water autoprotolysis:**

$$
\mathrm{H_2O \rightleftharpoons H^+ + OH^-}
\qquad K_w(T)
$$

Strong electrolyte ions (Na⁺, Ca²⁺, Cl⁻, …) **do not undergo protolytic redistribution**; their total amounts are conserved.

### 2.3. Not modeled explicitly

- solid phase precipitation (CaCO₃, Mg(OH)₂, etc.) — polynomial `fun_no_precip` assumes no precipitate;
- complexes and ion pairs (except via γ);
- gas-phase CO₂ pressure (excess CO₂ is set via H₂CO₃ component amount);
- redox, adsorption, membrane transport (other Excel modules).

---

## 3. Material balance

After mixing or adding substances in volume *V* (L), the analytical concentration of each component is:

$$
m_i = C_{0,i} + \frac{n_i}{V}
$$

where $C_{0,i}$ is initial concentration (mol/L), $n_i$ is amount added (mol). Negative $n_i$ means removal.

### Carbon balance

$$
s_m = m_{\mathrm{H_2CO_3}} + m_{\mathrm{HCO_3^-}} + m_{\mathrm{CO_3^{2-}}}
$$

Total analytical carbon in the carbonate system (mol C/L).

### Auxiliary parameter

$$
s_{m1} = m_{\mathrm{H^+}} + m_{\mathrm{H_2CO_3}} - m_{\mathrm{CO_3^{2-}}} - m_{\mathrm{OH^-}}
$$

For typical inputs (no added acid/base), $m_{\mathrm{H^+}} \approx m_{\mathrm{CO_3^{2-}}} \approx m_{\mathrm{OH^-}} \approx 0$ and $s_{m1} \approx m_{\mathrm{H_2CO_3}}$. This parameter enters the polynomial coefficients when initial H⁺, OH⁻, or CO₃²⁻ are nonzero.

---

## 4. Equilibrium with activity coefficients

Constants are expressed via **activities** $a_i = \gamma_i c_i$:

$$
K_1 = \frac{a_{\mathrm{H^+}}\, a_{\mathrm{HCO_3^-}}}{a_{\mathrm{H_2CO_3}}}
\qquad
K_2 = \frac{a_{\mathrm{H^+}}\, a_{\mathrm{CO_3^{2-}}}}{a_{\mathrm{HCO_3^-}}}
\qquad
K_w = a_{\mathrm{H^+}}\, a_{\mathrm{OH^-}}
$$

On each γ iteration, **reduced constants** are used:

$$
k_{p,1} = K_1 \frac{\gamma_{\mathrm{H_2CO_3}}}{\gamma_{\mathrm{H^+}}\, \gamma_{\mathrm{HCO_3^-}}}
\qquad
k_{p,2} = K_2 \frac{\gamma_{\mathrm{HCO_3^-}}}{\gamma_{\mathrm{H^+}}\, \gamma_{\mathrm{CO_3^{2-}}}}
\qquad
k_{p,3} = K_w \frac{1}{\gamma_{\mathrm{H^+}}\, \gamma_{\mathrm{OH^-}}}
$$

### Equilibrium concentrations (fixed $c_{\mathrm{H^+}} = A$)

Let $A = [\mathrm{H^+}]$. Then:

$$
[\mathrm{HCO_3^-}] = \frac{s_m}{1 + A/k_{p,1} + k_{p,2}/A}
$$

$$
[\mathrm{H_2CO_3}] = \frac{A\,[\mathrm{HCO_3^-}]}{k_{p,1}}
\qquad
[\mathrm{CO_3^{2-}}] = \frac{k_{p,2}\,[\mathrm{HCO_3^-}]}{A}
\qquad
[\mathrm{OH^-}] = \frac{k_{p,3}}{A}
$$

Strong electrolyte concentrations equal $m_i$.

---

## 5. Equation for [H⁺]: fourth-degree polynomial

Unknown $A = [\mathrm{H^+}]$ is the **positive root** of $f(A) = 0$:

$$
\begin{aligned}
f(c) =\;& c^4 + c^3(k_{p,1} - s_{m1} + s_m) \\
&+ c^2(k_{p,1} k_{p,2} - k_{p,1} s_{m1} - k_{p,3}) \\
&- c\,(k_{p,1} k_{p,2} s_{m1} + k_{p,3} k_{p,1} + s_m k_{p,1} k_{p,2}) \\
&- k_{p,1} k_{p,2} k_{p,3}
\end{aligned}
$$

`fun_no_precip(c, kp, sm, sm1)` implements this expression.

The equation follows from carbonate and water equilibria, material balances $s_m$, $s_{m1}$, and charge neutrality.

If $f$ has no sign change on $[10^{-15},\,10]$ mol/L, `equilibrium_calc` returns `success=False`.

---

## 6. Temperature dependence of constants

Absolute temperature: $T_\mathrm{abs} = t + 273.15$ (K), $t$ in °C.

### 6.1. Carbonic acid constants

As in VBA:

$$
\log K_1 = -\left(\frac{17052}{T_\mathrm{abs}} + 215.21\log T_\mathrm{abs} - 0.12675\,T_\mathrm{abs} - 545.56\right)
$$

$$
\log K_2 = -\left(\frac{2909.1}{T_\mathrm{abs}} - 6.498 + 0.02379\,T_\mathrm{abs}\right)
$$

$K_1, K_2 = 10^{\log K}$.

### 6.2. Ion product of water

`kw(t_celsius)`:

1. Table of $(t,\; pK_w)$ from Lurie Yu.Yu. (1971) — 35 points from 0 to 100 °C.
2. **Lagrange interpolation** for $pK_w(t)$.
3. $K_w = 10^{-pK_w} \times 10^{-14}$ (in code: `sum_kw * 1e-14`).

---

## 7. Activity coefficients (Debye–Hückel extended)

`calculate_activity_coefficients` (VBA: `calculate_f`).

### 7.1. Water dielectric permittivity

$$
\varepsilon = 78.54\,\left(1 - 0.0046\,t + 0.0000088\,t^2\right)
$$

($t$ in °C, as in VBA `calculate_f`).

### 7.2. Ionic strength

$$
\mu = \frac{1}{2}\sum_k z_k^2 c_k
$$

Over 6 anions and 4 cations, including H⁺ as a cation.

### 7.3. Activity coefficient

$$
A_1 = 1.825\times10^6 \left(\varepsilon\,\varepsilon_0\,T_\mathrm{abs}\right)^{3/2}
$$

$$
\log \gamma_i = -\frac{|z_i|\,A_1\,\sqrt{\mu}}{1 + \sqrt{\mu}}
\qquad
\gamma_i = 10^{\log \gamma_i}
$$

$\varepsilon_0 = 8.854\times10^{-12}$ F/m.

First iteration: all $\gamma_i = 1$; after finding $A$, concentrations and $\gamma_i$ are updated until $|A^{(k)} - A^{(k-1)}| \le \delta$.

---

## 8. Numerical algorithm

```mermaid
flowchart TD
    A[Input C0, n, V, t] --> B[m_i = C0_i + n_i/V]
    B --> C[sm, sm1; gamma = 1]
    C --> D[K1, K2, Kw from t]
    D --> E[kp1, kp2, kp3 from gamma]
    E --> F{Root of f on 1e-15..10?}
    F -->|no| G[success = false]
    F -->|yes| H[Bisection: find A = H+]
    H --> I[Equilibrium c_i from A]
    I --> J{|A - A_prev| <= delta?}
    J -->|yes| K[pH = -log A; return]
    J -->|no| L[Recalc gamma from mu]
    L --> E
```

### 8.1. Inner loop (bisection)

- Interval: $A \in [10^{-15},\,10]$ mol/L.
- Each step checks midpoints $(A+B)/2$ and $(B-A)/2$ (two branches, as in VBA).
- Stop when $|A - B| \le \delta$, $\delta \sim 10^{-\lfloor-\log A\rfloor + 14}$.

### 8.2. Outer loop (activities)

- Previous $A$ stored as `aa`.
- If $|aa - A| > \delta_\mathrm{outer}$ (exponent 16), γ is updated and the loop repeats.
- Typically 2–5 iterations for natural waters.

### 8.3. pH

$$
\mathrm{pH} = -\log_{10}[\mathrm{H^+}]
$$

---

## 9. Problem setup in Excel

**Ion Equlibrium** sheet:

| Cell | Parameter |
|------|-----------|
| C3 | Temperature, °C |
| D3 | Volume, L |
| B7–L7 | Initial concentrations $C_0$ |
| B9–L9 | Amounts added $n$ |
| B11–L11 | Result: equilibrium concentrations |
| L13 | Result: pH |
| K13 | Specific conductivity κ, S/m (`el_conduct`; B24 — κ in mS/cm) |

The calculate button calls `model.equilibrium_calc`.

### Discretization method (dissertation)

Substance addition is specified as **finite amounts** $n_i$ in volume $V$. This models titration, stream mixing in electrodialysis, etc., by linearizing compared to continuous composition change in the full ED model.

---

## 10. Interpreting results

### 10.1. Adding salts to distilled water

Excel example (V=1 L, t=18 °C): NaCl, CaCl₂, H₂CO₃, OH⁻, etc. → pH ≈ 7.58. Python matches the macro to ~10⁻⁵ on pH.

### 10.2. Natural / mineral water (degassed)

“Goryachiy Klyuch”, well 934 (charge-balanced): HCO₃⁻ dominates → **pH ≈ 8.35** at 25 °C.

### 10.3. Carbonated water

Lab analysis usually refers to a **degassed** sample. Excess CO₂ in the bottle increases $m_{\mathrm{H_2CO_3}}$ via `moles_added[5]`:

| Added CO₂, mmol/L | pH (934, 25 °C) |
|-------------------|-----------------|
| 0 | 8.35 |
| 8 | 6.45 |
| 15 | 6.18 |
| 22 | 6.0 |

pH meter reading **without degassing** in carbonated water is lower — expected, not a model failure.

### 10.4. Charge balance of inputs

The model assumes net charge of strong ions in $m_i$ is near zero; carbonate and H⁺/OH⁻ adjust balance. Independent passport ranges for Na, Cl, HCO₃, Ca may disagree by **several meq/L** — balance before calculation (e.g. adjust Na⁺ or Cl⁻).

---

## 11. Carbonate speciation (`carbon_speciation`, `pure_water_composition`)

Port of VBA `carbon_calc` and `pure_water`.

### 11.1. `pure_water_composition(T)`

K_w(T) → [H⁺]=[OH⁻] with γ iteration (Debye–Hückel). Returns 11-component vector with zero strong electrolytes.

### 11.2. `carbon_speciation(pH, strong, T, *, total_carbonate=… | hco3=…)`

At fixed pH and strong ions, recalculates H₂CO₃, HCO₃⁻, CO₃²⁻, OH⁻, H⁺ until γ converges.

| Mode | Excel | Python parameter |
|------|-------|------------------|
| Total carbonate | OptionButton1, J3 | `total_carbonate` |
| Fixed HCO₃⁻ | OptionButton2, I3 | `hco3` |

### 11.3. API

```python
from ion_model import StrongIonInput, carbon_speciation, pure_water_composition

strong = StrongIonInput(na=0.003, ca=0.0024, cl=0.0011, so4=0.0003)
c = carbon_speciation(7.0, strong, 18.0, total_carbonate=0.0065)
```

---

## 12. API summary

```python
from ion_model import equilibrium_calc, EquilibriumResult, carbon_speciation, pure_water_composition
```

See also [conductivity.md](conductivity.md), [electrodialysis.md](electrodialysis.md).

---

## 13. References

1. Senik Yu.V. Theoretical and experimental study of electrodialysis processing of natural waters. Krasnodar, 2005.
2. Lurie Yu.Yu. Handbook of analytical chemistry. Moscow, 1971 — pK_w(T) table.

---

## 14. Related files

- [README.md](../../README.en.md)
- [docs/en/README.md](README.md)
- `ion_model/` package
