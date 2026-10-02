"""Tests for gas/water (GW-MF / GW-ID) support."""

from __future__ import annotations

from aioresponses import aioresponses

from aio_wattwaechter import (
    OBIS_GAS_FLOW,
    OBIS_GAS_VOLUME,
    OBIS_WATER_FLOW,
    OBIS_WATER_VOLUME,
    UNIT_KWH,
    UNIT_M3,
    Medium,
    Wattwaechter,
)

from .conftest import BASE_URL

GW_STATUS = {
    "ok": True,
    "medium": "gas",
    "ticks": 1234,
    "revolutions": 308.5,
    "activeCoils": 3,
    "coils": 3,
    "referenceCoil": 0,
    "cycles": 308,
    "catchUp": 0,
    "dropped": 0,
    "refLost": 0,
    "hysteresis": 12.0,
    "energyFactor": 10.5,
    "field": 120,
}


# --- /system/alive ---


async def test_alive_extra_and_missing_keys(mock_api: aioresponses) -> None:
    """Test alive tolerates unknown keys and missing fields."""
    mock_api.get(
        f"{BASE_URL}/system/alive",
        payload={"alive": True, "version": "2.0.0", "model_id": "ww_gw_mf"},
    )
    mock_api.get(f"{BASE_URL}/system/alive", payload={"alive": True})
    async with Wattwaechter("192.168.1.100") as client:
        result = await client.alive()
        assert result.alive is True
        assert result.version == "2.0.0"

        result = await client.alive()
        assert result.alive is True
        assert result.version == ""


# --- /system/info ---


