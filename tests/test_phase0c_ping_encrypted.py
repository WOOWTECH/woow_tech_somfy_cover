"""Phase 0c: Test encrypted ping with specific targetID."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.protocol import SomfyProtocol
from custom_components.somfy_poe.api.transport import SomfyTransport
from custom_components.somfy_poe.api.encryption import SomfyEncryption


async def test_encrypted_ping():
    """Test encrypted ping to verify if device requires encryption for ping."""
    # Configuration
    HOST = "192.168.1.77"
    TARGET_ID = "160326"
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

    print(f"Testing ENCRYPTED ping to {HOST}")
    print(f"Target ID: {TARGET_ID}")
    print("-" * 50)

    # Create encryption and transport
    encryption = SomfyEncryption(KEY)
    transport = SomfyTransport(HOST, encryption=encryption)
    protocol = SomfyProtocol(TARGET_ID)

    try:
        async with transport:
            # Build ping request
            request = protocol.build_request("status.ping")
            print(f"Request: {request}")

            # Send ENCRYPTED ping
            print("Sending encrypted ping...")
            response = await transport.send_encrypted(request)
            print(f"Response: {response}")

            # Parse response
            result = protocol.parse_response(response)
            print(f"Parsed result: {result}")

            if result.get("result") is True:
                print("\n✓ ENCRYPTED ping successful!")
                print("\nConclusion:")
                print("  Device REQUIRES encryption even for ping")
                print("  Documentation is incorrect about 'ping doesn't need encryption'")
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
    success = asyncio.run(test_encrypted_ping())
    sys.exit(0 if success else 1)
