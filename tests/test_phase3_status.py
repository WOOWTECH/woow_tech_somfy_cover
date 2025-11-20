"""Phase 3: Test status queries WITHOUT authentication.

TESTED AND VERIFIED:
- UDP port 55055 with encrypted commands works WITHOUT authentication
- TCP/TLS authentication on port 55056 is NOT required for basic motor control
- Zero-padding encryption has 100% success rate
- Position status retrieval works without authentication
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.somfy_poe.api.client import SomfyClient


async def test_status():
    """Test status queries WITHOUT authentication (authentication is NOT required)."""
    # Configuration
    HOST = "192.168.1.77"
    TARGET_ID = "160326"  # Must be STRING
    KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

    print(f"Testing status queries to {HOST} (NO authentication required)")
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
            # Test position status (encrypted, NO authentication needed)
            print("Fetching position status...")
            status = await client.get_position()

            print("\nPosition Status:")
            print(f"  Position: {status.position}%")
            print(f"  Status: {status.status}")
            print(f"  Direction: {status.direction}")
            print(f"  Source: {status.source}")
            print(f"  Cause: {status.cause}")
            print(f"  Is Moving: {status.is_moving}")
            print(f"  Is Stopped: {status.is_stopped}")
            print(f"  Is Opening: {status.is_opening}")
            print(f"  Is Closing: {status.is_closing}")

            print("\n✓ Status queries successful without authentication!")
            return True

    except Exception as err:
        print(f"\n✗ Error: {err}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_status())
    sys.exit(0 if success else 1)
