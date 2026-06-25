# Модель ионных равновесий и электродиализа

**Документация:** [русская](docs/README.md) · **[English](docs/en/README.md)** · [README.en.md](README.en.md)

Python-порт книги `ECS_model3_3 N.xls` — программы для расчёта ионных равновесий и компартментной модели ЭД (диссертация [Сеник Ю.В., 2005](https://www.dissercat.com/content/teoreticheskoe-i-eksperimentalnoe-issledovanie-elektromembrannykh-protsessov-pererabotki-pri); научный руководитель — **Никоненко Виктор Васильевич**).

Лицензия: [MIT](LICENSE).

## Возможности

| Сценарий | Модуль | VBA |
|----------|--------|-----|
| Равновесный состав и pH | `ion_model.equilibrium` | `equilibrium_calc` |
| Карбонат при заданном pH | `ion_model.carbon` | `carbon_calc`, `pure_water` |
| Удельная электропроводность κ | `ion_model.conductivity` | `el_conduct` |
| Числа переноса в мембранах | `ion_model.transport` | `T_calc_no_counterions` |
| Слой ЭД, профиль pH(L), сканы | `ion_model.ecs` | `CommandButton3`–`5`, `6`, `9` |

## Установка

```bash
pip install -r requirements.txt
pytest
```

Требуется **Python 3.10+**. Для чтения эталона в тестах: `xlrd`, `pytest`.

## Структура

```
programm/
  ion_model/           # пакет модели
  ion_equilibrium.py   # обратная совместимость (re-export)
  tests/               # регрессия vs ECS_model3_3 N.xls
  docs/                # equilibrium, conductivity, electrodialysis
  ECS_model3_3 N.xls   # исходная Excel-модель
```

## Быстрый старт

### Равновесие

```python
from ion_model import equilibrium_calc, equilibrium_conductivity

c0 = [0.0] * 11
n = [0.0] * 11
n[0], n[1], n[3], n[10], n[5], n[8] = 0.003, 0.0024, 0.0011, 0.0003, 0.0065, 0.0061

result = equilibrium_calc(1.0, 18.0, n, c0)
kappa = equilibrium_conductivity(result.concentrations, 18.0, excel_vba_mapping=True)
```

### Минеральная вода + CO₂

```python
from ion_model import StrongIonInput, carbon_speciation, equilibrium_calc

strong = StrongIonInput(na=0.004, ca=0.00175, mg=0.00041, cl=0.0049, hco3=0.0098, so4=0.0001)
c0 = [strong.na, strong.ca, strong.mg, strong.cl, 0, 0, strong.hco3, 0, 0, 1e-7, strong.so4]
r = equilibrium_calc(1.0, 25.0, [0.0]*11, c0)  # pH ~8.35 без CO2
```

### Симуляция электродиализа

```python
from ion_model import (
    load_membrane_constants,
    load_ecs_geometry_from_workbook,
    simulate_channel,
)

membrane = load_membrane_constants("ECS_model3_3 N.xls")
geometry = load_ecs_geometry_from_workbook("ECS_model3_3 N.xls")
dc_in = [...]  # 10 концентраций, лист ECS строка 17
cc_in = [...]  # строка 22

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

## Документация

- [docs/README.md](docs/README.md) — оглавление
- [docs/equilibrium.md](docs/equilibrium.md) — равновесия, карбонат
- [docs/conductivity.md](docs/conductivity.md) — κ
- [docs/electrodialysis.md](docs/electrodialysis.md) — ЭД, TN, слой, канал

**English:** [docs/en/README.md](docs/en/README.md) · [README.en.md](README.en.md)

## Верификация

Тесты сравнивают Python с сохранёнными значениями Excel (листы *Ion Equlibrium*, *ECS*, *pH(L)*). Критический путь — профиль pH по длине канала (19 точек, ±0.001 pH).

## Благодарности

Исходная Excel-модель и диссертационное исследование (2005) выполнены под научным руководством **Никоненко Виктора Васильевича**. Автор благодарит научного руководителя за постановку задачи, методологическую поддержку и развитие подходов к моделированию электромембранных процессов.

## Литература

Сеник Ю.В. Теоретическое и экспериментальное исследование электромембранных процессов переработки природных вод. Краснодар, 2005.

Дополнительно использованы: Лурье Ю.Ю. Справочник по аналитической химии. М., 1971 (таблица pK_w); Ларин Б.М., Лукомская Н.Д. Расчёт концентраций ионов по измеренной электропроводности // Изв. вузов. Энергетика. 1986.

## Лицензия

Проект распространяется под лицензией [MIT](LICENSE).

© 2005–2026 Юрий В. Сеник. Исходная модель: Excel-книга `ECS_model3_3 N.xls` (VBA) и диссертация 2005 г.; Python-порт — отдельная реализация того же алгоритмического ядра.

Программа предоставляется «как есть», без гарантий пригодности для конкретных инженерных или производственных задач.

## Цитирование

Если вы используете этот код в публикации, укажите:

> Сеник Ю.В. Модель ионных равновесий и электродиализа (Python-порт ECS_model3_3). 2005–2026. URL: https://github.com/yurisenik/ion-model

```bibtex
@misc{senik_ion_model,
  author       = {Senik, Yury V.},
  title        = {Ionic equilibrium and electrodialysis model},
  note         = {Python port of ECS\_model3\_3 N.xls},
  year         = {2005--2026},
  howpublished = {\url{https://github.com/yurisenik/ion-model}}
}
```
