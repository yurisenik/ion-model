"""Electrodialysis compartment model (ECS sheet)."""

from __future__ import annotations

import math
from dataclasses import replace

from ion_model.constants import membrane_diffusion, solution_diffusion
from ion_model.equilibrium import equilibrium_calc
from ion_model.transport import transport_numbers_from_ecs_state
from ion_model.types import (
    ChannelPoint,
    ChannelResult,
    ECSGeometry,
    LayerResult,
    MembraneConstants,
    ScanPoint,
    TransportNumbers,
    ecs_to_11,
    eleven_to_ecs,
)

FARADAY_MCS = 96500000.0  # mC/mol, VBA CommandButton4
CHARGES_11 = (1, 2, 2, -1, -1, 0, -1, -2, -1, 1, -2)


def _ecs_anions_cations(ecs_dc: list[float]) -> tuple[list[float], list[float]]:
    return (
        [ecs_dc[2], ecs_dc[3], ecs_dc[4], ecs_dc[6], ecs_dc[7], ecs_dc[8]],
        [ecs_dc[0], ecs_dc[1], ecs_dc[9]],
    )


def compute_transport(
    geometry: ECSGeometry,
    membrane: MembraneConstants,
    dc_in: list[float],
    cc_in: list[float],
) -> TransportNumbers:
    d_c, d_a = solution_diffusion(membrane)
    d_c_mc, d_a_mc = membrane_diffusion(membrane)
    c_a, c_c = _ecs_anions_cations(dc_in)
    cb_a, cb_c = _ecs_anions_cations(cc_in)
    return transport_numbers_from_ecs_state(
        c_a, c_c, cb_a, cb_c,
        geometry.current_density_ma_cm2,
        geometry.delta_cm,
        geometry.delta0_cm,
        geometry.tw,
        geometry.twa,
        membrane.q_mc_mmol_cm3,
        d_a, d_c, d_a_mc, d_c_mc,
        membrane.kd_anion_mc,
        membrane.k12_h_na,
        membrane.k13_h_na,
    )


def _moles_removed(
    transport: TransportNumbers,
    geometry: ECSGeometry,
    desalination: int,
) -> list[float]:
    """Moles per second removed from stream (11-component vector)."""
    n = [0.0] * 11
    i = transport.i_total or geometry.current_density_ma_cm2
    a, l_len = geometry.area_cm2, geometry.layer_thickness_cm
    factor = -desalination * i * a * l_len / FARADAY_MCS

    n[0] = factor * (transport.t_mc_c[0] - transport.t_ma_c[0]) / 1
    n[1] = factor * (transport.t_mc_c[1] - transport.t_ma_c[1]) / 2
    n[3] = factor * (transport.t_ma_a[0] - transport.t_mc_a[0]) / 1
    n[4] = factor * (transport.t_ma_a[1] - transport.t_mc_a[1]) / 1
    n[5] = 0.0
    n[6] = factor * (transport.t_ma_a[3] - transport.t_mc_a[3]) / 1
    n[7] = factor * (transport.t_ma_a[4] - transport.t_mc_a[4]) / 2
    n[8] = factor * (transport.t_ma_a[5] - transport.t_mc_a[5]) / 1
    n[9] = factor * (transport.t_mc_c[2] - transport.t_ma_c[2]) / 1
    n[10] = factor * (transport.t_ma_a[2] - transport.t_mc_a[2]) / 2
    return n


def _equilibrate_stream(
    ecs_in: list[float],
    moles_per_s: list[float],
    flow_ml_s: float,
    temperature_c: float,
) -> tuple[list[float], float]:
    c0 = ecs_to_11(ecs_in)
    vol_l_s = flow_ml_s / 1000.0
    result = equilibrium_calc(vol_l_s, temperature_c, moles_per_s, c0, CHARGES_11)
    return eleven_to_ecs(result.concentrations), result.ph


def ecs_layer_step(
    dc_in: list[float],
    cc_in: list[float],
    geometry: ECSGeometry,
    membrane: MembraneConstants,
    transport: TransportNumbers | None = None,
    temperature_c: float = 25.0,
) -> LayerResult:
    if transport is None:
        transport = compute_transport(geometry, membrane, dc_in, cc_in)
    n_dc = _moles_removed(transport, geometry, desalination=1)
    dc_out, ph_dc = _equilibrate_stream(dc_in, n_dc, geometry.flow_dc_ml_s, temperature_c)
    n_cc = _moles_removed(transport, geometry, desalination=-1)
    cc_out, ph_cc = _equilibrate_stream(cc_in, n_cc, geometry.flow_cc_ml_s, temperature_c)
    return LayerResult(dc_out, cc_out, ph_dc, ph_cc, n_dc)


