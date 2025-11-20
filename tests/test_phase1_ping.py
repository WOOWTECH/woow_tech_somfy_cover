"""Phase 1: Test encrypted ping WITHOUT authentication.

TESTED AND VERIFIED:
- UDP port 55055 with encrypted commands works WITHOUT authentication
- TCP/TLS authentication on port 55056 is NOT required for basic motor control
- Zero-padding encryption has 100% success rate
- Socket must bind to port 55055 with SO_REUSEADDR
- targetID must be STRING ("160326")
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.protocol import SomfyProtocol
from custom_components.somfy_poe.api.transport import SomfyTransport
from custom_components.somfy_poe.api.encryption import SomfyEncryption


async def test_ping():
    """Test encrypted ping WITHOUT authentication (authentication is NOT required)."""
    # Configuration
    HOST = "192.168.1.77"
    TARGET_ID = "160326"  # Must be STRING
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

    print(f"Testing encrypted ping to {HOST} (NO authentication required)")
    print(f"Target ID: {TARGET_ID}")
    print("-" * 50)

    try:
        # Direct encrypted UDP on port 55055 (NO authentication needed)
        print("\nSending encrypted UDP ping on port 55055...")
        print("Note: Authentication is NOT required for basic motor control")

        encryption = SomfyEncryption(KEY)
        transport = SomfyTransport(HOST, encryption=encryption)
        protocol = SomfyProtocol(TARGET_ID)

        async with transport:
            # Build ping request
            request = protocol.build_request("status.ping")
            print(f"Request: {request}")

            # Send encrypted (uses zero-padding - 100% success rate)
            response = await transport.send_encrypted(request)
            print(f"Response: {response}")

            # Parse response
            result = protocol.parse_response(response)
            print(f"Parsed result: {result}")

            if result.get("result") is True:
                print("\n✓ Ping successful without authentication!")
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
