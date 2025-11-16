"""Phase 1: Test unencrypted ping communication."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.protocol import SomfyProtocol
from custom_components.somfy_poe.api.transport import SomfyTransport


async def test_ping():
    """Test basic UDP communication with unencrypted ping."""
    # Configuration
    HOST = "10.1.1.10"
    TARGET_ID = "160326"

    print(f"Testing ping to {HOST} with target ID {TARGET_ID}")
    print("-" * 50)

    # Create transport without encryption (None)
    transport = SomfyTransport(HOST, encryption=None)
    protocol = SomfyProtocol(TARGET_ID)

    try:
        async with transport:
            # Build ping request
            request = protocol.build_request("status.ping")
            print(f"Sending: {request}")

            # Send unencrypted
            response = await transport.send_unencrypted(request)
            print(f"Received: {response}")

            # Parse response
            result = protocol.parse_response(response)
            print(f"Parsed result: {result}")

            if result.get("result") is True:
                print("\n✓ Ping successful!")
                return True
            else:
                print(f"\n✗ Unexpected result: {result}")
                return False

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_ping())
    sys.exit(0 if success else 1)
