"""Tests for carbon_speciation and pure_water_composition."""

from __future__ import annotations

import pytest

from ion_model import StrongIonInput, carbon_speciation, pure_water_composition


def test_pure_water_ph_25():
    c = pure_water_composition(25.0)
    ph = -__import__("math").log10(c[9])
    assert ph == pytest.approx(7.0, abs=0.1)


def test_carbon_speciation_total_carbonate_mode():
    strong = StrongIonInput(na=0.003, ca=0.0024, cl=0.0011, so4=0.0003)
    c = carbon_speciation(7.0, strong, 18.0, total_carbonate=0.0065)
    assert c[0] == pytest.approx(0.003, rel=1e-3)
    assert c[5] + c[6] + c[7] == pytest.approx(0.0065, rel=1e-3)
    assert c[9] == pytest.approx(10 ** (-7.0), rel=0.1)
