"""Example: Update device settings (requires WRITE token)."""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100", token="your-write-token") as client:
        # Toggle LED
        applied = await client.update_settings({"ledEnable": False})
        print(f"Applied: {applied}")

        # Change device name
        applied = await client.update_settings({"device_name": "Keller-Zähler"})
        print(f"Applied: {applied}")

        # Configure MQTT
        applied = await client.update_settings({
            "mqtt": {
                "enable": True,
                "host": "mqtt.local",
                "port": 1883,
                "use_tls": False,
                "user": "wattwaechter",
                "password": "secret",
                "sendInterval": 15,
                "client_id": "ww-keller",
                "topic_prefix": "energy/keller",
            }
        })
        print(f"MQTT configured: {applied}")

        # Verify settings
        settings = await client.settings()
        print(f"LED: {'on' if settings.led_enable else 'off'}")
        print(f"Name: {settings.device_name}")
        print(f"MQTT: {settings.mqtt.host}:{settings.mqtt.port}")


if __name__ == "__main__":
    asyncio.run(main())
