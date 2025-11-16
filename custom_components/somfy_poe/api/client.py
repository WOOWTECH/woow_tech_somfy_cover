"""High-level API client for Somfy PoE motors."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .encryption import SomfyEncryption
from .transport import SomfyTransport
from .protocol import SomfyProtocol
from .models import DeviceInfo, PositionStatus
from ..errors import SomfyError
from ..const import (
    METHOD_PING,
    METHOD_STATUS_INFO,
    METHOD_STATUS_POSITION,
    METHOD_MOVE_UP,
    METHOD_MOVE_DOWN,
    METHOD_MOVE_STOP,
    METHOD_MOVE_TO,
)

if TYPE_CHECKING:
    pass

_LOGGER = logging.getLogger(__name__)


class SomfyClient:
    """High-level async API client for Somfy PoE motors.

    Design Decisions:
    - Encapsulates all protocol/transport complexity
    - Context manager for resource management
    - Type-safe return values via models
    - Optional seq parameter support for position tracking
    - Automatic reconnection handling
    """

    def __init__(
        self,
        host: str,
        target_id: str,
        key: str,
        port: int = 55055,
        timeout: float = 5.0,
    ) -> None:
        """Initialize API client.

        Args:
            host: Device IP address
            target_id: 6-character hex target ID
            key: 32-character hex encryption key
            port: UDP port (default 55055)
            timeout: Request timeout in seconds

        Raises:
            ValueError: If parameters are invalid
        """
        self._encryption = SomfyEncryption(key)
        self._protocol = SomfyProtocol(target_id)
        self._transport = SomfyTransport(
            host=host,
            encryption=self._encryption,
            port=port,
            default_timeout=timeout,
        )
        self._host = host
        self._target_id = target_id

        _LOGGER.debug(
            "Initialized SomfyClient: host=%s, target_id=%s, port=%s, timeout=%s",
            host,
            target_id,
            port,
            timeout
        )

    async def __aenter__(self) -> SomfyClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Connect to device."""
        _LOGGER.debug("Connecting to device at %s", self._host)
        await self._transport.connect()

    async def close(self) -> None:
        """Close connection."""
        _LOGGER.debug("Closing connection to %s", self._host)
        await self._transport.close()

    async def ping(self) -> bool:
        """Send unencrypted ping to verify connectivity.

        Returns:
            True if device responds

        Raises:
            SomfyError: If ping fails
        """
        try:
            request = self._protocol.build_request(METHOD_PING)
            response = await self._transport.send_unencrypted(request)
            result = self._protocol.parse_response(response)
            return result.get("result") is True
        except SomfyError:
            raise
        except Exception as err:
            _LOGGER.error("Ping failed: %s", err)
            return False

    async def get_device_info(self) -> DeviceInfo:
        """Get device information.

        Returns:
            DeviceInfo model with device details

        Raises:
            SomfyError: If request fails
        """
        request = self._protocol.build_request(METHOD_STATUS_INFO)
        response = await self._transport.send_encrypted(request)
        result = self._protocol.parse_response(response)

        _LOGGER.debug("Received device info response: %s", result)

        return DeviceInfo.from_api_response(result)

    async def get_position(self) -> PositionStatus:
        """Get current position and state.

        Returns:
            PositionStatus model with current state

        Raises:
            SomfyError: If request fails
        """
        _LOGGER.debug("Requesting position status from device")
        request = self._protocol.build_request(METHOD_STATUS_POSITION)
        response = await self._transport.send_encrypted(request)
        result = self._protocol.parse_response(response)

        _LOGGER.debug("Received position response: %s", result)

        return PositionStatus.from_api_response(result)

    async def move_up(self) -> None:
        """Start moving up (opening).

        Raises:
            SomfyError: If command fails
        """
        request = self._protocol.build_request(METHOD_MOVE_UP)
        response = await self._transport.send_encrypted(request)
        self._protocol.parse_response(response)
        _LOGGER.debug("Move up (open) command sent to target %s", self._target_id)

    async def move_down(self) -> None:
        """Start moving down (closing).

        Raises:
            SomfyError: If command fails
        """
        request = self._protocol.build_request(METHOD_MOVE_DOWN)
        response = await self._transport.send_encrypted(request)
        self._protocol.parse_response(response)
        _LOGGER.debug("Move down (close) command sent to target %s", self._target_id)

    async def stop(self) -> None:
        """Stop movement.

        Raises:
            SomfyError: If command fails
        """
        request = self._protocol.build_request(METHOD_MOVE_STOP)
        response = await self._transport.send_encrypted(request)
        self._protocol.parse_response(response)
        _LOGGER.debug("Stop command sent to target %s", self._target_id)

    async def move_to_position(self, position: float) -> None:
        """Move to specific position.

        Args:
            position: Target position (0-100, up to 3 decimal places)

        Raises:
            ValueError: If position is out of range
            SomfyError: If command fails
        """
        if not 0 <= position <= 100:
            raise ValueError(f"Position must be 0-100, got {position}")

        # Round to 3 decimal places as per API spec
        rounded_position = round(position, 3)

        params = {"position": rounded_position}
        request = self._protocol.build_request(METHOD_MOVE_TO, params)
        response = await self._transport.send_encrypted(request)
        self._protocol.parse_response(response)
        _LOGGER.debug(
            "Move to position command sent: requested=%s, rounded=%s, target=%s",
            position,
            rounded_position,
            self._target_id
        )

    @property
    def is_connected(self) -> bool:
        """Check if client is connected."""
        return self._transport.is_connected

    @property
    def host(self) -> str:
        """Get device host."""
        return self._host

    @property
    def target_id(self) -> str:
        """Get target ID."""
        return self._target_id
