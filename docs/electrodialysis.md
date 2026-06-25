# Электродиализ (лист ECS)

Порт макросов листа **ECS** книги `ECS_model3_3 N.xls`: числа переноса (`T_calc_no_counterions`), шаг компартмента (`CommandButton4`), проход по каналу (`CommandButton5`), параметрические сканирования (`CommandButton6`, `CommandButton9`).

**Реализация:** [ion_model/transport.py](../ion_model/transport.py), [ion_model/ecs.py](../ion_model/ecs.py), [ion_model/constants.py](../ion_model/constants.py).

**Источник:** Сеник Ю.В. *Теоретическое и экспериментальное исследование электромембранных процессов переработки природных вод.* Краснодар, 2005 (гл. 4).

---

## 1. Геометрия и потоки (`ECSGeometry`)

| Поле Python | Ячейка ECS | Единица | Описание |
|-------------|------------|---------|----------|
| `area_cm2` | B2 | см² | Площадь мембраны *a* |
| `layer_thickness_cm` | B3 | см | Толщина слоя *L* |
| `channel_height_cm` | B4 | см | Высота канала *h* |
| `flow_dc_ml_s` | B5 | мл/с | Расход обессоливающего канала W_DC |
| `flow_cc_ml_s` | B6 | мл/с | Расход концентрирующего канала W_CC |
| `current_density_ma_cm2` | B7 | мА/см² | Плотность тока *i* (обновляется до *i_tot* при расчёте TN) |
| `delta_cm` | B9 | см | Толщина ДДС у КМ |
| `delta0_cm` | I9 | см | Эталонная толщина ДДС |
| `tw` | B10 | — | Доля генерации H⁺/OH⁻ у КМ |
| `twa` | B11 | — | Доля генерации у АМ |
| `mixing_ratio` | J6 | — | b = W_DC/(W_DC+W_CC) |

Константы мембран — лист **Constants** (`MembraneConstants`, `load_membrane_constants()`).

---

## 2. Числа переноса (`T_calc_no_counterions`)

ECS использует вариант **без контр-ионов** (`CommandButton3`):

1. `T_calc_lim_current_no_counterions` — предельные TN при *i* → *i_lim*; итерация по *i_tot* с учётом водородной генерации Tw на КМ.
2. При *i* ≥ *i_lim,MA* (= 0 в этой модели) TN на АМ берутся из предельных значений.
3. TN на КМ всегда равны предельным (`T_MC_c_lim`, `T_MC_a` = 0).

Побочный эффект VBA: `Worksheets(2).Range("B7") = i_tot` — в Python поле `TransportNumbers.i_total`.

### 2.1. `Tw_func`

\[
T_w(i) = B\,\bigl(\exp(A\, i/i_{lim}) - 1\bigr)
\]

Параметры *A*, *B* — лист Constants (B25, C25).

### 2.2. Порядок ионов в транспорте

**Анионы (6):** Cl⁻, NO₃⁻, SO₄²⁻, HCO₃⁻, CO₃²⁻, OH⁻ — столбцы C, D, E, G, H, I листа ECS.

**Катионы (3):** Na⁺, Ca²⁺, H⁺ — столбцы A, B, J.

Строки **28** (АМ) и **30** (КМ) листа ECS — эталон TN для регрессионных тестов.

---

## 3. Материальный баланс слоя (`ecs_layer_step`)

Для каждого иона (кроме H₂CO₃) поток через мембранный пакет:

\[
n_k = -\mathrm{desalination}\,\frac{(T_{\mathrm{MC},k} - T_{\mathrm{MA},k})\, i\, A\, L}{|z_k|\, F}
\]

- **DC:** `desalination = +1`, объёмный расход `V = W_DC` (мл/с) → в `equilibrium_calc` передаётся `V/1000` (л/с).
- **CC:** `desalination = -1`, `V = W_CC`.

Константа Фарадея в VBA: **F = 96 500 000** мкКл/моль (`FARADAY_MCS`).

После расчёта *n* вызывается `equilibrium_calc` при **T = 25 °C** (как в VBA `CommandButton4`).

### Маппинг ECS → 11 компонентов

Na, Ca, Cl, NO₃, SO₄, H₂CO₃, HCO₃⁻, CO₃²⁻, OH⁻, H⁺ (Mg = 0).

---

## 4. Проход по длине канала (`simulate_channel`)

Аналог `CommandButton5`:

1. Запись начальной точки *L* = 0, pH DC.
2. Цикл `n_layers` раз: `compute_transport` → обновить *i* = `i_total` → `ecs_layer_step` → копировать выход в вход.
3. Запись в профиль: *L*, pH, T(Na), T(Ca), T(H), *i*, интегралы N(Na), N(Ca).

Эталон — лист **pH(L)** (19 точек pH, допуск ±10⁻³).

---

## 5. Параметрические сканирования

| Python | VBA | Лист | Что меняется |
|--------|-----|------|--------------|
| `scan_current_density` | CommandButton6 | pH(i) | *i* с шагом G45 до G46; перед каждой точкой сброс DC/CC из Ion Equilibrium |
| `scan_mixing_ratio` | CommandButton9 | pH(b) | *b* = W_DC/(W_DC+W_CC); W_CC = W_DC·(1/*b* − 1) |

Обе функции возвращают `list[ScanPoint]` с выходным pH DC и CC после полного прохода по каналу.

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

## 7. Ограничения и замечания

- Режим *i* < *i_lim,MA* при *i_lim,MA* = 0 не используется (ветка VBA с MsgBox закомментирована).
- `T_calc_zero_current` в VBA для ECS **закомментирован** — не вызывается.
- Концентрации контр-концентрата `Cb_*` передаются в VBA, но в `T_calc_no_counterions` не влияют на TN.
- Опечатка VBA: `D_c_MC(3)` для H⁺ берётся из **J5**, не J7 — воспроизведено в `membrane_diffusion()`.

---

## 8. Связанные файлы

- [equilibrium.md](equilibrium.md) — `equilibrium_calc` после слоя
- [conductivity.md](conductivity.md) — κ раствора
- [README.md](README.md) — оглавление документации
