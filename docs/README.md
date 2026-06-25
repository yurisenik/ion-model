# Документация `ion_model`

Порт расчётного ядра книги **ECS_model3_3 N.xls** (диссертация Сеник Ю.В., 2005).

**English:** [en/README.md](en/README.md) · [README.en.md](../README.en.md)

## Модули

| Документ | Python | VBA / лист Excel |
|----------|--------|------------------|
| [equilibrium.md](equilibrium.md) | `equilibrium.py`, `carbon.py` | `equilibrium_calc`, `carbon_calc`, `pure_water` — *Ion Equlibrium* |
| [conductivity.md](conductivity.md) | `conductivity.py` | `el_conduct` — *Ion Equlibrium* K13 |
| [electrodialysis.md](electrodialysis.md) | `transport.py`, `ecs.py`, `constants.py` | `T_calc*`, лист *ECS*, *pH(L)*, *pH(i)*, *pH(b)* |

## Быстрый старт

```bash
pip install -r requirements.txt
pytest
```

```python
from ion_model import equilibrium_calc, simulate_channel, load_membrane_constants
```

Обратная совместимость: `from ion_equilibrium import equilibrium_calc` по-прежнему работает.

## Карта пакета

```
ion_model/
  equilibrium.py    # равновесие, pH, γ
  carbon.py         # карбонат при заданном pH
  conductivity.py   # κ (См/м)
  constants.py      # лист Constants
  transport.py      # числа переноса
  ecs.py            # слой, канал, сканирования
  types.py          # dataclass API
```

## Верификация

Регрессионные тесты в `tests/` читают эталонные значения из `ECS_model3_3 N.xls` (xlrd). Критические допуски: pH ±10⁻³, κ ±10⁻⁴ См/м, TN ±10⁻⁴.

## Устаревший файл

[model.md](model.md) — перенаправление сюда; содержимое разбито по трём тематическим файлам выше.
