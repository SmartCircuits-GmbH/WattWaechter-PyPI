"""Example: List supported timezones."""

import asyncio
import sys

from aio_wattwaechter import Wattwaechter

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
TOKEN = sys.argv[2] if len(sys.argv) > 2 else None


async def main() -> None:
    async with Wattwaechter(HOST, token=TOKEN) as client:
        timezones = await client.timezones()
        print(f"Supported timezones ({len(timezones)}):\n")
        for tz in timezones:
            hours, minutes = divmod(abs(tz.utc_offset_min), 60)
            sign = "-" if tz.utc_offset_min < 0 else "+"
            print(f"  {tz.name:<30} UTC{sign}{hours:02d}:{minutes:02d}")


asyncio.run(main())
