"""The Body Metrics integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store

from .const import DOMAIN, PLATFORMS, SERVICE_REASSIGN_GUEST, STORAGE_KEY, STORAGE_VERSION
from .coordinator import ScaleCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Body Metrics from a config entry."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    coordinator = ScaleCoordinator(hass, entry, store)
    await coordinator.async_load_history()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, SERVICE_REASSIGN_GUEST):

        async def handle_reassign_guest(call: ServiceCall) -> None:
            person = call.data["person"]
            entry_id = call.data.get("entry_id")

            coordinators = hass.data.get(DOMAIN, {})
            if entry_id:
                coord = coordinators.get(entry_id)
                if coord is None:
                    raise HomeAssistantError(
                        f"Config entry '{entry_id}' not found"
                    )
                coord.reassign_guest(person)
            else:
                if not coordinators:
                    raise HomeAssistantError("No body_metrics entries configured")
                for coord in coordinators.values():
                    coord.reassign_guest(person)

        hass.services.async_register(
            DOMAIN, SERVICE_REASSIGN_GUEST, handle_reassign_guest
        )

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_REASSIGN_GUEST)
    return unload_ok
