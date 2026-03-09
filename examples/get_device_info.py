"""Example: Get device diagnostics and system information."""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100") as client:
        # Health check
        alive = await client.alive()
        print(f"Device alive: {alive.alive}")
        print(f"Firmware:     {alive.version}")
        print()

        # System info
        info = await client.system_info()
        print("Uptime:")
        for entry in info.uptime:
            print(f"  {entry.name}: {entry.value} {entry.unit}")
        print()
        print("WiFi:")
        for entry in info.wifi:
            print(f"  {entry.name}: {entry.value} {entry.unit}")
        print()

        # LED status
        led = await client.led()
        print(f"LED: {led.color} ({led.mode}), status: {led.status}")
        print()

        # Settings
        settings = await client.settings()
        print(f"Device name: {settings.device_name}")
        print(f"WiFi SSID:   {settings.wifi_primary.ssid}")
        print(f"MQTT:        {'enabled' if settings.mqtt.enable else 'disabled'}")
        print(f"Timezone:    {settings.timezone}")


if __name__ == "__main__":
    asyncio.run(main())
