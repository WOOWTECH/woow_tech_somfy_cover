"""Phase 0b: Test unencrypted ping with specific targetID instead of wildcard."""
import asyncio
import sys
import json

# Minimal UDP test - no imports from our codebase


async def test_ping_specific_target():
    """Test unencrypted ping with specific targetID instead of '*'."""
    # Configuration
    HOST = "10.1.1.10"
    PORT = 55055
    TARGET_ID = "160326"  # Your specific target ID

    # Command with specific targetID (not wildcard)
    ping_command = {
        "method": "status.ping",
        "params": {
            "targetID": TARGET_ID
        },
        "id": 0
    }

    print(f"Testing unencrypted ping to {HOST}:{PORT}")
    print(f"Using specific targetID: {TARGET_ID}")
    print("-" * 50)
    print(f"Command:")
    print(json.dumps(ping_command, indent=2))
    print("-" * 50)

    try:
        # Create UDP socket
        loop = asyncio.get_running_loop()
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: MinimalProtocolHandler(),
            remote_addr=(HOST, PORT),
        )

        try:
            # Convert to JSON string (compact format)
            message = json.dumps(ping_command, separators=(",", ":"))
            print(f"\nJSON payload: {message}")

            # Send unencrypted
            data = message.encode("utf-8")
            print(f"Sending {len(data)} bytes unencrypted...")
            transport.sendto(data)

            # Wait for response (5 second timeout)
            print("Waiting for response...")
            response_data = await asyncio.wait_for(
                protocol.wait_for_response(),
                timeout=5.0,
            )

            # Decode response
            response = response_data.decode("utf-8")
            print(f"\nReceived response: {response}")

            # Parse response
            response_obj = json.loads(response)
            print(f"Parsed response:")
            print(json.dumps(response_obj, indent=2))

            # Check result
            if response_obj.get("result") is True:
                print("\n✓ Unencrypted ping with specific targetID works!")
                return True
            else:
                print(f"\n✗ Unexpected result: {response_obj}")
                return False

        finally:
            transport.close()

    except asyncio.TimeoutError:
        print("\n✗ Timeout - device doesn't respond to unencrypted ping")
        print("\nConclusion:")
        print("  Device REQUIRES encryption even for ping commands")
        print("  (This contradicts the documentation on page 41)")
        return False

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


class MinimalProtocolHandler(asyncio.DatagramProtocol):
    """Minimal protocol handler for receiving UDP responses."""

    def __init__(self):
        """Initialize protocol handler."""
        self._response_future = None

    def connection_made(self, transport):
        """Called when connection is established."""
        self._transport = transport
        print("UDP connection established")

    def datagram_received(self, data, addr):
        """Called when datagram is received."""
        print(f"Received datagram from {addr} ({len(data)} bytes)")

        if self._response_future and not self._response_future.done():
            self._response_future.set_result(data)

    def error_received(self, exc):
        """Called when error occurs."""
        print(f"Protocol error: {exc}")

        if self._response_future and not self._response_future.done():
            self._response_future.set_exception(exc)

    async def wait_for_response(self):
        """Wait for response data."""
        loop = asyncio.get_running_loop()
        self._response_future = loop.create_future()
        return await self._response_future


if __name__ == "__main__":
    success = asyncio.run(test_ping_specific_target())
    sys.exit(0 if success else 1)
