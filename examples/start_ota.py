"""Example: Check for and start a firmware update (requires WRITE token)."""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100", token="your-write-token") as client:
        # Check for updates
        ota = await client.ota_check()
        if not ota.data.update_available:
            print("No update available.")
            print(f"Last checked: {ota.data.last_checked}")
            return

        print(f"Update available: v{ota.data.version} ({ota.data.tag})")
        print(f"Release date:    {ota.data.release_date}")
        print(f"Release notes:   {ota.data.release_note_en}")
        print()

        confirm = input("Start update? (y/N): ")
        if confirm.lower() == "y":
            await client.ota_start()
            print("OTA update started. Device will reboot when done.")
        else:
            print("Update cancelled.")


if __name__ == "__main__":
    asyncio.run(main())