def simulate_channel(
    dc_initial: list[float],
    cc_initial: list[float],
    geometry: ECSGeometry,
    membrane: MembraneConstants,
    *,
    n_layers: int,
    temperature_c: float = 25.0,
    initial_ph_dc: float | None = None,
) -> ChannelResult:
    dc, cc = list(dc_initial), list(cc_initial)
    points: list[ChannelPoint] = []
    sum_na = sum_ca = sum_h = 0.0
    length_prev = 0.0
    geo = geometry
    layer: LayerResult | None = None

    if initial_ph_dc is None:
        initial_ph_dc = -math.log10(dc[9]) if dc[9] > 0 else 7.0
    points.append(
        ChannelPoint(
            length_cm=0.0,
            ph_dc=initial_ph_dc,
            t_na=0.0,
            t_ca=0.0,
            t_h=0.0,
            current_ma_cm2=geo.current_density_ma_cm2,
            tw_cem=geo.tw,
        )
    )

    for j in range(1, n_layers + 1):
        transport = compute_transport(geo, membrane, dc, cc)
        geo = replace(geo, current_density_ma_cm2=transport.i_total)
        layer = ecs_layer_step(dc, cc, geo, membrane, transport=transport, temperature_c=temperature_c)
        dc, cc = layer.dc_out, layer.cc_out
        length = geo.layer_thickness_cm * j
        points.append(
            ChannelPoint(
                length_cm=length,
                ph_dc=layer.ph_dc,
                t_na=transport.t_mc_c[0],
                t_ca=transport.t_mc_c[1],
                t_h=transport.t_mc_c[2],
                current_ma_cm2=transport.i_total,
                tw_cem=geo.tw,
            )
        )
        sum_na += (length - length_prev) * transport.t_mc_c[0]
        sum_ca += (length - length_prev) * transport.t_mc_c[1]
        sum_h += (length - length_prev) * transport.t_mc_c[2]
        length_prev = length

    total_l = geometry.layer_thickness_cm * n_layers
    return ChannelResult(
        points=points,
        n_na_avg=sum_na / total_l if total_l else 0.0,
        n_ca_avg=sum_ca / total_l if total_l else 0.0,
        n_h_avg=sum_h / total_l if total_l else 0.0,
        final_ph_cc=layer.ph_cc if layer is not None else 0.0,
    )


def load_ecs_geometry_from_workbook(xls_path: str) -> ECSGeometry:
    import xlrd

    sh = xlrd.open_workbook(xls_path).sheet_by_name("ECS")
    return ECSGeometry(
        area_cm2=sh.cell_value(1, 1),
        layer_thickness_cm=sh.cell_value(2, 1),
        channel_height_cm=sh.cell_value(3, 1),
        flow_dc_ml_s=sh.cell_value(4, 1),
        flow_cc_ml_s=sh.cell_value(5, 1),
        current_density_ma_cm2=sh.cell_value(6, 1),
        delta_cm=sh.cell_value(8, 1),
        delta0_cm=sh.cell_value(8, 8),
        tw=sh.cell_value(9, 1),
        twa=sh.cell_value(10, 1),
        mixing_ratio=sh.cell_value(5, 9),
    )


def read_ecs_row(sh, row: int) -> list[float]:
    return [sh.cell_value(row - 1, c) for c in range(10)]


def scan_current_density(
    dc_initial: list[float],
    cc_initial: list[float],
    geometry: ECSGeometry,
    membrane: MembraneConstants,
    *,
    i_start: float | None = None,
    i_step: float,
    i_end: float,
    n_layers: int,
    temperature_c: float = 25.0,
) -> list[ScanPoint]:
    """VBA CommandButton6: outlet pH (M40) vs current density."""
    i_beg = geometry.current_density_ma_cm2 if i_start is None else i_start
    results: list[ScanPoint] = []
    j = 1
    while i_beg + j * i_step <= i_end + 1e-12:
        geo = replace(geometry, current_density_ma_cm2=i_beg)
        ch = simulate_channel(
            dc_initial, cc_initial, geo, membrane,
            n_layers=n_layers, temperature_c=temperature_c,
        )
        results.append(ScanPoint(i_beg, ch.points[-1].ph_dc, ch.final_ph_cc))
        j += 1
    return results


def scan_mixing_ratio(
    dc_initial: list[float],
    cc_initial: list[float],
    geometry: ECSGeometry,
    membrane: MembraneConstants,
    *,
    b_start: float | None = None,
    b_step: float,
    b_end: float,
    n_layers: int,
    temperature_c: float = 25.0,
) -> list[ScanPoint]:
    """VBA CommandButton9: outlet pH vs W_DC/(W_DC+W_CC)."""
    b_beg = geometry.mixing_ratio if b_start is None else b_start
    results: list[ScanPoint] = []
    j = 0
    current_b = b_beg
    while b_beg + j * b_step <= b_end + 1e-12:
        w_cc = geometry.flow_dc_ml_s * (1.0 / current_b - 1.0)
        geo = replace(geometry, mixing_ratio=current_b, flow_cc_ml_s=w_cc)
        ch = simulate_channel(
            dc_initial, cc_initial, geo, membrane,
            n_layers=n_layers, temperature_c=temperature_c,
        )
        results.append(
            ScanPoint(
                current_b,
                ch.points[-1].ph_dc,
                ch.final_ph_cc,
                extra={"n_na": ch.n_na_avg, "n_ca": ch.n_ca_avg},
            )
        )
        j += 1
        current_b = b_beg + j * b_step
    return results
