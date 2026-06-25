"""Load membrane and solution constants from Excel or defaults."""

from __future__ import annotations

from pathlib import Path

from ion_model.types import MembraneConstants

# Ion order in Constants sheet columns A-J: Na, Ca, Cl, NO3, SO4, _, HCO3, CO3, OH, H
_SHEET_ION_COLS = list(range(10))


def default_membrane_constants() -> MembraneConstants:
    return MembraneConstants()


def load_membrane_constants(xls_path: str | Path | None = None) -> MembraneConstants:
    if xls_path is None:
        return default_membrane_constants()
    import xlrd

    wb = xlrd.open_workbook(str(xls_path))
    sh = wb.sheet_by_name("Constants")

    def row_vals(r: int) -> list[float]:
        out = []
        for c in _SHEET_ION_COLS:
            v = sh.cell_value(r, c)
            out.append(float(v) if v != "" else 0.0)
        return out

    mc = default_membrane_constants()
    mc.d_solution = row_vals(4)  # row 5
    d_mc_row = row_vals(6)  # row 7
    mc.d_membrane_cation = [d_mc_row[0], d_mc_row[1], 0, 0, 0, 0, 0, 0, 0, 0, d_mc_row[9]]
    mc.d_membrane_anion = [0, 0, d_mc_row[2], d_mc_row[3], d_mc_row[4], 0, d_mc_row[6], d_mc_row[7], d_mc_row[8], 0, 0]
    mc.kd_anion_mc = [
        float(sh.cell_value(8, c)) if sh.cell_value(8, c) != "" else 0.2
        for c in (2, 3, 4, 6, 7, 8)
    ]
    mc.k12_h_na = float(sh.cell_value(10, 0))
    mc.k13_h_na = float(sh.cell_value(10, 9)) if sh.cell_value(10, 9) != "" else 10.0
    mc.q_mc_mmol_cm3 = float(sh.cell_value(20, 1))
    mc.tw_arg_a = float(sh.cell_value(24, 1))
    mc.tw_arg_b = float(sh.cell_value(24, 2))
    return mc


def solution_diffusion(mc: MembraneConstants) -> tuple[list[float], list[float]]:
    """D_c (3) and D_a (6) for transport — Na, Ca, H and Cl..OH."""
    d = mc.d_solution
    d_c = [d[0], d[1], d[9]]
    d_a = [d[2], d[3], d[4], d[6], d[7], d[8]]
    return d_c, d_a


def membrane_diffusion(mc: MembraneConstants) -> tuple[list[float], list[float]]:
    full = [0.0] * 11
    for i, v in enumerate(mc.d_membrane_cation):
        if v:
            full[i] = v
    for i, v in enumerate(mc.d_membrane_anion):
        if v:
            full[i] = v
    d_c = [full[0], full[1], mc.d_solution[9]]
    d_a = [full[3], full[4], full[10], full[6], full[7], full[8]]
    return d_c, d_a
