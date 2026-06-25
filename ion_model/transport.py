"""Transport numbers in ED membranes (VBA T_calc*)."""

from __future__ import annotations

import math
from typing import Sequence

from ion_model.types import TransportNumbers

F_MA_CM2 = 96500.0  # mC/mmol in VBA
Z_A_ED = (-1.0, -1.0, -2.0, -1.0, -2.0, -1.0)
Z_C_ED = (1.0, 2.0, 1.0)
A_NUM = 6
C_NUM_ED = 3


def tw_func(i: float, i_lim: float, *, arg_a: float, arg_b: float) -> float:
    return arg_b * (math.exp(arg_a * i / i_lim) - 1) if i_lim else 0.0


def t_calc_zero_current(
    c_a_in: Sequence[float],
    c_c_in: Sequence[float],
    q_mc: float,
    d_a_mc: Sequence[float],
    d_c_mc: Sequence[float],
    kd_a_mc: Sequence[float],
    k12_c_mc: float,
    k13_c_mc: float,
) -> tuple[list[float], list[float], list[float], list[float]]:
    """Return T_MC_c_0, T_MC_a_0, T_MA_c_0, T_MA_a_0."""
    teta_a_mc = [kd_a_mc[i] * c_a_in[i] ** 2 / q_mc for i in range(A_NUM)]
    gamma = [Z_C_ED[i] * c_c_in[i] / abs(Z_A_ED[0]) / c_a_in[0] for i in range(C_NUM_ED)]
    temp_a = k12_c_mc * k12_c_mc * gamma[2] / gamma[0] / gamma[0]
    t_sum = sum(teta_a_mc)
    teta_c_mc_1 = (
        (gamma[2] / gamma[0] - 1)
        + math.sqrt((1 - gamma[2] / gamma[0]) ** 2 + 4 * temp_a * (t_sum + 1))
    ) / 2 / temp_a
    teta_c_mc = [
        teta_c_mc_1,
        1 + t_sum - teta_c_mc_1 * (1 - gamma[2] / gamma[0]),
        gamma[2] / gamma[0] * teta_c_mc_1,
    ]
    denom = sum(
        d_c_mc[i] * Z_C_ED[i] ** 2 * teta_c_mc[i] for i in range(C_NUM_ED)
    ) + sum(d_a_mc[i] * Z_A_ED[i] ** 2 * teta_a_mc[i] for i in range(A_NUM))
    t_mc_c = [(d_c_mc[i] * Z_C_ED[i] ** 2 * teta_c_mc[i]) / denom for i in range(C_NUM_ED)]
    t_mc_a = [(d_a_mc[i] * Z_A_ED[i] ** 2 * teta_a_mc[i]) / denom for i in range(A_NUM)]
    t_ma_a = [0.0] * A_NUM
    t_ma_c = [0.0, 0.0, 1.0]
    return t_mc_c, t_mc_a, t_ma_c, t_ma_a


