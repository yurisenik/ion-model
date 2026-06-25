"""Shared fixtures for regression tests against ECS_model3_3 N.xls."""

from __future__ import annotations

from pathlib import Path

import pytest

XLS_PATH = Path(__file__).resolve().parent.parent / "ECS_model3_3 N.xls"


@pytest.fixture(scope="session")
def workbook():
    import xlrd

    if not XLS_PATH.is_file():
        pytest.skip(f"Excel reference not found: {XLS_PATH}")
    return xlrd.open_workbook(str(XLS_PATH))


@pytest.fixture(scope="session")
def ecs_sheet(workbook):
    return workbook.sheet_by_name("ECS")


@pytest.fixture(scope="session")
def ion_sheet(workbook):
    return workbook.sheet_by_name("Ion Equlibrium")
