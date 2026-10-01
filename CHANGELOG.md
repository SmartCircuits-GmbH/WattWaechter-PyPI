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

## 1.1.0

- `modbus_status()` and `mqtt_status()` endpoints.

## 1.0.0

- Initial release.
