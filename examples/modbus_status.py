"""Example: Read Modbus TCP server status and register map.

Requires Modbus TCP to be enabled via the settings API. When enabled, the
device exposes a SunSpec-compliant Modbus TCP server (port 502 by default).

The /modbus/status endpoint is informational — it returns whether the
server is running, how many clients are connected, and the current register
map with OBIS mapping and live values.
"""

import asyncio

from aio_wattwaechter import Wattwaechter


async def main() -> None:
    # Pass token="your-read-token" if authentication is enabled
    async with Wattwaechter("192.168.1.100") as client:
        status = await client.modbus_status()

        if not status.enabled:
            print("Modbus TCP is disabled — enable it via /settings first.")
            return

        print(f"Modbus TCP server running: {status.running}")
        print(f"Port: {status.port}")
        print(f"Active client connections: {status.active_connections}")
        print()

        print(f"{'Register':<10}{'Name':<12}{'OBIS':<12}{'Value':<16}{'Unit':<6}Valid")
        print("-" * 64)
        for r in status.registers:
            value = f"{r.value:.3f}" if r.value is not None else "—"
            print(
                f"{r.register:<10}{r.name:<12}{r.obis:<12}"
                f"{value:<16}{r.unit:<6}{r.valid}"
            )

        invalid = [r for r in status.registers if not r.valid]
        if invalid:
            print()
            print(f"{len(invalid)} register(s) not delivered by the meter:")
            for r in invalid:
                print(f"  - {r.name} (OBIS {r.obis})")


if __name__ == "__main__":
    asyncio.run(main())
