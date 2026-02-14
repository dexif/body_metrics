"""Constants for the Body Metrics integration."""

from __future__ import annotations

DOMAIN = "body_metrics"
PLATFORMS = ["sensor"]

# Config entry data keys
CONF_WEIGHT_SENSOR = "weight_sensor"
CONF_IMPEDANCE_SENSOR = "impedance_sensor"

# Options keys
CONF_PEOPLE = "people"

# Person fields
CONF_PERSON_NAME = "name"
CONF_PERSON_HEIGHT = "height_cm"
CONF_PERSON_AGE = "age"
CONF_PERSON_SEX = "sex"
CONF_PERSON_EXPECTED_WEIGHT = "expected_weight"
CONF_PERSON_EXPECTED_IMPEDANCE = "expected_impedance"
CONF_PERSON_TOLERANCE = "tolerance"

# Sex values
SEX_MALE = "male"
SEX_FEMALE = "female"

# Sensor keys
SENSOR_KEY_WEIGHT = "weight"
SENSOR_KEY_IMPEDANCE = "impedance"
SENSOR_KEY_BMI = "bmi"
SENSOR_KEY_BODY_FAT = "body_fat"
SENSOR_KEY_MUSCLE_MASS = "muscle_mass"
SENSOR_KEY_WATER_PCT = "water_pct"
SENSOR_KEY_BONE_MASS = "bone_mass"
SENSOR_KEY_CONFIDENCE = "confidence"

# Defaults
DEFAULT_TOLERANCE = 8
DEFAULT_EMA_ALPHA = 0.2