def t_calc_lim_current_no_counterions(
    c_a_in: Sequence[float],
    c_c_in: Sequence[float],
    d_a: Sequence[float],
    d_c: Sequence[float],
    delta_0: float,
    tw: float,
    twa: float,
) -> tuple[list[float], list[float], list[float], float, float]:
    """
    Limiting transport numbers (no counterions model).

    Returns T_MC_c_lim, T_MA_a_lim, i_concurA, i_lim_mc, i_tot.
    """
    i_concur = [
        abs(z_a) * F_MA_CM2 * d_a[i] * c_a_in[i] * (1 - z_a) / delta_0
        for i, z_a in enumerate(Z_A_ED)
    ]
    i_tot_tmp, i_tot = -1.0, 0.0
    c_tot = sum(Z_C_ED[i] * c_c_in[i] for i in range(C_NUM_ED))
    while abs(i_tot_tmp - i_tot) > (i_tot / 1000 if i_tot else 1e-9):
        i_c = [
            abs(Z_C_ED[i]) * F_MA_CM2 * d_c[i] * c_c_in[i] / delta_0 * (1 + Z_C_ED[i])
            + (d_c[i] * Z_C_ED[i] * c_c_in[i] / (d_a[5] * c_tot) * tw * i_tot if i < 2 else 0.0)
            for i in range(C_NUM_ED)
        ]
        i_lim_mc = sum(i_c)
        i_w = tw / (1 - tw) * i_lim_mc if tw != 1 else 0.0
        i_tot_tmp = i_tot
        i_tot = i_lim_mc + i_w

    t_mc_c = [
        i_c[0] / i_tot,
        i_c[1] / i_tot,
        (i_c[2] + i_w) / i_tot,
    ]
    i_wa = twa * i_tot
    sum_da = (
        d_a[0] * c_a_in[0] * Z_A_ED[0] ** 2
        + d_a[1] * c_a_in[1] * Z_A_ED[1] ** 2
        + d_a[2] * c_a_in[2] * Z_A_ED[2] ** 2
        + d_a[3] * c_a_in[3] * Z_A_ED[3] ** 2
        + d_a[4] * c_a_in[4] * Z_A_ED[4] ** 2
    ) / (d_c[2] * c_tot)
    sum_iconcur = sum(i_concur)
    delta_ca = i_wa * (((1 - twa) / twa if twa else 0) - sum_da) / sum_iconcur if sum_iconcur else 0.0
    t_ma_a = [0.0] * A_NUM
    for i in range(A_NUM - 1):
        t_ma_a[i] = (
            delta_ca * i_concur[i]
            + (Z_A_ED[i] ** 2) * d_a[i] * c_a_in[i] * i_wa / (d_c[2] * c_tot)
        ) / i_tot
    t_ma_a[5] = (delta_ca * i_concur[5] + i_wa) / i_tot
    return t_mc_c, t_ma_a, i_concur, i_lim_mc, i_tot


def t_calc_no_counterions(
    c_a_in: Sequence[float],
    c_c_in: Sequence[float],
    cb_a_in: Sequence[float],
    cb_c_in: Sequence[float],
    q_mc: float,
    d_a_mc: Sequence[float],
    d_c_mc: Sequence[float],
    d_a: Sequence[float],
    d_c: Sequence[float],
    delta_0: float,
    delta_00: float,
    i: float,
    kd_a_mc: Sequence[float],
    k12_c_mc: float,
    k13_c_mc: float,
    tw: float,
    twa: float,
) -> TransportNumbers:
    """ECS CommandButton3 transport number calculation."""
    i_lim_ma = 0.0
    t_mc_c_lim, t_ma_a_lim, _, i_lim_mc, i_tot = t_calc_lim_current_no_counterions(
        c_a_in, c_c_in, d_a, d_c, delta_0, tw, twa
    )
    t_mc_a_lim = [0.0] * A_NUM
    t_ma_c_lim = [0.0, 0.0, 0.0]

    if i < i_lim_ma:
        i_pr = i / i_lim_ma if i_lim_ma else 0.0
        t_ma_a = [(t_ma_a_lim[n] - 0.0) * i_pr for n in range(A_NUM)]
        t_ma_c = [(t_ma_c_lim[n] - (0.0 if n < 2 else 1.0)) * i_pr + (0.0 if n < 2 else 1.0) for n in range(C_NUM_ED)]
    else:
        t_ma_a = list(t_ma_a_lim)
        t_ma_c = list(t_ma_c_lim)

    t_mc_a = list(t_mc_a_lim)
    t_mc_c = list(t_mc_c_lim)

    return TransportNumbers(
        t_ma_a=t_ma_a,
        t_ma_c=t_ma_c,
        t_mc_a=t_mc_a,
        t_mc_c=t_mc_c,
        i_lim_ma=i_lim_ma,
        i_lim_mc=i_lim_mc,
        i_total=i_tot,
    )


def transport_numbers_from_ecs_state(
    c_a_in: Sequence[float],
    c_c_in: Sequence[float],
    cb_a_in: Sequence[float],
    cb_c_in: Sequence[float],
    current_density: float,
    delta_cm: float,
    delta0_cm: float,
    tw: float,
    twa: float,
    q_mc: float,
    d_a: Sequence[float],
    d_c: Sequence[float],
    d_a_mc: Sequence[float],
    d_c_mc: Sequence[float],
    kd_a_mc: Sequence[float],
    k12: float,
    k13: float,
) -> TransportNumbers:
    return t_calc_no_counterions(
        c_a_in, c_c_in, cb_a_in, cb_c_in, q_mc,
        d_a_mc, d_c_mc, d_a, d_c,
        delta_cm, delta0_cm, current_density,
        kd_a_mc, k12, k13, tw, twa,
    )
