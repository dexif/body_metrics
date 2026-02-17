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
    # LBM cannot exceed body weight
    return min(lbm, weight * 0.95)


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

    # Clamp: bone mass cannot exceed 15% of body weight
    max_bone = min(5.1 if sex == "male" else 4.2, weight * 0.15)
    min_bone = max(0.1, weight * 0.01)
    bone = max(min_bone, min(max_bone, bone))

    return round(bone, 1)


def calc_muscle_mass(
    weight: float, height_cm: float, age: int, sex: str, impedance: float
) -> float:
    """Calculate muscle mass in kg."""
    fat_pct = calc_body_fat_pct(weight, height_cm, age, sex, impedance)
    bone = calc_bone_mass(weight, height_cm, age, sex, impedance)
    muscle = weight - ((fat_pct / 100) * weight) - bone

    # Clamp: muscle mass must stay within reasonable ratio of body weight
    muscle = max(weight * 0.25, min(weight * 0.75, muscle))

    return round(muscle, 1)


def calc_bmr(weight: float, height_cm: float, age: int, sex: str) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor formula."""
    bmr = 10 * weight + 6.25 * height_cm - 5 * age
    if sex == "male":
        bmr += 5
    else:
        bmr -= 161
    return round(max(0.0, bmr))


def calc_visceral_fat(weight: float, height_cm: float, age: int, sex: str) -> float:
    """Calculate visceral fat rating (scale 1-59)."""
    height_m = height_cm / 100.0
    if height_m <= 0:
        return 1.0

    if sex == "male":
        if age <= 30:
            vf = (weight * 0.74 - height_cm * 0.082 + 13.95) * 0.55
        else:
            vf = (weight * 0.74 - height_cm * 0.082 + 13.95) * 0.55 + (age - 30) * 0.1
    else:
        if age <= 30:
            vf = (weight * 0.74 - height_cm * 0.082 + 13.95) * 0.44
        else:
            vf = (weight * 0.74 - height_cm * 0.082 + 13.95) * 0.44 + (age - 30) * 0.07

    return round(max(1.0, min(59.0, vf)))


def calc_ideal_weight(height_cm: float, sex: str) -> float:
    """Calculate ideal weight using the Devine formula."""
    height_in = height_cm / 2.54
    if sex == "male":
        ideal = 50.0 + 2.3 * (height_in - 60)
    else:
        ideal = 45.5 + 2.3 * (height_in - 60)
    return round(max(0.0, ideal), 1)


def get_body_type(
    body_fat_pct: float, muscle_mass: float, weight: float, sex: str
) -> str:
    """Classify body type based on fat percentage and muscle ratio."""
    if weight <= 0:
        return "Balanced"

    muscle_ratio = muscle_mass / weight

    # Fat thresholds depend on sex
    if sex == "male":
        fat_low, fat_high = 15.0, 25.0
        muscle_low, muscle_high = 0.38, 0.46
    else:
        fat_low, fat_high = 22.0, 32.0
        muscle_low, muscle_high = 0.30, 0.37

    if body_fat_pct > fat_high:
        if muscle_ratio >= muscle_high:
            return "Thick-set"
        if muscle_ratio >= muscle_low:
            return "Overweight"
        return "Obese"
    if body_fat_pct >= fat_low:
        if muscle_ratio >= muscle_high:
            return "Balanced-muscular"
        if muscle_ratio >= muscle_low:
            return "Balanced"
        return "Lack of exercise"
    # Low fat
    if muscle_ratio >= muscle_high:
        return "Skinny-muscular"
    if muscle_ratio >= muscle_low:
        return "Balanced-skinny"
    return "Skinny"


def calc_water_pct(
    weight: float, height_cm: float, age: int, sex: str, impedance: float
) -> float:
    """Calculate body water percentage."""
    fat_pct = calc_body_fat_pct(weight, height_cm, age, sex, impedance)
    water = (100 - fat_pct) * 0.7
    coeff = 0.98 if water > 50 else 1.02
    water *= coeff
    return round(max(5.0, min(80.0, water)), 1)
