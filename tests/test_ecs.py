"""Electrodialysis layer and channel vs ECS / pH(L)."""

from __future__ import annotations

import pytest

from ion_model.constants import load_membrane_constants
from ion_model.ecs import (
    ecs_layer_step,
    load_ecs_geometry_from_workbook,
    read_ecs_row,
    scan_current_density,
    scan_mixing_ratio,
    simulate_channel,
    compute_transport,
)
from tests.conftest import XLS_PATH


@pytest.fixture(scope="module")
def membrane():
    return load_membrane_constants(XLS_PATH)


def test_one_layer_ph(ecs_sheet, membrane):
    geo = load_ecs_geometry_from_workbook(str(XLS_PATH))
    dc = read_ecs_row(ecs_sheet, 17)
    cc = read_ecs_row(ecs_sheet, 22)
    phl = ecs_sheet.book.sheet_by_name("pH(L)")
    tn = compute_transport(geo, membrane, dc, cc)
    from dataclasses import replace

    geo = replace(geo, current_density_ma_cm2=tn.i_total)
    layer = ecs_layer_step(dc, cc, geo, membrane, transport=tn)
    assert layer.ph_dc == pytest.approx(phl.cell_value(2, 1), abs=1e-3)


def test_channel_ph_profile(ecs_sheet, membrane):
    geo = load_ecs_geometry_from_workbook(str(XLS_PATH))
    dc = read_ecs_row(ecs_sheet, 17)
    cc = read_ecs_row(ecs_sheet, 22)
    ph0 = ecs_sheet.cell_value(16, 12)
    n_layers = int(ecs_sheet.cell_value(44, 2))
    phl = ecs_sheet.book.sheet_by_name("pH(L)")

    ch = simulate_channel(dc, cc, geo, membrane, n_layers=n_layers, initial_ph_dc=ph0)
    for row, point in enumerate(ch.points):
        expected = phl.cell_value(row + 1, 1)
        assert point.ph_dc == pytest.approx(expected, abs=1e-3), f"L={point.length_cm}"


def test_scan_current_outlet_stable(ecs_sheet, membrane):
    geo = load_ecs_geometry_from_workbook(str(XLS_PATH))
    dc = read_ecs_row(ecs_sheet, 17)
    cc = read_ecs_row(ecs_sheet, 22)
    n = int(ecs_sheet.cell_value(44, 2))
    pts = scan_current_density(
        dc, cc, geo, membrane,
        i_step=ecs_sheet.cell_value(44, 6),
        i_end=geo.current_density_ma_cm2 + ecs_sheet.cell_value(44, 6) * 2,
        n_layers=n,
    )
    assert len(pts) >= 2
    assert pts[0].ph_dc == pytest.approx(6.267726, abs=1e-3)


def test_scan_mixing_cc_ph_increases_with_b(ecs_sheet, membrane):
    geo = load_ecs_geometry_from_workbook(str(XLS_PATH))
    dc = read_ecs_row(ecs_sheet, 17)
    cc = read_ecs_row(ecs_sheet, 22)
    n = int(ecs_sheet.cell_value(44, 2))
    pts = scan_mixing_ratio(
        dc, cc, geo, membrane,
        b_start=0.3,
        b_step=0.2,
        b_end=0.7,
        n_layers=n,
    )
    assert len(pts) >= 2
    assert pts[0].ph_cc < pts[-1].ph_cc
