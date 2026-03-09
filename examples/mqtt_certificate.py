"""Example: Manage custom MQTT CA certificates (requires WRITE token)."""

import asyncio
from pathlib import Path

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    async with Wattwaechter("192.168.1.100", token="your-write-token") as client:
        # Check current status
        status = await client.mqtt_ca_status()
        print(f"Custom certificate: {'yes' if status.has_custom_cert else 'no'}")
        print(f"Bundle size: {status.bundle_size} bytes")
        print(f"Custom size: {status.custom_size} bytes")
        print()

        if not status.has_custom_cert:
            # Upload a custom CA certificate
            cert_path = Path("my-mqtt-ca.pem")
            if cert_path.exists():
                cert = cert_path.read_text()
                success = await client.mqtt_ca_upload(cert)
                print(f"Upload: {'success' if success else 'failed'}")
            else:
                print(f"Certificate file not found: {cert_path}")
        else:
            # Optionally delete the custom certificate
            confirm = input("Delete custom certificate? (y/N): ")
            if confirm.lower() == "y":
                success = await client.mqtt_ca_delete()
                print(f"Delete: {'success' if success else 'failed'}")


if __name__ == "__main__":
    asyncio.run(main())
