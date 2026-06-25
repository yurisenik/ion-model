"""Carbonate speciation helpers (VBA carbon_calc, pure_water)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ion_model.equilibrium import calculate_activity_coefficients, carbonic_constants, kw

A_NUM = 6
C_NUM = 4
N_NUM = 1

_Z_C = (1, 2, 2, 1)
_Z_A = (-1, -1, -2, -1, -2, -1)


@dataclass
class StrongIonInput:
    na: float = 0.0
    ca: float = 0.0
    mg: float = 0.0
    cl: float = 0.0
    no3: float = 0.0
    so4: float = 0.0


def _to_11(
    strong: StrongIonInput,
    h2co3: float,
    hco3: float,
    co3: float,
    oh: float,
    h: float,
) -> list[float]:
    return [
        strong.na, strong.ca, strong.mg, strong.cl, strong.no3,
        h2co3, hco3, co3, oh, h, strong.so4,
    ]


def pure_water_composition(temperature_c: float) -> list[float]:
    """Return 11-component vector for pure water at temperature."""
    k3 = kw(temperature_c)
    c0_c = [0.0, 0.0, 0.0, math.sqrt(k3)]
    c0_a = [0.0, 0.0, 0.0, 0.0, 0.0, k3 / c0_c[3]]
    f_a, f_c = [1.0] * A_NUM, [1.0] * C_NUM
    while True:
        f_a, f_c = calculate_activity_coefficients(c0_a, c0_c, _Z_A, _Z_C, temperature_c)
        kp3 = k3 / f_a[5] / f_c[3]
        ch = math.sqrt(kp3)
        delta = 10 ** (-(int(-math.log10(ch)) + 16)) * 2
        if abs(ch - c0_c[3]) < delta:
            break
        c0_c[3] = ch
        c0_a[5] = kp3 / c0_c[3]
    return _to_11(StrongIonInput(), 0.0, 0.0, 0.0, c0_a[5], c0_c[3])


def carbon_speciation(
    ph: float,
    strong: StrongIonInput,
    temperature_c: float,
    *,
    total_carbonate: float | None = None,
    hco3: float | None = None,
) -> list[float]:
    """
    Distribute carbonate species at fixed pH and strong electrolytes.

    One of ``total_carbonate`` (Cc mode) or ``hco3`` (fixed bicarbonate mode) required.
    """
    if (total_carbonate is None) == (hco3 is None):
        raise ValueError("Specify exactly one of total_carbonate or hco3")

    k1, k2, k3 = carbonic_constants(temperature_c)
    c0_c = [strong.na, strong.ca, strong.mg, 10 ** (-ph)]
    c0_a = [strong.cl, strong.no3, strong.so4, 0.0, 0.0, 0.0]
    c0_n = [0.0]
    f_a, f_c, f_n = [1.0] * A_NUM, [1.0] * C_NUM, [1.0] * N_NUM
    c_carbcalc = c0_c[3]

    while True:
        kp1 = k1 * f_n[0] / f_c[3] / f_a[3]
        kp2 = k2 * f_a[3] / f_c[3] / f_a[4]
        kp3 = k3 / f_c[3] / f_a[5]
        c0_c[3] = 10 ** (-ph) / f_c[3]
        if total_carbonate is not None:
            cc = total_carbonate
            c0_n[0] = cc / (1 + kp1 * kp2 / c0_c[3] ** 2 + kp1 / c0_c[3])
            c0_a[3] = kp1 * c0_n[0] / c0_c[3]
            c0_a[4] = c0_a[3] * kp2 / c0_c[3]
        else:
            c0_a[3] = hco3  # type: ignore[arg-type]
            c0_n[0] = c0_c[3] * c0_a[3] / kp1
            c0_a[4] = kp2 * c0_a[3] / c0_c[3]
            cc = c0_n[0] + c0_a[3] + c0_a[4]
        c0_a[5] = kp3 / c0_c[3]
        delta = 10 ** (-(int(-math.log10(c0_c[3])) + 16)) * 2
        if abs(c_carbcalc - c0_c[3]) <= delta:
            break
        f_a, f_c = calculate_activity_coefficients(c0_a, c0_c, _Z_A, _Z_C, temperature_c)
        c_carbcalc = c0_c[3]

    return _to_11(strong, c0_n[0], c0_a[3], c0_a[4], c0_a[5], c0_c[3])
