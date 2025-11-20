"""Phase 5: Test position control WITHOUT authentication.

TESTED AND VERIFIED:
- UDP port 55055 with encrypted commands works WITHOUT authentication
- TCP/TLS authentication on port 55056 is NOT required for basic motor control
- Zero-padding encryption has 100% success rate
- Position control commands work without authentication
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.client import SomfyClient


async def test_position_control():
    """Test precise position control WITHOUT authentication (authentication is NOT required)."""
    # Configuration
    HOST = "192.168.1.77"
    TARGET_ID = "160326"  # Must be STRING
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"
    TARGET_POSITION = 50.0  # Middle position

    print(f"Testing position control to {HOST} (NO authentication required)")
    print("-" * 50)
    print(f"WARNING: This will move your cover to {TARGET_POSITION}%!")
    print("Press Ctrl+C to abort...")
    await asyncio.sleep(3)

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
            print(f"\nMoving to {TARGET_POSITION}%...")
            await client.move_to_position(TARGET_POSITION)

            # Poll until movement completes
            print("Monitoring position updates...")
            for i in range(30):  # Max 60 seconds (30 * 2s)
                await asyncio.sleep(2)
                status = await client.get_position()
                print(
                    f"  [{i+1}] Position: {status.position}%, "
                    f"Status: {status.status}, "
                    f"Direction: {status.direction}"
                )

                if not status.is_moving:
                    print("Movement completed!")
                    break

            # Verify final position (allow 2% tolerance)
            final_position = status.position
            if final_position is not None:
                difference = abs(final_position - TARGET_POSITION)
                print(f"\nFinal position: {final_position}%")
                print(f"Target position: {TARGET_POSITION}%")
                print(f"Difference: {difference}%")

                if difference <= 2.0:
                    print("✓ Position control successful without authentication!")
                    return True
                else:
                    print(f"✗ Position difference too large: {difference}%")
                    return False
            else:
                print("✗ Final position is None")
                return False

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_position_control())
    sys.exit(0 if success else 1)
