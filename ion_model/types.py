"""Shared types for ion_model package."""

from __future__ import annotations

from dataclasses import dataclass, field

COMPONENT_NAMES = (
    "Na+",
    "Ca2+",
    "Mg2+",
    "Cl-",
    "NO3-",
    "H2CO3",
    "HCO3-",
    "CO3^2-",
    "OH-",
    "H+",
    "SO4^2-",
)

CHARGES = (1, 2, 2, -1, -1, 0, -1, -2, -1, 1, -2)

A_NUM = 6  # anions in conductivity / transport
C_NUM = 4  # cations in conductivity
C_NUM_ED = 3  # cations in ED transport (Na, Ca, H)

# ECS row mapping: 10 columns A-J (indices 0-9)
ECS_ION_NAMES = ("Na+", "Ca2+", "Cl-", "NO3-", "SO42-", "H2CO3", "HCO3-", "CO32-", "OH-", "H+")

# Map ECS 10-vector index -> 11-component index
ECS_TO_11 = (0, 1, 3, 4, 10, 5, 6, 7, 8, 9)


def ecs_to_11(ecs: list[float]) -> list[float]:
    out = [0.0] * 11
    for i, idx in enumerate(ECS_TO_11):
        out[idx] = ecs[i]
    return out


def eleven_to_ecs(c: list[float]) -> list[float]:
    return [c[idx] for idx in ECS_TO_11]


@dataclass
class EquilibriumResult:
    concentrations: list[float]
    ph: float
    activity_coefficients: list[float]
    success: bool


@dataclass
class ECSGeometry:
    """Geometrical and flow parameters (ECS sheet row 2-11)."""

    area_cm2: float  # B2, a
    layer_thickness_cm: float  # B3, L
    channel_height_cm: float  # B4, h
    flow_dc_ml_s: float  # B5, W_DC
    flow_cc_ml_s: float  # B6, W_CC
    current_density_ma_cm2: float  # B7, i
    delta_cm: float  # B9, DBL thickness at CEM
    delta0_cm: float  # I9
    tw: float = 0.01  # B10, H/OH generation at CEM
    twa: float = 0.3  # B11, at AEM
    mixing_ratio: float = 0.9  # J6, W_DC/(W_DC+W_CC)


@dataclass
class MembraneConstants:
    """Constants sheet default values."""

    d_solution: list[float] = field(default_factory=lambda: [1.334e-5, 7.92e-6, 2.032e-5, 1.902e-5, 1.065e-5, 0.0, 1.185e-5, 9.23e-6, 0.0, 0.0, 5.273e-5])
    d_membrane_cation: list[float] = field(default_factory=lambda: [1.334e-5, 7.92e-6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    d_membrane_anion: list[float] = field(default_factory=lambda: [0.0, 0.0, 2.032e-5, 1.902e-5, 1.065e-5, 0.0, 1.185e-5, 9.23e-6, 5.273e-5, 0.0, 0.0])
    kd_anion_mc: list[float] = field(default_factory=lambda: [0.2, 0.2, 0.2, 0.2, 0.2, 0.2])
    k12_h_na: float = 10.0
    k13_h_na: float = 10.0
    q_mc_mmol_cm3: float = 3.0
    tw_arg_a: float = 0.43
    tw_arg_b: float = 0.01375519721736927


@dataclass
class TransportNumbers:
    t_ma_a: list[float]  # AEM anions, length 6
    t_ma_c: list[float]  # AEM cations, length 3
    t_mc_a: list[float]  # CEM anions
    t_mc_c: list[float]  # CEM cations
    i_lim_ma: float = 0.0
    i_lim_mc: float = 0.0
    i_total: float = 0.0  # VBA writes this to ECS B7 after T_calc_lim


@dataclass
class LayerResult:
    dc_out: list[float]  # ECS 10-vector
    cc_out: list[float]
    ph_dc: float
    ph_cc: float
    moles_removed_dc: list[float]  # 11-component n/s


@dataclass
class ChannelPoint:
    length_cm: float
    ph_dc: float
    t_na: float
    t_ca: float
    t_h: float
    current_ma_cm2: float
    tw_cem: float


@dataclass
class ChannelResult:
    points: list[ChannelPoint]
    n_na_avg: float = 0.0
    n_ca_avg: float = 0.0
    n_h_avg: float = 0.0
    final_ph_cc: float = 0.0


@dataclass
class ScanPoint:
    parameter: float
    ph_dc: float
    ph_cc: float
    extra: dict = field(default_factory=dict)
