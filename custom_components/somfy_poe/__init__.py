"""The Somfy PoE Motor integration."""
from __future__ import annotations

import logging

# Allow importing API modules for testing without Home Assistant installed
try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import Platform
    from homeassistant.core import HomeAssistant

    from .api.client import SomfyClient
    from .const import DOMAIN, CONF_HOST, CONF_TARGET_ID, CONF_KEY
    from .coordinator import SomfyDataUpdateCoordinator

    PLATFORMS: list[Platform] = [Platform.COVER]
except ImportError:
    # Running in test mode without Home Assistant
    pass

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Somfy PoE Motor from a config entry."""
    # Create API client
    client = SomfyClient(
        host=entry.data[CONF_HOST],
        target_id=entry.data[CONF_TARGET_ID],
        key=entry.data[CONF_KEY],
    )

    # Connect to device
    try:
        await client.connect()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.error("Failed to connect to device: %s", err)
        return False

    # Create coordinator
    coordinator = SomfyDataUpdateCoordinator(
        hass=hass,
        client=client,
        entry_data=entry.data,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Fetch device info for device registry
    try:
        await coordinator.async_get_device_info()
    except Exception as err:  # pylint: disable=broad-except
        _LOGGER.warning("Failed to fetch device info: %s", err)

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Close client connection
        coordinator: SomfyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.client.close()

        # Remove coordinator
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
