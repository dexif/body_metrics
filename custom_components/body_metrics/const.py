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
SENSOR_KEY_BMR = "bmr"
SENSOR_KEY_VISCERAL_FAT = "visceral_fat"
SENSOR_KEY_IDEAL_WEIGHT = "ideal_weight"
SENSOR_KEY_BODY_TYPE = "body_type"
SENSOR_KEY_LAST_MEASUREMENT = "last_measurement"
SENSOR_KEY_WEIGHT_TREND_WEEK = "weight_trend_week"
SENSOR_KEY_WEIGHT_TREND_MONTH = "weight_trend_month"

# Storage
STORAGE_KEY = "body_metrics.history"
STORAGE_VERSION = 1

# Events
EVENT_MEASUREMENT = "body_metrics_measurement"

# Guest
GUEST_SLUG = "guest"
GUEST_NAME = "Guest"
EVENT_GUEST_MEASUREMENT = "body_metrics_guest_measurement"
GUEST_MIN_WEIGHT = 10.0  # ignore readings under 10 kg (noise / pets)

# Defaults
DEFAULT_TOLERANCE = 8
DEFAULT_EMA_ALPHA = 0.2
