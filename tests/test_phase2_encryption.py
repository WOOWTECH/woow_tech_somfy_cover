"""Phase 2: Test AES encryption/decryption."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.client import SomfyClient


async def test_encrypted_status():
    """Test encrypted communication with device info."""
    # Configuration
    HOST = "10.1.1.10"
    TARGET_ID = "160326"
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

    print(f"Testing encrypted communication to {HOST}")
    print(f"Target ID: {TARGET_ID}")
    print(f"Key: {KEY}")
    print("-" * 50)

    client = SomfyClient(
        host=HOST,
        target_id=TARGET_ID,
        key=KEY,
    )

    try:
        async with client:
            # Test device info (encrypted)
            print("Fetching device info...")
            device_info = await client.get_device_info()

            print("\nDevice Info:")
            print(f"  Name: {device_info.name}")
            print(f"  Model: {device_info.model}")
            print(f"  MAC: {device_info.mac_address}")
            print(f"  Firmware: {device_info.firmware}")
            print(f"  Hardware: {device_info.hardware}")
            print(f"  Target ID: {device_info.target_id}")

            print("\n✓ Encrypted communication successful!")
            return True

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_encrypted_status())
    sys.exit(0 if success else 1)
