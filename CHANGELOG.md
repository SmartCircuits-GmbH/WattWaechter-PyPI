# Changelog

## 1.2.0 (unreleased)

Gas and water support (WattWächter Gas / Wasser, model IDs `ww_gw_mf` and `ww_gw_id`).

- `MeterData`: new `medium` (`Medium.ELECTRICITY` / `GAS` / `WATER`), `is_volume_meter`,
  `volume` (m³), `flow` (m³/h), `volume_obis`, `flow_obis` and the parsed `gw` status
  block (`GwStatus`: `ok`, `medium`, `revolutions`, `coils`, `active_coils`,
  `energy_factor`, `raw`).
- New constants `OBIS_GAS_VOLUME` (`7-0:3.0.0`), `OBIS_GAS_FLOW` (`7-0:43.0.0`),
  `OBIS_WATER_VOLUME` (`8-0:1.0.0`), `OBIS_WATER_FLOW` (`8-0:2.0.0`), `VOLUME_OBIS`,
  `FLOW_OBIS`, `UNIT_KWH`, `UNIT_M3`.
- `history_high_res()` no longer raises `KeyError` on gas/water devices: the m³ keys
  (`import_total_m3`, `import_m3h`, `flow_m3h`, `consumption_m3`) are parsed into new
  optional fields. `history_low_res()` parses `import_total_m3`, `import_m3` and
  `consumption_m3` instead of silently returning zeros.
- `HighResHistory` / `LowResHistory`: new `unit` (`kWh` or `m³`), `is_volume`,
  `consumption_m3` and `consumption`; entries get unit-neutral `import_total`
  (and `consumption` on low-res entries). The electricity fields of history entries
  now default to 0.0.
- `SystemInfo`: new accessors `device_id`, `firmware_version`, `model_id`,
  `product_name`, `is_gas_water`.
- `alive()` tolerates unknown and missing keys (the firmware reports only `alive` and
  `version`).
- The client passes `mypy --strict`; boolean results are always returned as `bool`.
- Tested on Python 3.14 and aiohttp 3.14.

Fixes from an audit of the client against the firmware API:

- **Breaking:** `TimezoneEntry` now has `name` and `utc_offset_min` (minutes), which is
  what the firmware reports. The previous fields `gmt_offset` and `daylight_offset`
  never existed in the API, so `timezones()` always raised `KeyError`.
- `LedStatus.METER_ATTENTION` added; `led()` raised `ValueError` when the device
  reported it.
- `history_low_res()` and `history_high_res()` return an empty history when the device
  has no data for the range (HTTP 204) instead of raising `KeyError`.
- `ota_start()` returns `False` when the device reports that no update is available;
  it returned `True` before. It also waits up to 30 seconds, because the device asks
  the update server before it answers.
- `OtaData.url` and `OtaData.md5` are deprecated. The firmware never reports them, so
  they are always empty. They will be removed in 2.0.
- `ModbusRegisterInfo`: new `raw`, `scale_factor`, `scale_register` and `derived`.
- `logs_ram()` and `logs_persistent()` no longer raise `UnicodeDecodeError` on a log
  line that was cut inside a multibyte character.
- `max_retries=0` is treated as a single attempt instead of raising `TypeError`.
- `AccessPointConfig`, `LanguageConfig` and `LanguageEntry` are exported.
- Documented: `selftest()` and `logs_rawdump()` are not available on gas/water devices,
  `ota_check()` returns the cached result of the device's own check, and
  `update_settings()` returns an echo of the request.

## 1.1.0

- `modbus_status()` and `mqtt_status()` endpoints.

## 1.0.0

- Initial release.
