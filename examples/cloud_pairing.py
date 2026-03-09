"""Example: Cloud pairing management (requires WRITE token)."""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100", token="your-write-token") as client:
        # Check current cloud status via settings
        settings = await client.settings()
        print(f"AWS IoT: {'enabled' if settings.aws_iot_enabled else 'disabled'}")
        print()

        # Pair with cloud
        pairing_token = input("Enter pairing token (e.g. WW-ABCD2345): ").strip()
        if pairing_token:
            success = await client.cloud_pair(pairing_token)
            print(f"Pairing: {'success' if success else 'failed'}")
        else:
            # Or unpair
            confirm = input("Unpair from cloud? (y/N): ")
            if confirm.lower() == "y":
                success = await client.cloud_unpair()
                print(f"Unpair: {'success' if success else 'failed'}")


if __name__ == "__main__":
    asyncio.run(main())
