"""Body composition calculation functions (Mi Scale formulas)."""

from __future__ import annotations


def calc_bmi(weight: float, height_cm: float) -> float:
    """Calculate Body Mass Index."""
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 0.0
    return round(weight / (height_m**2), 1)


def _lbm_coefficient(
    weight: float, height_cm: float, age: int, impedance: float
) -> float:
    """Calculate Lean Body Mass coefficient."""
    lbm = (height_cm * 9.058 / 100) * (height_cm / 100)
    lbm += weight * 0.32 + 12.226
    lbm -= impedance * 0.0068
    lbm -= age * 0.0542
    return lbm


def calc_body_fat_pct(
    weight: float, height_cm: float, age: int, sex: str, impedance: float
) -> float:
    """Calculate body fat percentage using BIA."""
    if weight <= 0:
        return 0.0
    lbm = _lbm_coefficient(weight, height_cm, age, impedance)
    coeff = 0.055 if sex == "male" else 0.025
    fat_pct = (
        1.0 - (((lbm - (impedance * coeff / 100 * (30 - age))) / weight) * 1.1)
    ) * 100
    return round(max(3.0, min(60.0, fat_pct)), 1)


def calc_bone_mass(
    weight: float, height_cm: float, age: int, sex: str, impedance: float
) -> float:
    """Calculate bone mass in kg."""
    lbm = _lbm_coefficient(weight, height_cm, age, impedance)
    base = 0.18016894 if sex == "male" else 0.245691014
    bone = (base - (lbm * 0.05158)) * -1

    if bone > 2.2:
        bone += 0.1
    else:
        bone -= 0.1

    if sex == "male":
        bone = max(1.5, min(5.1, bone))
    else:
        bone = max(0.8, min(4.2, bone))

    return round(bone, 1)


def calc_muscle_mass(
    weight: float, height_cm: float, age: int, sex: str, impedance: float
) -> float:
    """Calculate muscle mass in kg."""
    fat_pct = calc_body_fat_pct(weight, height_cm, age, sex, impedance)
    bone = calc_bone_mass(weight, height_cm, age, sex, impedance)
    muscle = weight - ((fat_pct / 100) * weight) - bone

    if sex == "male":
        muscle = max(30.0, min(120.0, muscle))
    else:
        muscle = max(20.0, min(100.0, muscle))

    return round(muscle, 1)


def calc_water_pct(
    weight: float, height_cm: float, age: int, sex: str, impedance: float
) -> float:
    """Calculate body water percentage."""
    fat_pct = calc_body_fat_pct(weight, height_cm, age, sex, impedance)
    water = (100 - fat_pct) * 0.7
    coeff = 0.98 if water > 50 else 1.02
    water *= coeff
    return round(max(5.0, min(80.0, water)), 1)
