# aio-wattwaechter

Async Python client for the [WattWächter](https://wattwächter.de) smart meter API.

## Installation

```bash
pip install aio-wattwaechter
```

## Usage

```python
import asyncio
from aio_wattwaechter import Wattwaechter

async def main():
    # No token needed if authentication is disabled (factory default)
    async with Wattwaechter("192.168.1.100") as client:
        # Check device connectivity
        alive = await client.alive()
        print(f"Device online: {alive.alive}, firmware: {alive.version}")

        # Get current meter readings
        data = await client.meter_data()
        if data:
            print(f"Power: {data.power} W")
            print(f"Total consumption: {data.total_consumption} kWh")

            # Access any OBIS code (short format, e.g. "1.8.0")
            for code, value in data.values.items():
                print(f"  {value.name} ({code}): {value.value} {value.unit}")

        # Get system diagnostics
        info = await client.system_info()
        print(f"WiFi RSSI: {info.get_value('wifi', 'RSSI')} dBm")

        # Check for firmware updates
        ota = await client.ota_check()
        if ota.data.update_available:
            print(f"Update available: {ota.data.version}")

        # Get 15-minute resolution history
        history = await client.history_high_res("2024-03-08")
        for entry in history.items:
            print(f"  {entry.date}: {entry.power_w} W")
        print(f"  Total import: {history.import_total_kwh} kWh")

        # Get device logs
        ram_log = await client.logs_ram()
        print(f"RAM log: {len(ram_log)} bytes")

asyncio.run(main())
```

## Gas and water (WattWächter Gas / Wasser)

Gas/water devices (model IDs `ww_gw_mf`, `ww_gw_id`) report full OBIS codes
(`7-0:3.0.0` gas volume in m³, `7-0:43.0.0` gas flow in m³/h, `8-0:1.0.0`
water volume, `8-0:2.0.0` water flow). The medium can be switched on the device
at runtime, which also switches the OBIS codes.

```python
info = await client.system_info()
print(info.product_name, info.model_id)  # "WattWächter Gas", "ww_gw_mf"

data = await client.meter_data()
if data and data.is_volume_meter:
    print(f"{data.medium}: {data.volume} m³, {data.flow} m³/h")
    print(f"Sensor ok: {data.gw.ok if data.gw else None}")

history = await client.history_low_res("2024-03-01", 7)
print(history.unit)  # "m³" on gas/water, "kWh" on electricity
for day in history.items:
    print(day.date, day.import_total, day.consumption)
print(history.consumption)
```

## Authentication

By default, the WattWächter device ships with authentication **disabled**. You can connect without a token:

```python
client = Wattwaechter("192.168.1.100")
```

When authentication is enabled on the device, it uses two tokens:
- **READ token** — for reading data (meter values, settings, diagnostics)
- **WRITE token** — for modifying settings, starting OTA updates, rebooting

```python
# Read-only access
client = Wattwaechter("192.168.1.100", token="your-read-token")

# Full access (read + write)
client = Wattwaechter("192.168.1.100", token="your-write-token")
```

## Automatic Retry

The client automatically retries requests when the device returns **429** (rate limit) or **503** (busy). By default, up to 3 attempts are made, respecting the `Retry-After` header:

```python
# Default: 3 retries
client = Wattwaechter("192.168.1.100")

# Customize retry behavior
client = Wattwaechter("192.168.1.100", max_retries=5)

# Disable retries
client = Wattwaechter("192.168.1.100", max_retries=1)
```

## API Coverage

| Category | Endpoints |
|---|---|
| System | `alive`, `system_info`, `led`, `selftest`, `wifi_scan`, `timezones`, `reboot` |
| Meter Data | `meter_data`, `history_high_res`, `history_low_res` |
| Logs | `logs_rawdump`, `logs_persistent`, `logs_ram` |
| OTA | `ota_check`, `ota_start` |
| Settings | `settings`, `update_settings` |
| Auth | `generate_tokens`, `confirm_tokens`, `setup_token` |
| MQTT | `mqtt_ca_status`, `mqtt_ca_upload`, `mqtt_ca_delete`, `mqtt_status` |
| Modbus TCP | `modbus_status` |
| Cloud | `cloud_pair`, `cloud_unpair` |

## Using with Home Assistant

This library is the foundation for the [WattWächter Home Assistant integration](https://github.com/SmartCircuits-GmbH/WattWaechter_HA_Integration). You can pass an existing `aiohttp.ClientSession`:

```python
from aio_wattwaechter import Wattwaechter

client = Wattwaechter(
    "192.168.1.100",
    token="your-token",
    session=existing_session,  # reuse HA's session
)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
