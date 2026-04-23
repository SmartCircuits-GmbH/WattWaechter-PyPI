"""Example: Check the MQTT broker connection status.

Useful for diagnosing MQTT connection issues — e.g. Home Assistant can't
see the device, or messages aren't being published. Shows the current
connection state and the last error reported by the MQTT client.
"""

import asyncio

from aio_wattwaechter import Wattwaechter
from aio_wattwaechter.models import MqttState


async def main() -> None:
    # Pass token="your-read-token" if authentication is enabled
    async with Wattwaechter("192.168.1.100") as client:
        status = await client.mqtt_status()

        if not status.enabled:
            print("MQTT is disabled in device settings.")
            return

        print(f"Broker: {status.host}:{status.port}")
        print(f"Client ID: {status.client_id}")
        print(f"TLS: {'yes' if status.use_tls else 'no'}")
        print(f"State: {status.state.value}")

        if status.state == MqttState.CONNECTED:
            print("MQTT is connected.")
        elif status.last_error != 0:
            print(f"Last error ({status.last_error}): {status.last_error_message}")
            print(f"Reconnect attempts: {status.reconnect_attempts}")
        else:
            print(f"Not connected — state is {status.state.value}")


if __name__ == "__main__":
    asyncio.run(main())
