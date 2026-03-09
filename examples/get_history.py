"""Example: Retrieve energy history data."""

import asyncio
from datetime import date, timedelta

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100", token="your-read-token") as client:
        # High-resolution data (15-min intervals) for today
        today = date.today().isoformat()
        print(f"High-res data for {today}:")
        high_res = await client.history_high_res(today)
        for item in high_res.items[:5]:  # Show first 5 entries
            print(f"  {item.date}: {item.pwr}W, import +{item.di}kWh, export +{item.de}kWh")
        print(f"  ... ({len(high_res.items)} entries total)")
        print(f"  Summary: import={high_res.summary.total_import}kWh, export={high_res.summary.total_export}kWh")
        print()

        # Low-resolution data (daily) for the last 7 days
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        print(f"Daily data from {week_ago} (7 days):")
        low_res = await client.history_low_res(week_ago, 7)
        for item in low_res.items:
            print(f"  {item.date}: import +{item.di}kWh, export +{item.de}kWh")
        print(f"  Summary: import={low_res.summary.total_import}kWh, export={low_res.summary.total_export}kWh")


if __name__ == "__main__":
    asyncio.run(main())
