#!/usr/bin/env python3
"""Debug test that mimics exactly what HA integration does."""
import asyncio
import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from custom_components.woow_tech_somfy_cover.api.client import SomfyClient


async def test_connection():
    """Test connection exactly like HA config_flow does."""
    print("=" * 70)
    print("TESTING HA INTEGRATION CONNECTION (exact config_flow pattern)")
    print("=" * 70)

    config = {
        "host": "192.168.1.77",
        "target_id": "160326",
        "key": "FBE90399BA25B4B67DC1B23BE0D9C084",
    }

    print(f"\nConfiguration:")
    print(f"  Host: {config['host']}")
    print(f"  Target ID: {config['target_id']}")
    print(f"  Key: {config['key']}")
    print("\n" + "=" * 70)

    # Create client exactly like config_flow.py does (lines 91-95)
    client = SomfyClient(
        host=config["host"],
        target_id=config["target_id"],
        key=config["key"],
    )

    print("\n1. Client created")
    print(f"   Using transport: {client._transport}")
    print(f"   Using encryption: {client._encryption}")
    print(f"   Using protocol: {client._protocol}")

    try:
        # Connect
        print("\n2. Connecting...")
        await client.connect()
        print("   ✓ Connection successful!")

        # Test with get_device_info like config_flow does (line 99)
        print("\n3. Getting device info...")
        device_info = await client.get_device_info()

        print("   ✓ Device info retrieved successfully!")
        print(f"   Name: {device_info.name}")
        print(f"   Model: {device_info.model}")
        print(f"   Firmware: {device_info.firmware}")
        print(f"   MAC: {device_info.mac_address}")

        # Also test position
        print("\n4. Getting position...")
        position = await client.get_position()
        print(f"   ✓ Position: {position.position}%")
        print(f"   Status: {position.status.value}")

        print("\n" + "=" * 70)
        print("SUCCESS - All tests passed!")
        print("=" * 70)
        return True

    except Exception as err:
        print(f"\n✗ ERROR: {type(err).__name__}: {err}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()
        print("\n5. Client closed")


if __name__ == "__main__":
    try:
        success = asyncio.run(test_connection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
        sys.exit(1)
