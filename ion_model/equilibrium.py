"""Ion equilibrium calculation (VBA equilibrium_calc)."""

from __future__ import annotations

import math
from typing import Sequence

from ion_model.types import CHARGES, EquilibriumResult

EPSILON0 = 8.854187817e-12
A_NUM = 6
C_NUM = 4

_KW_TABLE = (
    (0, 0.11), (5, 0.19), (10, 0.3), (15, 0.46), (16, 0.5), (17, 0.55),
    (18, 0.6), (19, 0.65), (20, 0.69), (21, 0.76), (22, 0.81), (23, 0.87),
    (24, 0.93), (25, 1.0), (26, 1.1), (27, 1.17), (28, 1.29), (29, 1.38),
    (30, 1.48), (31, 1.58), (32, 1.7), (33, 1.82), (34, 1.95), (35, 2.09),
    (36, 2.24), (37, 2.4), (38, 2.57), (39, 2.75), (40, 2.95), (50, 5.5),
    (60, 9.55), (70, 15.8), (80, 25.1), (90, 38.0), (100, 55.0),
)


def kw(t_celsius: float) -> float:
    temps = [row[0] for row in _KW_TABLE]
    pkw_values = [row[1] for row in _KW_TABLE]
    sum_kw = 0.0
    for i, ti in enumerate(temps):
        p1 = 1.0
        p2 = 1.0
        for j, tj in enumerate(temps):
            if j == i:
                continue
            p1 *= t_celsius - tj
            p2 *= ti - tj
        sum_kw += p1 / p2 * pkw_values[i]
    return sum_kw * 1e-14


def carbonic_constants(t_celsius: float) -> tuple[float, float, float]:
    t_abs = t_celsius + 273.15
    k1 = 10 ** (-(17052 / t_abs + 215.21 * math.log10(t_abs) - 0.12675 * t_abs - 545.56))
    k2 = 10 ** (-(2909.1 / t_abs - 6.498 + 0.02379 * t_abs))
    return k1, k2, kw(t_celsius)


def fun_no_precip(c: float, kp: Sequence[float], sm: float, sm1: float) -> float:
    return (
        c**4
        + c**3 * (kp[0] - sm1 + sm)
        + c**2 * (kp[0] * kp[1] - kp[0] * sm1 - kp[2])
        - c * (kp[0] * kp[1] * sm1 + kp[2] * kp[0] + sm * kp[0] * kp[1])
        - kp[0] * kp[1] * kp[2]
    )


def calculate_activity_coefficients(
    c_a: list[float],
    c_c: list[float],
    z_a: Sequence[float],
    z_c: Sequence[float],
    t_celsius: float,
) -> tuple[list[float], list[float]]:
    epsilon = 78.54 * (1 - 0.0046 * t_celsius + 0.0000088 * t_celsius**2)
    t_k = t_celsius + 273.15
    a1 = 1825000.0 * (epsilon * EPSILON0 * t_k) ** 1.5
    mu = sum(z_a[i] ** 2 * c_a[i] for i in range(A_NUM)) + sum(
        z_c[i] ** 2 * c_c[i] for i in range(C_NUM)
    )
    mu /= 2.0
    sqrt_mu = math.sqrt(mu) if mu > 0 else 0.0
    f_a, f_c = [], []
    for i in range(A_NUM):
        if sqrt_mu == 0:
            f_a.append(1.0)
        else:
            f_a.append(10 ** (-abs(z_a[i]) * a1 * sqrt_mu / (1 + sqrt_mu)))
    for i in range(C_NUM):
        if sqrt_mu == 0:
            f_c.append(1.0)
        else:
            f_c.append(10 ** (-abs(z_c[i]) * a1 * sqrt_mu / (1 + sqrt_mu)))
    return f_a, f_c


def _bisection_h_plus(a: float, b: float, kp: Sequence[float], sm: float, sm1: float) -> float:
    while True:
        fa = fun_no_precip(a, kp, sm, sm1)
        fb = fun_no_precip(b, kp, sm, sm1)
        if fb == 0.0 or fa == 0.0:
            return b if fb == 0.0 else a
        if abs(a - b) <= 10 ** (-(int(-math.log10(a)) + 14)) * 2:
            return (a + b) / 2
        mid_up = a + (b - a) / 2
        mid_down = b - (b - a) / 2
        if fun_no_precip(mid_up, kp, sm, sm1) * fb < 0:
            a = mid_up
        if fun_no_precip(mid_down, kp, sm, sm1) * fa < 0:
            b = mid_down


def equilibrium_calc(
    volume_l: float,
    temperature_c: float,
    moles_added: Sequence[float],
    initial_concentrations: Sequence[float],
    charges: Sequence[int] = CHARGES,
    max_outer_iterations: int = 50,
) -> EquilibriumResult:
    if len(moles_added) != 11 or len(initial_concentrations) != 11:
        raise ValueError("moles_added and initial_concentrations must have length 11")

    k1, k2, k3 = carbonic_constants(temperature_c)
    m = [initial_concentrations[i] + moles_added[i] / volume_l for i in range(11)]
    f = [1.0] * 11
    sm = m[5] + m[6] + m[7]
    sm1 = m[9] + m[5] - m[7] - m[8]
    a_prev = 1e-15
    c_res = [0.0] * 11

    for _ in range(max_outer_iterations):
        aa = a_prev
        b, a = 10.0, 1e-15
        kp1 = k1 * f[5] / f[9] / f[6]
        kp2 = k2 * f[6] / f[9] / f[7]
        kp3 = k3 / f[9] / f[8]
        kp = (kp1, kp2, kp3)
        if fun_no_precip(a, kp, sm, sm1) * fun_no_precip(b, kp, sm, sm1) > 0:
            return EquilibriumResult([0.0] * 11, 0.0, f, False)
        h_plus = _bisection_h_plus(a, b, kp, sm, sm1)
        c_res[6] = sm / (1 + h_plus / kp1 + kp2 / h_plus)
        c_res[9] = h_plus
        c_res[8] = kp3 / h_plus
        c_res[7] = kp2 * c_res[6] / h_plus
        c_res[5] = h_plus * c_res[6] / kp1
        for i in range(5):
            c_res[i] = m[i]
        c_res[10] = m[10]
        if abs(aa - h_plus) <= 10 ** (-(int(-math.log10(aa)) + 16)) * 2:
            return EquilibriumResult(c_res, -math.log10(c_res[9]), f, True)
        c_c = [c_res[0], c_res[1], c_res[2], c_res[9]]
        c_a = [c_res[3], c_res[4], c_res[10], c_res[6], c_res[7], c_res[8]]
        z_c = [charges[0], charges[1], charges[2], charges[9]]
        z_a = [charges[3], charges[4], charges[10], charges[6], charges[7], charges[8]]
        f_a, f_c = calculate_activity_coefficients(c_a, c_c, z_a, z_c, temperature_c)
        f[0], f[1], f[2], f[9] = f_c[0], f_c[1], f_c[2], f_c[3]
        f[3], f[4], f[10], f[6], f[7], f[8] = f_a[0], f_a[1], f_a[2], f_a[3], f_a[4], f_a[5]
        a_prev = h_plus

    ph = -math.log10(c_res[9]) if c_res[9] > 0 else 0.0
    return EquilibriumResult(c_res, ph, f, True)
