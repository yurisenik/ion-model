"""Transport numbers vs ECS sheet rows 28/30."""

from __future__ import annotations

import pytest

from ion_model.constants import load_membrane_constants, membrane_diffusion, solution_diffusion
from ion_model.ecs import compute_transport, read_ecs_row
from ion_model.ecs import load_ecs_geometry_from_workbook
from tests.conftest import XLS_PATH


@pytest.fixture(scope="module")
def membrane():
    return load_membrane_constants(XLS_PATH)


def test_transport_first_layer_vs_ph_l(ecs_sheet, membrane):
    geo = load_ecs_geometry_from_workbook(str(XLS_PATH))
    dc = read_ecs_row(ecs_sheet, 17)
    cc = read_ecs_row(ecs_sheet, 22)
    tn = compute_transport(geo, membrane, dc, cc)

    phl = ecs_sheet.book.sheet_by_name("pH(L)")
    assert tn.t_mc_c[0] == pytest.approx(phl.cell_value(2, 2), abs=1e-4)
    assert tn.t_mc_c[1] == pytest.approx(phl.cell_value(2, 3), abs=1e-4)
    assert tn.t_mc_c[2] == pytest.approx(phl.cell_value(2, 4), abs=1e-4)
    assert tn.i_total == pytest.approx(phl.cell_value(2, 5), abs=1e-3)
