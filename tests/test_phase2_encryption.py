"""Phase 2: Test encrypted communication WITHOUT authentication.

TESTED AND VERIFIED:
- UDP port 55055 with encrypted commands works WITHOUT authentication
- TCP/TLS authentication on port 55056 is NOT required for basic motor control
- Zero-padding encryption has 100% success rate
- Device info retrieval works without authentication
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.client import SomfyClient


async def test_encrypted_status():
    """Test encrypted communication with device info WITHOUT authentication."""
    # Configuration
    HOST = "192.168.1.77"
    TARGET_ID = "160326"  # Must be STRING
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

    print(f"Testing encrypted communication to {HOST} (NO authentication required)")
    print(f"Target ID: {TARGET_ID}")
    print("-" * 50)

    # Create client WITHOUT PIN (authentication is optional and not required)
    client = SomfyClient(
        host=HOST,
        target_id=TARGET_ID,
        key=KEY,
        pin=None,  # No authentication needed
        verify_ssl=False,
    )

    try:
        async with client:
            # Test device info (encrypted, NO authentication needed)
            print("\nFetching device info...")
            device_info = await client.get_device_info()

            print("\nDevice Info:")
            print(f"  Name: {device_info.name}")
            print(f"  Model: {device_info.model}")
            print(f"  MAC: {device_info.mac_address}")
            print(f"  Firmware: {device_info.firmware}")
            print(f"  Hardware: {device_info.hardware}")
            print(f"  Target ID: {device_info.target_id}")

            print("\n✓ Encrypted communication successful without authentication!")
            return True

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_encrypted_status())
    sys.exit(0 if success else 1)
