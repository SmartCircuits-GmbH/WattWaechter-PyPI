"""Example: Scan for available WiFi networks."""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100") as client:
        # Start a fresh scan
        result = await client.wifi_scan(refresh=True)

        if result.scanning:
            print("Scan in progress, waiting...")
            await asyncio.sleep(1)
            result = await client.wifi_scan()

        print(f"Found {result.count} networks:\n")
        for network in result.networks:
            # Signal strength indicator
            if network.rssi > -50:
                strength = "████"
            elif network.rssi > -60:
                strength = "███░"
            elif network.rssi > -70:
                strength = "██░░"
            else:
                strength = "█░░░"

            print(f"  {strength}  {network.rssi:>4} dBm  {network.ssid}")


if __name__ == "__main__":
    asyncio.run(main())
