"""Sensor platform for Body Metrics."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import (
    CONF_PEOPLE,
    CONF_PERSON_NAME,
    DOMAIN,
    SENSOR_KEY_BMI,
    SENSOR_KEY_BODY_FAT,
    SENSOR_KEY_BONE_MASS,
    SENSOR_KEY_CONFIDENCE,
    SENSOR_KEY_IMPEDANCE,
    SENSOR_KEY_MUSCLE_MASS,
    SENSOR_KEY_WATER_PCT,
    SENSOR_KEY_WEIGHT,
)
from .coordinator import ScaleCoordinator

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_KEY_WEIGHT,
        translation_key=SENSOR_KEY_WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_IMPEDANCE,
        translation_key=SENSOR_KEY_IMPEDANCE,
        native_unit_of_measurement="Ω",
        icon="mdi:flash",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_BMI,
        translation_key=SENSOR_KEY_BMI,
        native_unit_of_measurement="kg/m²",
        icon="mdi:human",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_BODY_FAT,
        translation_key=SENSOR_KEY_BODY_FAT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:percent",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_MUSCLE_MASS,
        translation_key=SENSOR_KEY_MUSCLE_MASS,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_WATER_PCT,
        translation_key=SENSOR_KEY_WATER_PCT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-percent",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_BONE_MASS,
        translation_key=SENSOR_KEY_BONE_MASS,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        device_class=SensorDeviceClass.WEIGHT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=SENSOR_KEY_CONFIDENCE,
        translation_key=SENSOR_KEY_CONFIDENCE,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:target",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Body Metrics sensors from a config entry."""
    coordinator: ScaleCoordinator = hass.data[DOMAIN][entry.entry_id]

    people: list[dict[str, Any]] = entry.options.get(CONF_PEOPLE, [])

    entities: list[BodyMetricsSensor] = []
    for person in people:
        person_name = person[CONF_PERSON_NAME]
        person_slug = slugify(person_name)
        for desc in SENSOR_DESCRIPTIONS:
            entities.append(
                BodyMetricsSensor(coordinator, entry, desc, person_slug, person_name)
            )

    async_add_entities(entities)


class BodyMetricsSensor(CoordinatorEntity[ScaleCoordinator], RestoreEntity, SensorEntity):
    """Sensor for a body metric of a specific person."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ScaleCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
        person_slug: str,
        person_name: str,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._person_slug = person_slug
        self._attr_unique_id = f"{entry.entry_id}_{person_slug}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.entry_id}_{person_slug}")},
            name=person_name,
            manufacturer="Body Metrics",
            model="Body Composition",
        )
        self._restored_value: float | None = None

    async def async_added_to_hass(self) -> None:
        """Restore last known state on startup."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unknown", "unavailable", None):
            try:
                self._restored_value = float(last_state.state)
            except (ValueError, TypeError):
                self._restored_value = None

    @property
    def native_value(self) -> Any:
        """Return the sensor value, falling back to restored state."""
        if self.coordinator.data:
            person_data = self.coordinator.data.get("people", {}).get(self._person_slug)
            if person_data:
                value = person_data.get(self.entity_description.key)
                if value is not None:
                    return value
        return self._restored_value
