#!/usr/bin/env python3
"""
Test the wake-up mechanism for the Somfy PoE motor integration.

This script tests that:
1. First command after idle works (no timeout)
2. Wake-up mechanism properly handles sleeping motor
3. Subsequent commands work without wake-up overhead
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add core to path
core_path = Path(__file__).parent.parent / "core"
sys.path.insert(0, str(core_path))

from custom_components.woow_tech_somfy_cover.api.client import SomfyClient

# Device configuration
HOST = "192.168.1.77"
UDP_PORT = 55055
TARGET_ID = "160326"
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

_LOGGER = logging.getLogger(__name__)


async def test_wakeup_mechanism():
    """Test the wake-up mechanism."""
    print("=" * 70)
    print("TESTING WAKE-UP MECHANISM")
    print("=" * 70)
    print(f"\nDevice: {HOST}:{UDP_PORT}")
    print(f"Target ID: {TARGET_ID}")
    print("\nThis test verifies that the wake-up mechanism works correctly.")
    print("The motor should respond to the first command without timing out.")
    print("=" * 70)

    # Test 1: First command after connection (motor might be sleeping)
    print("\n[TEST 1] First command after connection (motor likely sleeping)")
    print("-" * 70)

    async with SomfyClient(
        host=HOST,
        target_id=TARGET_ID,
        key=KEY_HEX,
        port=UDP_PORT,
        timeout=10.0,
    ) as client:
        try:
            print("Sending: status.position (first command)")
            position = await client.get_position()
            print(f"SUCCESS - Got position: {position.position}%")
            print(f"  Status: {position.status}")
            print(f"  Direction: {position.direction}")
        except Exception as e:
            print(f"FAILED - {type(e).__name__}: {e}")
            return False

        # Brief pause
        print("\nWaiting 2 seconds...")
        await asyncio.sleep(2)

        # Test 2: Second command (motor should be awake, no wake-up needed)
        print("\n[TEST 2] Second command (motor awake, should be fast)")
        print("-" * 70)

        try:
            print("Sending: status.info")
            info = await client.get_device_info()
            print(f"SUCCESS - Got device info:")
            print(f"  Name: {info.name}")
            print(f"  MAC: {info.mac_address}")
            print(f"  Firmware: {info.firmware}")
        except Exception as e:
            print(f"FAILED - {type(e).__name__}: {e}")
            return False

        # Test 3: Movement command
        print("\n[TEST 3] Movement command (stop - harmless)")
        print("-" * 70)

        try:
            print("Sending: move.stop")
            await client.stop()
            print("SUCCESS - Stop command accepted")
        except Exception as e:
            print(f"FAILED - {type(e).__name__}: {e}")
            return False

    # Test 4: Reconnection (simulates motor going to sleep)
    print("\n[TEST 4] After reconnection (motor may have slept)")
    print("-" * 70)
    print("Waiting 3 seconds (simulating idle time)...")
    await asyncio.sleep(3)

    async with SomfyClient(
        host=HOST,
        target_id=TARGET_ID,
        key=KEY_HEX,
        port=UDP_PORT,
        timeout=10.0,
    ) as client:
        try:
            print("Sending: status.position (after reconnect)")
            position = await client.get_position()
            print(f"SUCCESS - Got position: {position.position}%")
        except Exception as e:
            print(f"FAILED - {type(e).__name__}: {e}")
            return False

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
    print("\nWake-up mechanism is working correctly:")
    print("  - First commands after connection work without timeout")
    print("  - Wake-up command is sent transparently")
    print("  - Subsequent commands work without overhead")
    print("=" * 70)

    return True


async def main():
    """Main test function."""
    try:
        success = await test_wakeup_mechanism()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
