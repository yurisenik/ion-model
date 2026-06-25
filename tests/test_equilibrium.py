"""Regression tests for equilibrium_calc."""

from __future__ import annotations

import pytest

from ion_model import equilibrium_calc


def test_excel_equilibrium_ph_and_success():
    c0 = [0.0] * 11
    n = [0.0] * 11
    n[0] = 0.003
    n[1] = 0.0024
    n[3] = 0.0011
    n[10] = 0.0003
    n[5] = 0.0065
    n[8] = 0.0061

    result = equilibrium_calc(1.0, 18.0, n, c0)
    assert result.success
    assert result.ph == pytest.approx(7.579402, abs=1e-5)