async def test_system_info_model_accessors(mock_api: aioresponses) -> None:
    """Test model_id / product_name accessors."""
    mock_api.get(
        f"{BASE_URL}/system/info",
        payload={
            "esp": [
                {"name": "esp_id", "value": "9BFEFF453AB4", "unit": ""},
                {"name": "product_name", "value": "WattWächter Gas", "unit": ""},
                {"name": "model_id", "value": "ww_gw_mf", "unit": ""},
                {"name": "os_version", "value": "2.0.0", "unit": ""},
            ],
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.system_info()
    assert result.device_id == "9BFEFF453AB4"
    assert result.product_name == "WattWächter Gas"
    assert result.model_id == "ww_gw_mf"
    assert result.firmware_version == "2.0.0"
    assert result.is_gas_water is True


async def test_system_info_legacy_without_model(mock_api: aioresponses) -> None:
    """Test older firmware without model_id / product_name."""
    mock_api.get(
        f"{BASE_URL}/system/info",
        payload={"esp": [{"name": "esp_id", "value": "ABC", "unit": ""}]},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.system_info()
    assert result.model_id is None
    assert result.product_name is None
    assert result.is_gas_water is False


# --- /history/latest ---


async def test_meter_data_gas(mock_api: aioresponses) -> None:
    """Test gas meter data with full OBIS keys and gw block."""
    mock_api.get(
        f"{BASE_URL}/history/latest",
        payload={
            "timestamp": 1709913600,
            "datetime": "2024-03-08T16:00:00",
            "gw": GW_STATUS,
            OBIS_GAS_VOLUME: {"value": 1234.567, "unit": "m³", "name": "Meter Reading"},
            OBIS_GAS_FLOW: {"value": 0.42, "unit": "m³/h", "name": "Flow Rate"},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.meter_data()
    assert result is not None
    assert set(result.values) == {OBIS_GAS_VOLUME, OBIS_GAS_FLOW}
    assert result.medium is Medium.GAS
    assert result.is_volume_meter is True
    assert result.volume_obis == OBIS_GAS_VOLUME
    assert result.flow_obis == OBIS_GAS_FLOW
    assert result.volume == 1234.567
    assert result.flow == 0.42
    assert result.power is None
    assert result.total_consumption is None
    assert result.gw is not None
    assert result.gw.ok is True
    assert result.gw.medium is Medium.GAS
    assert result.gw.revolutions == 308.5
    assert result.gw.coils == 3
    assert result.gw.active_coils == 3
    assert result.gw.energy_factor == 10.5
    assert result.gw.raw["field"] == 120


async def test_meter_data_water_without_gw_block(mock_api: aioresponses) -> None:
    """Test the medium is derived from the OBIS keys without a gw block."""
    mock_api.get(
        f"{BASE_URL}/history/latest",
        payload={
            "timestamp": 1709913600,
            "datetime": "2024-03-08T16:00:00",
            OBIS_WATER_VOLUME: {"value": 55.5, "unit": "m³", "name": "Meter Reading"},
            OBIS_WATER_FLOW: {"value": 0.0, "unit": "m³/h", "name": "Flow Rate"},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.meter_data()
    assert result is not None
    assert result.gw is None
    assert result.medium is Medium.WATER
    assert result.volume == 55.5
    assert result.flow == 0.0


async def test_meter_data_gw_block_wins(mock_api: aioresponses) -> None:
    """Test the gw medium is authoritative, unknown media are ignored."""
    mock_api.get(
        f"{BASE_URL}/history/latest",
        payload={
            "gw": {**GW_STATUS, "medium": "water"},
            OBIS_WATER_VOLUME: {"value": 1.0, "unit": "m³"},
        },
    )
    mock_api.get(
        f"{BASE_URL}/history/latest",
        payload={
            "gw": {"ok": False, "medium": "steam"},
            OBIS_GAS_VOLUME: {"value": 1.0, "unit": "m³"},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.meter_data()
        assert result is not None
        assert result.medium is Medium.WATER

        result = await client.meter_data()
        assert result is not None
        assert result.gw is not None
        assert result.gw.medium is None
        assert result.medium is Medium.GAS


async def test_meter_data_electricity_medium(mock_api: aioresponses) -> None:
    """Test electricity meters report no volume."""
    mock_api.get(
        f"{BASE_URL}/history/latest",
        payload={"1.8.0": {"value": 1.0, "unit": "kWh"}},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.meter_data()
    assert result is not None
    assert result.gw is None
    assert result.medium is Medium.ELECTRICITY
    assert result.is_volume_meter is False
    assert result.volume_obis is None
    assert result.volume is None
    assert result.flow is None


# --- /history/highRes and /history/lowRes ---


async def test_history_high_res_gw(mock_api: aioresponses) -> None:
    """Test high-resolution history of a gas/water device (m³ keys)."""
    mock_api.get(
        f"{BASE_URL}/history/highRes?date=2024-03-08",
        payload={
            "start": "2024-03-08",
            "days": 1,
            "items": [
                {
                    "date": "2024-03-08T00:00",
                    "timestamp": 1709856000,
                    "import_total_m3": 1234.5,
                    "import_m3h": 0.12,
                    "flow_m3h": 0.1,
                },
                {
                    "date": "2024-03-08T00:15",
                    "timestamp": 1709856900,
                    "import_total_m3": 1234.53,
                    "import_m3h": 0.12,
                    "flow_m3h": 0.0,
                },
            ],
            "consumption_m3": 0.03,
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.history_high_res("2024-03-08")
    assert result.unit == UNIT_M3
    assert result.is_volume is True
    assert result.consumption_m3 == 0.03
    assert result.consumption == 0.03
    assert len(result.items) == 2
    item = result.items[0]
    assert item.import_total_m3 == 1234.5
    assert item.import_total == 1234.5
    assert item.import_m3h == 0.12
    assert item.flow_m3h == 0.1
    assert item.import_total_kwh == 0.0
    assert item.power_w == 0.0


async def test_history_high_res_electricity_unit(mock_api: aioresponses) -> None:
    """Test electricity high-res history keeps kWh semantics."""
    mock_api.get(
        f"{BASE_URL}/history/highRes?date=2024-03-08",
        payload={
            "start": "2024-03-08",
            "days": 1,
            "items": [
                {
                    "date": "2024-03-08T00:00",
                    "timestamp": 1709856000,
                    "import_total_kWh": 100.0,
                    "export_total_kWh": 1.0,
                    "import_kW": 0.2,
                    "export_kW": 0.0,
                    "power_W": 200,
                }
            ],
            "import_total_kWh": 2.5,
            "export_total_kWh": 0.5,
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.history_high_res("2024-03-08")
    assert result.unit == UNIT_KWH
    assert result.is_volume is False
    assert result.consumption_m3 is None
    assert result.consumption == 2.5
    assert result.items[0].import_total == 100.0
    assert result.items[0].import_total_m3 is None


async def test_history_low_res_gw(mock_api: aioresponses) -> None:
    """Test low-resolution history of a gas/water device (m³ keys)."""
    mock_api.get(
        f"{BASE_URL}/history/lowRes?start=2024-03-01&days=2",
        payload={
            "start": "2024-03-01",
            "days": 2,
            "items": [
                {
                    "date": "2024-03-01",
                    "timestamp": 1709251200,
                    "import_total_m3": 1200.0,
                    "import_m3": 2.5,
                },
                {
                    "date": "2024-03-02",
                    "timestamp": 1709337600,
                    "import_total_m3": 1202.5,
                    "import_m3": 3.0,
                },
            ],
            "consumption_m3": 5.5,
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.history_low_res("2024-03-01", 2)
    assert result.unit == UNIT_M3
    assert result.is_volume is True
    assert result.consumption == 5.5
    assert result.import_total_kwh == 0.0
    assert [i.import_total for i in result.items] == [1200.0, 1202.5]
    assert [i.consumption for i in result.items] == [2.5, 3.0]
    assert result.items[0].import_kwh == 0.0


async def test_history_low_res_electricity_consumption(
    mock_api: aioresponses,
) -> None:
    """Test electricity low-res history helpers stay in kWh."""
    mock_api.get(
        f"{BASE_URL}/history/lowRes?start=2024-03-01&days=1",
        payload={
            "start": "2024-03-01",
            "items": [
                {
                    "date": "2024-03-01",
                    "timestamp": 1709251200,
                    "import_total_kWh": 12340.0,
                    "export_total_kWh": 4560.0,
                    "import_kWh": 8.5,
                    "export_kWh": 2.1,
                }
            ],
            "import_total_kWh": 8.5,
            "export_total_kWh": 2.1,
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.history_low_res("2024-03-01", 1)
    assert result.unit == UNIT_KWH
    assert result.consumption == 8.5
    assert result.items[0].import_total == 12340.0
    assert result.items[0].consumption == 8.5
