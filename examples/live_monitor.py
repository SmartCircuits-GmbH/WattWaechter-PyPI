"""Example: Live power monitoring with continuous updates."""

import asyncio
import sys

from aio_wattwaechter import Wattwaechter, WattwaechterConnectionError


async def main() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    token = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Connecting to WattWächter at {host}...")

    async with Wattwaechter(host, token=token) as client:
        alive = await client.alive()
        print(f"Connected! Firmware: {alive.version}")
        print("Press Ctrl+C to stop.\n")

        while True:
            try:
                data = await client.meter_data()
                if data is None:
                    print("Waiting for meter data...", end="\r")
                else:
                    power = data.power or 0
                    bar_len = min(abs(int(power)) // 50, 40)
                    if power >= 0:
                        bar = "▸" * bar_len
                        print(f"  ← {power:>7.0f} W  [{bar:<40}]  consuming", end="\r")
                    else:
                        bar = "◂" * bar_len
                        print(f"  → {power:>7.0f} W  [{bar:>40}]  feeding in", end="\r")
            except WattwaechterConnectionError:
                print("  ⚠ Connection lost, retrying...          ", end="\r")

            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
