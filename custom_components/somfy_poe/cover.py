"""Somfy PoE cover platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
    ATTR_POSITION,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_CLOSED, STATE_CLOSING, STATE_OPEN, STATE_OPENING
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SomfyDataUpdateCoordinator
from .api.models import MovementState, Direction

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Somfy cover from config entry."""
    coordinator: SomfyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([SomfyCover(coordinator, entry)])


class SomfyCover(CoordinatorEntity[SomfyDataUpdateCoordinator], CoverEntity):
    """Somfy PoE motor cover entity.

    Design Decisions:
    - Uses coordinator pattern for state updates
    - Supports position, open/close, and stop
    - Maps API states to HA states
    - Handles null positions gracefully
    - Position 0 = fully closed, 100 = fully open
    """

    _attr_device_class = CoverDeviceClass.SHADE
    _attr_has_entity_name = True
    _attr_name = None  # Use device name

    def __init__(
        self,
        coordinator: SomfyDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize cover entity."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{entry.entry_id}_cover"
        self._attr_device_info = coordinator.device_info

        # Determine supported features
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

    @property
    def current_cover_position(self) -> int | None:
        """Return current position (0 closed - 100 open).

        Note: Somfy API uses 0=open/up, 100=closed/down
        We need to invert this for HA (0=closed, 100=open)
        """
        if self.coordinator.data is None:
            return None

        position = self.coordinator.data.position
        if position is None:
            return None

        # Invert position: Somfy 0=open/up, 100=closed/down
        # HA expects: 0=closed, 100=open
        inverted = 100 - position

        # Convert to integer for HA (0-100)
        return round(inverted)

    @property
    def is_closed(self) -> bool | None:
        """Return if cover is closed.

        Returns None if position is unknown.
        """
        position = self.current_cover_position
        if position is None:
            return None

        return position == 0

    @property
    def is_opening(self) -> bool:
        """Return if cover is opening."""
        if self.coordinator.data is None:
            return False

        return self.coordinator.data.is_opening

    @property
    def is_closing(self) -> bool:
        """Return if cover is closing."""
        if self.coordinator.data is None:
            return False

        return self.coordinator.data.is_closing

    @property
    def state(self) -> str:
        """Return the state of the cover."""
        if self.coordinator.data is None:
            return STATE_OPEN

        # Check movement state
        if self.coordinator.data.is_opening:
            return STATE_OPENING
        elif self.coordinator.data.is_closing:
            return STATE_CLOSING

        # If stopped, determine open/closed from position
        position = self.current_cover_position
        if position is not None and position == 0:
            return STATE_CLOSED

        return STATE_OPEN

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        _LOGGER.debug("Opening cover")
        await self.coordinator.async_move_up()

        # Request immediate refresh
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        _LOGGER.debug("Closing cover")
        await self.coordinator.async_move_down()

        # Request immediate refresh
        await self.coordinator.async_request_refresh()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        _LOGGER.debug("Stopping cover")
        await self.coordinator.async_stop()

        # Request immediate refresh
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move cover to a specific position."""
        position = kwargs[ATTR_POSITION]

        # Invert position for Somfy API
        # HA: 0=closed, 100=open
        # Somfy: 0=open/up, 100=closed/down
        somfy_position = 100 - position

        _LOGGER.debug("Setting cover position to %s (Somfy: %s)", position, somfy_position)
        await self.coordinator.async_move_to_position(float(somfy_position))

        # Request immediate refresh
        await self.coordinator.async_request_refresh()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self.async_write_ha_state()
