"""Phase 4: Test movement commands."""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.client import SomfyClient


async def test_movement():
    """Test basic movement commands."""
    # Configuration
    HOST = "10.1.1.10"
    TARGET_ID = "160326"
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

    print(f"Testing movement commands to {HOST}")
    print("-" * 50)
    print("WARNING: This will move your cover!")
    print("Press Ctrl+C to abort...")
    await asyncio.sleep(3)

    client = SomfyClient(
        host=HOST,
        target_id=TARGET_ID,
        key=KEY,
    )

    try:
        async with client:
            # Initial status
            print("\n1. Initial status:")
            status = await client.get_position()
            print(f"   Position: {status.position}%, Status: {status.status}")

            # Test move up
            print("\n2. Sending move up command...")
            await client.move_up()
            await asyncio.sleep(2)

            status = await client.get_position()
            print(f"   Position: {status.position}%, Status: {status.status}")

            if status.status.value != "running":
                print("   Warning: Expected status to be 'running'")

            # Test stop
            print("\n3. Sending stop command...")
            await client.stop()
            await asyncio.sleep(1)

            status = await client.get_position()
            print(f"   Position: {status.position}%, Status: {status.status}")

            if status.status.value != "stopped":
                print("   Warning: Expected status to be 'stopped'")

            print("\n✓ Movement commands successful!")
            return True

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_movement())
    sys.exit(0 if success else 1)
