"""Specific conductivity (VBA el_conduct)."""

from __future__ import annotations

from typing import Sequence

from ion_model.types import A_NUM, C_NUM

_LAMBDA_25_CATION = (50.1, 59.5, 53.06, 349.7)
_LAMBDA_25_ANION = (76.3, 71.4, 50.0, 44.5, 69.3, 197.6)
_TEMP_COEF_CATION = (0.0244, 0.0247, 0.0256, 0.0154)
_TEMP_COEF_ANION = (0.0216, 0.0192, 0.01, 0.01, 0.027, 0.018)
_ION_RADIUS_CATION = (0.33e-9, 0.7e-9, 0.44e-9, 0.1e-9)
_ION_RADIUS_ANION = (0.442e-9, 0.189e-9, 0.189e-9, 1.0e-9, 0.5e-9, 0.4e-9)
_GAMMA_CORRECTION_CATION = (1.0, 2.5, 2.0, 1.4)
_GAMMA_CORRECTION_ANION = (1.0, -0.5, 1.0, 1.0, 2.0, 1.6)
_Z_CATION = (1, 2, 2, 1)
_Z_ANION = (-1, -1, -2, -1, -2, -1)


def concentrations_to_conductivity_arrays(
    concentrations: Sequence[float],
    *,
    excel_vba_mapping: bool = False,
) -> tuple[list[float], list[float]]:
    c = concentrations
    if excel_vba_mapping:
        c_c = [c[0], c[1], c[2], c[8]]
    else:
        c_c = [c[0], c[1], c[2], c[9]]
    c_a = [c[3], c[4], c[10], c[6], c[7], c[8]]
    return c_c, c_a


def el_conduct(c_a: Sequence[float], c_c: Sequence[float], temperature_c: float) -> float:
    if len(c_a) != A_NUM or len(c_c) != C_NUM:
        raise ValueError(f"c_a length {A_NUM}, c_c length {C_NUM} required")
    t_k = temperature_c + 273.15
    epsilon = 78.54 * (1 - 0.0046 * (t_k - 298) + 0.0000088 * (t_k - 298) ** 2)
    eta = 0.00002414 * 10 ** (247.8 / (t_k - 140))
    eq_c = [c_c[i] * abs(_Z_CATION[i]) for i in range(C_NUM)]
    eq_a = [c_a[i] * abs(_Z_ANION[i]) for i in range(A_NUM)]
    lam_c = [_LAMBDA_25_CATION[i] * (1 + _TEMP_COEF_CATION[i] * (t_k - 298)) for i in range(C_NUM)]
    lam_a = [_LAMBDA_25_ANION[i] * (1 + _TEMP_COEF_ANION[i] * (t_k - 298)) for i in range(A_NUM)]
    q_bin = [[0.0] * A_NUM for _ in range(C_NUM)]
    for i in range(C_NUM):
        for j in range(A_NUM):
            zi, zj = _Z_CATION[i], _Z_ANION[j]
            q_bin[i][j] = (
                abs(zi * zj) / (abs(zi) + abs(zj)) * (lam_c[i] + lam_a[j])
                / (abs(zi) * lam_c[i] + abs(zj) * lam_a[j])
            )
    w_bin = [[abs(_Z_CATION[i] * _Z_ANION[j]) * q / (1 + q**0.5)
              for j, q in enumerate(q_bin[i])] for i in range(C_NUM)]
    w_c = []
    for i in range(C_NUM):
        num = sum(w_bin[i][j] * eq_a[j] for j in range(A_NUM))
        den = sum(eq_a)
        w_c.append((num / den if den else 0.0) * _GAMMA_CORRECTION_CATION[i])
    w_a = []
    for j in range(A_NUM):
        num = sum(w_bin[i][j] * eq_c[i] for i in range(C_NUM))
        den = sum(eq_c)
        w_a.append((num / den if den else 0.0) * _GAMMA_CORRECTION_ANION[j])
    gamma = sum(eq_c[i] * abs(_Z_CATION[i]) for i in range(C_NUM))
    gamma += sum(eq_a[j] * abs(_Z_ANION[j]) for j in range(A_NUM))
    gamma **= 0.5
    kappa_dh = 5029000000.0 * (gamma / 2**0.5) / ((epsilon * t_k) ** 0.5) * 100
    total = 0.0
    for i in range(C_NUM):
        alfa = 1970000.0 * w_c[i] / (epsilon * t_k) ** 1.5
        betta = 28.98 * abs(_Z_CATION[i]) / (10 * eta * (epsilon * t_k) ** 0.5)
        lam_eq = lam_c[i] - (alfa * lam_c[i] + betta) * gamma / (1 + kappa_dh * _ION_RADIUS_CATION[i])
        total += lam_eq * eq_c[i]
    for j in range(A_NUM):
        alfa = 1970000.0 * w_a[j] / (epsilon * t_k) ** 1.5
        betta = 28.98 * abs(_Z_ANION[j]) / (10 * eta * (epsilon * t_k) ** 0.5)
        lam_eq = lam_a[j] - (alfa * lam_a[j] + betta) * gamma / (1 + kappa_dh * _ION_RADIUS_ANION[j])
        total += lam_eq * eq_a[j]
    return total / 10.0


def equilibrium_conductivity(
    concentrations: Sequence[float],
    temperature_c: float,
    *,
    excel_vba_mapping: bool = False,
) -> float:
    c_c, c_a = concentrations_to_conductivity_arrays(
        concentrations, excel_vba_mapping=excel_vba_mapping
    )
    return el_conduct(c_a, c_c, temperature_c)
