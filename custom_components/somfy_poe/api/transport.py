"""UDP transport with encryption for Somfy PoE API."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from ..errors import SomfyConnectionError, SomfyTimeoutError

if TYPE_CHECKING:
    from .encryption import SomfyEncryption

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5.0  # seconds


class SomfyTransport:
    """Async UDP transport with AES encryption.

    Design Decisions:
    - Persistent socket for connection reuse
    - Async context manager for lifecycle management
    - Configurable timeout per request
    - Automatic encryption/decryption
    - Thread-safe with asyncio lock
    """

    def __init__(
        self,
        host: str,
        encryption: SomfyEncryption | None,
        port: int = 55055,
        default_timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize transport.

        Args:
            host: Target device IP address
            encryption: SomfyEncryption instance (None for unencrypted)
            port: UDP port (default 55055)
            default_timeout: Default request timeout in seconds
        """
        self._host = host
        self._port = port
        self._encryption = encryption
        self._default_timeout = default_timeout

        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: _SomfyProtocolHandler | None = None
        self._lock = asyncio.Lock()
        self._closed = False

    async def __aenter__(self) -> SomfyTransport:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.close()

    async def connect(self) -> None:
        """Establish UDP connection.

        Raises:
            SomfyConnectionError: If connection fails
        """
        if self._transport is not None:
            return  # Already connected

        try:
            loop = asyncio.get_running_loop()
            self._transport, self._protocol = await loop.create_datagram_endpoint(
                lambda: _SomfyProtocolHandler(),
                remote_addr=(self._host, self._port),
            )
            _LOGGER.debug("Connected to %s:%s", self._host, self._port)
        except OSError as err:
            raise SomfyConnectionError(f"Failed to connect: {err}") from err

    async def close(self) -> None:
        """Close UDP connection."""
        if self._transport is None:
            return

        self._closed = True
        self._transport.close()
        self._transport = None
        self._protocol = None
        _LOGGER.debug("Connection closed")

    async def send_encrypted(
        self,
        plaintext: str,
        timeout: float | None = None,
    ) -> str:
        """Send encrypted message and receive encrypted response.

        Args:
            plaintext: Unencrypted JSON-RPC message
            timeout: Request timeout (uses default if None)

        Returns:
            Decrypted response string

        Raises:
            SomfyConnectionError: If not connected or send fails
            SomfyTimeoutError: If request times out
        """
        if self._transport is None or self._protocol is None:
            raise SomfyConnectionError("Not connected")

        if self._encryption is None:
            raise SomfyConnectionError("Encryption not configured")

        timeout = timeout if timeout is not None else self._default_timeout

        async with self._lock:  # Serialize requests
            try:
                # Encrypt outgoing message
                encrypted_data = self._encryption.encrypt(plaintext)

                _LOGGER.debug("Sending encrypted data (%d bytes)", len(encrypted_data))

                # Send and wait for response
                self._protocol.clear_response()
                self._transport.sendto(encrypted_data)

                encrypted_response = await asyncio.wait_for(
                    self._protocol.wait_for_response(),
                    timeout=timeout,
                )

                # Decrypt response
                response = self._encryption.decrypt(encrypted_response)
                _LOGGER.debug("Received decrypted response: %s", response)

                return response

            except asyncio.TimeoutError as err:
                raise SomfyTimeoutError(
                    f"Request timed out after {timeout}s"
                ) from err
            except OSError as err:
                raise SomfyConnectionError(f"Send failed: {err}") from err

    async def send_unencrypted(
        self,
        message: str,
        timeout: float | None = None,
    ) -> str:
        """Send unencrypted message (for ping/testing).

        Args:
            message: Unencrypted message
            timeout: Request timeout

        Returns:
            Unencrypted response

        Raises:
            SomfyConnectionError: If not connected or send fails
            SomfyTimeoutError: If request times out
        """
        if self._transport is None or self._protocol is None:
            raise SomfyConnectionError("Not connected")

        timeout = timeout if timeout is not None else self._default_timeout

        async with self._lock:
            try:
                data = message.encode("utf-8")

                _LOGGER.debug("Sending unencrypted data: %s", message)

                self._protocol.clear_response()
                self._transport.sendto(data)

                response_data = await asyncio.wait_for(
                    self._protocol.wait_for_response(),
                    timeout=timeout,
                )

                response = response_data.decode("utf-8")
                _LOGGER.debug("Received unencrypted response: %s", response)

                return response

            except asyncio.TimeoutError as err:
                raise SomfyTimeoutError(
                    f"Request timed out after {timeout}s"
                ) from err
            except OSError as err:
                raise SomfyConnectionError(f"Send failed: {err}") from err

    @property
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._transport is not None and not self._closed


class _SomfyProtocolHandler(asyncio.DatagramProtocol):
    """Internal protocol handler for receiving UDP responses."""

    def __init__(self) -> None:
        """Initialize protocol handler."""
        self._response_future: asyncio.Future[bytes] | None = None
        self._transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Called when connection is established."""
        self._transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        """Called when datagram is received."""
        _LOGGER.debug("Received datagram from %s (%d bytes)", addr, len(data))

        if self._response_future and not self._response_future.done():
            self._response_future.set_result(data)

    def error_received(self, exc: Exception) -> None:
        """Called when error occurs."""
        _LOGGER.error("Protocol error: %s", exc)

        if self._response_future and not self._response_future.done():
            self._response_future.set_exception(exc)

    def clear_response(self) -> None:
        """Clear pending response future."""
        self._response_future = asyncio.get_running_loop().create_future()

    async def wait_for_response(self) -> bytes:
        """Wait for response data."""
        if self._response_future is None:
            raise RuntimeError("Must call clear_response() first")

        return await self._response_future
