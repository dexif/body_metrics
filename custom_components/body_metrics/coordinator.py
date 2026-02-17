"""DataUpdateCoordinator for Body Metrics."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from .calculations import (
    calc_bmi,
    calc_bmr,
    calc_body_fat_pct,
    calc_bone_mass,
    calc_ideal_weight,
    calc_muscle_mass,
    calc_visceral_fat,
    calc_water_pct,
    get_body_type,
)
from .const import (
    CONF_IMPEDANCE_SENSOR,
    CONF_PEOPLE,
    CONF_PERSON_AGE,
    CONF_PERSON_EXPECTED_IMPEDANCE,
    CONF_PERSON_EXPECTED_WEIGHT,
    CONF_PERSON_HEIGHT,
    CONF_PERSON_NAME,
    CONF_PERSON_SEX,
    CONF_PERSON_TOLERANCE,
    CONF_WEIGHT_SENSOR,
    DEFAULT_EMA_ALPHA,
    DEFAULT_TOLERANCE,
    DOMAIN,
    EVENT_MEASUREMENT,
    SENSOR_KEY_BMI,
    SENSOR_KEY_BMR,
    SENSOR_KEY_BODY_FAT,
    SENSOR_KEY_BODY_TYPE,
    SENSOR_KEY_BONE_MASS,
    SENSOR_KEY_CONFIDENCE,
    SENSOR_KEY_IDEAL_WEIGHT,
    SENSOR_KEY_IMPEDANCE,
    SENSOR_KEY_LAST_MEASUREMENT,
    SENSOR_KEY_MUSCLE_MASS,
    SENSOR_KEY_VISCERAL_FAT,
    SENSOR_KEY_WATER_PCT,
    SENSOR_KEY_WEIGHT,
    SENSOR_KEY_WEIGHT_TREND_MONTH,
    SENSOR_KEY_WEIGHT_TREND_WEEK,
)

_LOGGER = logging.getLogger(__name__)

_UNAVAILABLE_STATES = {"unknown", "unavailable"}

_NUM_RE = re.compile(r"^[\s]*([-+]?\d*\.?\d+)")


def _parse_float(value: str) -> float | None:
    """Parse a float from a string that may contain units (e.g. '75.5 kg')."""
    match = _NUM_RE.match(value)
    if match:
        return float(match.group(1))
    return None


class ScaleCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that reads scale sensors and computes body metrics."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, store: Store
    ) -> None:
        self.entry = entry
        self._store = store
        self._smoothed: dict[str, dict[str, float]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._last_matched: dict[str, float] = {}

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=2),
        )

    async def async_load_history(self) -> None:
        """Load weight history from store."""
        data = await self._store.async_load()
        if data and isinstance(data, dict):
            self._history = data
        else:
            self._history = {}

    def _save_history(self) -> None:
        """Schedule a save of weight history."""
        self._store.async_delay_save(lambda: self._history, 60)

    def _calc_weight_trend(
        self, slug: str, current_weight: float, days: int
    ) -> float | None:
        """Calculate weight change over the given number of days."""
        entries = self._history.get(slug, [])
        if not entries:
            return None

        now = datetime.now(timezone.utc)
        target = now - timedelta(days=days)
        best_entry: dict[str, Any] | None = None
        best_delta = float("inf")

        for entry in entries:
            ts = datetime.fromisoformat(entry["timestamp"])
            delta = abs((ts - target).total_seconds())
            if delta < best_delta:
                best_delta = delta
                best_entry = entry

        if best_entry is None:
            return None

        # Only return trend if the entry is at least half the period old
        entry_ts = datetime.fromisoformat(best_entry["timestamp"])
        if (now - entry_ts).total_seconds() < days * 86400 * 0.5:
            return None

        return round(current_weight - best_entry["weight"], 1)

    async def _async_update_data(self) -> dict[str, Any]:
        weight_entity = self.entry.data.get(CONF_WEIGHT_SENSOR)
        imp_entity = self.entry.data.get(CONF_IMPEDANCE_SENSOR)

        if not weight_entity:
            return self.data or {"people": {}}

        weight_state = self.hass.states.get(weight_entity)
        if not weight_state or weight_state.state in _UNAVAILABLE_STATES:
            return self.data or {"people": {}}

        weight = _parse_float(weight_state.state)
        if weight is None:
            _LOGGER.debug("Cannot parse weight state: %s", weight_state.state)
            return self.data or {"people": {}}

        impedance: float | None = None
        if imp_entity:
            imp_state = self.hass.states.get(imp_entity)
            if imp_state and imp_state.state not in _UNAVAILABLE_STATES:
                impedance = _parse_float(imp_state.state)
                if impedance is None:
                    _LOGGER.debug(
                        "Cannot parse impedance state: %s", imp_state.state
                    )

        people: list[dict[str, Any]] = self.entry.options.get(CONF_PEOPLE, [])

        # Find best matching person
        best: dict[str, Any] | None = None
        best_score = float("inf")

        for person in people:
            expected_weight = person.get(CONF_PERSON_EXPECTED_WEIGHT, 0)
            expected_impedance = person.get(CONF_PERSON_EXPECTED_IMPEDANCE, 0)
            tolerance = person.get(CONF_PERSON_TOLERANCE, DEFAULT_TOLERANCE)

            dw = abs(weight - expected_weight)
            di = abs((impedance or 0) - expected_impedance)
            score = dw * 1.5 + di * 0.02

            if score < tolerance and score < best_score:
                best_score = score
                best = person

        # Preserve previous data for unmatched people
        prev_people: dict[str, dict[str, Any]] = {}
        if self.data:
            prev_people = {
                k: dict(v) for k, v in self.data.get("people", {}).items()
            }
        result: dict[str, Any] = {"people": prev_people}

        if best:
            slug = slugify(best[CONF_PERSON_NAME])
            height = int(best.get(CONF_PERSON_HEIGHT, 170))
            age = int(best.get(CONF_PERSON_AGE, 30))
            sex = best.get(CONF_PERSON_SEX, "male")

            # EMA smoothing
            if slug not in self._smoothed:
                self._smoothed[slug] = {}

            alpha = DEFAULT_EMA_ALPHA
            prev_w = self._smoothed[slug].get("weight", weight)
            smoothed_weight = alpha * weight + (1 - alpha) * prev_w
            self._smoothed[slug]["weight"] = smoothed_weight

            smoothed_impedance = impedance
            if impedance is not None:
                prev_i = self._smoothed[slug].get("impedance", impedance)
                smoothed_impedance = alpha * impedance + (1 - alpha) * prev_i
                self._smoothed[slug]["impedance"] = smoothed_impedance

            confidence = max(0.0, min(100.0, 100.0 - best_score))

            person_data: dict[str, Any] = {
                SENSOR_KEY_WEIGHT: round(smoothed_weight, 2),
                SENSOR_KEY_IMPEDANCE: (
                    round(smoothed_impedance, 1)
                    if smoothed_impedance is not None
                    else None
                ),
                SENSOR_KEY_BMI: calc_bmi(smoothed_weight, height),
                SENSOR_KEY_CONFIDENCE: round(confidence, 1),
                SENSOR_KEY_BMR: calc_bmr(smoothed_weight, height, age, sex),
                SENSOR_KEY_IDEAL_WEIGHT: calc_ideal_weight(height, sex),
            }

            if smoothed_impedance is not None:
                fat_pct = calc_body_fat_pct(
                    smoothed_weight, height, age, sex, smoothed_impedance
                )
                muscle = calc_muscle_mass(
                    smoothed_weight, height, age, sex, smoothed_impedance
                )
                person_data[SENSOR_KEY_BODY_FAT] = fat_pct
                person_data[SENSOR_KEY_MUSCLE_MASS] = muscle
                person_data[SENSOR_KEY_WATER_PCT] = calc_water_pct(
                    smoothed_weight, height, age, sex, smoothed_impedance
                )
                person_data[SENSOR_KEY_BONE_MASS] = calc_bone_mass(
                    smoothed_weight, height, age, sex, smoothed_impedance
                )
                person_data[SENSOR_KEY_VISCERAL_FAT] = calc_visceral_fat(
                    smoothed_weight, height, age, sex
                )
                person_data[SENSOR_KEY_BODY_TYPE] = get_body_type(
                    fat_pct, muscle, smoothed_weight, sex
                )
            else:
                person_data[SENSOR_KEY_BODY_FAT] = None
                person_data[SENSOR_KEY_MUSCLE_MASS] = None
                person_data[SENSOR_KEY_WATER_PCT] = None
                person_data[SENSOR_KEY_BONE_MASS] = None
                person_data[SENSOR_KEY_VISCERAL_FAT] = None
                person_data[SENSOR_KEY_BODY_TYPE] = None

            # Detect new measurement (weight changed noticeably)
            prev_weight = self._last_matched.get(slug)
            now = datetime.now(timezone.utc)
            if prev_weight is None or abs(smoothed_weight - prev_weight) > 0.1:
                self._last_matched[slug] = smoothed_weight

                # Save to history
                if slug not in self._history:
                    self._history[slug] = []
                self._history[slug].append(
                    {"timestamp": now.isoformat(), "weight": round(smoothed_weight, 2)}
                )
                # Keep max 365 entries per person
                if len(self._history[slug]) > 365:
                    self._history[slug] = self._history[slug][-365:]
                self._save_history()

                # Fire event
                self.hass.bus.async_fire(
                    EVENT_MEASUREMENT,
                    {
                        "person": slug,
                        "entry_id": self.entry.entry_id,
                        **{k: v for k, v in person_data.items() if v is not None},
                    },
                )

            person_data[SENSOR_KEY_LAST_MEASUREMENT] = now.isoformat()

            # Weight trends
            person_data[SENSOR_KEY_WEIGHT_TREND_WEEK] = self._calc_weight_trend(
                slug, smoothed_weight, 7
            )
            person_data[SENSOR_KEY_WEIGHT_TREND_MONTH] = self._calc_weight_trend(
                slug, smoothed_weight, 30
            )

            result["people"][slug] = person_data

        return result
