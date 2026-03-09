"""Tests for the Wattwaechter client."""

from __future__ import annotations

import pytest
import aiohttp
from aioresponses import aioresponses

from aio_wattwaechter import (
    Wattwaechter,
    WattwaechterAuthenticationError,
    WattwaechterConnectionError,
    WattwaechterRateLimitError,
)
from aio_wattwaechter.models import (
    LedColor,
    LedMode,
    LedStatus,
)

from .conftest import BASE_URL


# --- System endpoints ---


async def test_alive(mock_api: aioresponses) -> None:
    """Test alive endpoint."""
    mock_api.get(
        f"{BASE_URL}/system/alive",
        payload={"alive": True, "version": "1.0.3"},
    )
    async with Wattwaechter("192.168.1.100") as client:
        result = await client.alive()
    assert result.alive is True
    assert result.version == "1.0.3"


async def test_system_info(mock_api: aioresponses) -> None:
    """Test system info endpoint."""
    mock_api.get(
        f"{BASE_URL}/system/info",
        payload={
            "uptime": [{"name": "Uptime", "value": "5h 30m", "unit": ""}],
            "wifi": [{"name": "RSSI", "value": "-45", "unit": "dBm"}],
            "ap": [],
            "esp": [{"name": "Chip", "value": "ESP32-S3", "unit": ""}],
            "heap": [{"name": "Free", "value": "150000", "unit": "bytes"}],
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.system_info()
    assert len(result.uptime) == 1
    assert result.uptime[0].name == "Uptime"
    assert result.get_value("wifi", "RSSI") == "-45"
    assert result.get_value("wifi", "nonexistent") is None


async def test_led(mock_api: aioresponses) -> None:
    """Test LED endpoint."""
    mock_api.get(
        f"{BASE_URL}/system/led",
        payload={
            "status": "OK",
            "priority": 1,
            "color": "green",
            "mode": "dimmed",
            "rgb": {"r": 0, "g": 255, "b": 0},
            "enabled": True,
            "active_statuses": {"ok": True, "error": False},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.led()
    assert result.status == LedStatus.OK
    assert result.color == LedColor.GREEN
    assert result.mode == LedMode.DIMMED
    assert result.rgb.g == 255
    assert result.enabled is True


async def test_selftest(mock_api: aioresponses) -> None:
    """Test self-test endpoint."""
    mock_api.post(
        f"{BASE_URL}/system/selftest",
        payload={"success": True, "result": "SUCCESS", "message": "IR-Transceiver OK"},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.selftest()
    assert result.success is True
    assert result.result == "SUCCESS"


async def test_wifi_scan(mock_api: aioresponses) -> None:
    """Test WiFi scan endpoint."""
    mock_api.get(
        f"{BASE_URL}/system/wifi_scan",
        payload={
            "networks": [
                {"ssid": "MyNetwork", "rssi": -45},
                {"ssid": "Other", "rssi": -67},
            ],
            "count": 2,
        },
    )
    async with Wattwaechter("192.168.1.100") as client:
        result = await client.wifi_scan()
    assert result.count == 2
    assert result.networks[0].ssid == "MyNetwork"
    assert result.networks[0].rssi == -45


async def test_wifi_scan_in_progress(mock_api: aioresponses) -> None:
    """Test WiFi scan when scan is still in progress."""
    mock_api.get(
        f"{BASE_URL}/system/wifi_scan?refresh=true",
        payload={"networks": [], "count": 0, "scanning": True},
    )
    async with Wattwaechter("192.168.1.100") as client:
        result = await client.wifi_scan(refresh=True)
    assert result.scanning is True
    assert result.count == 0


async def test_timezones(mock_api: aioresponses) -> None:
    """Test timezones endpoint."""
    mock_api.get(
        f"{BASE_URL}/system/timezones",
        payload={"Europe/Berlin": "CET-1CEST,M3.5.0,M10.5.0/3"},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.timezones()
    assert "Europe/Berlin" in result


async def test_reboot(mock_api: aioresponses) -> None:
    """Test reboot endpoint."""
    mock_api.post(
        f"{BASE_URL}/system/reboot",
        payload={"rebooting": True},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.reboot()
    assert result is True


# --- History / Meter endpoints ---


async def test_meter_data(mock_api: aioresponses) -> None:
    """Test meter data endpoint."""
    mock_api.get(
        f"{BASE_URL}/history/latest",
        payload={
            "timestamp": 1709913600,
            "datetime": "2024-03-08T16:00:00+01:00",
            "1-0:1.8.0": {"value": 12345.678, "unit": "kWh"},
            "1-0:2.8.0": {"value": 4567.89, "unit": "kWh"},
            "1-0:16.7.0": {"value": 1234, "unit": "W"},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.meter_data()
    assert result is not None
    assert result.timestamp == 1709913600
    assert result.power == 1234
    assert result.total_consumption == 12345.678
    assert result.total_feed_in == 4567.89
    assert result.get("1-0:1.8.0") is not None
    assert result.get("1-0:1.8.0").value == 12345.678  # type: ignore[union-attr]
    assert result.get("nonexistent") is None


async def test_meter_data_no_data(mock_api: aioresponses) -> None:
    """Test meter data returns None on 204."""
    mock_api.get(f"{BASE_URL}/history/latest", status=204)
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.meter_data()
    assert result is None


async def test_history_high_res(mock_api: aioresponses) -> None:
    """Test high-resolution history endpoint."""
    mock_api.get(
        f"{BASE_URL}/history/highRes?date=2024-03-08",
        payload={
            "start": "2024-03-08",
            "days": 1,
            "items": [
                {
                    "date": "2024-03-08T00:00:00",
                    "timestamp": 1709856000,
                    "imp": 12345.0,
                    "exp": 4567.0,
                    "pwr": 1234,
                    "di": 0.25,
                    "de": 0.0,
                }
            ],
            "summary": {"total_import": 5.6, "total_export": 1.2},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.history_high_res("2024-03-08")
    assert result.start == "2024-03-08"
    assert len(result.items) == 1
    assert result.items[0].pwr == 1234
    assert result.summary.total_import == 5.6


async def test_history_low_res(mock_api: aioresponses) -> None:
    """Test low-resolution history endpoint."""
    mock_api.get(
        f"{BASE_URL}/history/lowRes?start=2024-03-01&days=2",
        payload={
            "start": "2024-03-01",
            "days": 2,
            "items": [
                {"date": "2024-03-01", "imp": 12340.0, "exp": 4560.0, "di": 8.5, "de": 2.1},
                {"date": "2024-03-02", "imp": 12348.5, "exp": 4562.1, "di": 7.0, "de": 1.5},
            ],
            "summary": {"total_import": 15.5, "total_export": 3.6},
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.history_low_res("2024-03-01", 2)
    assert result.days == 2
    assert len(result.items) == 2
    assert result.summary.total_export == 3.6


# --- OTA endpoints ---


async def test_ota_check(mock_api: aioresponses) -> None:
    """Test OTA check endpoint."""
    mock_api.get(
        f"{BASE_URL}/ota/check",
        payload={
            "ok": True,
            "data": {
                "update_available": True,
                "version": "1.2.0",
                "tag": "stable",
                "release_date": "2025-03-01",
                "release_note_de": "Fehlerbehebungen",
                "release_note_en": "Bug fixes",
                "last_checked": 1709913600,
            },
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.ota_check()
    assert result.ok is True
    assert result.data.update_available is True
    assert result.data.version == "1.2.0"


async def test_ota_start(mock_api: aioresponses) -> None:
    """Test OTA start endpoint."""
    mock_api.post(
        f"{BASE_URL}/ota/start",
        payload={"ok": True, "msg": "OTA started"},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.ota_start()
    assert result is True


# --- Settings endpoints ---


async def test_settings(mock_api: aioresponses) -> None:
    """Test settings endpoint."""
    mock_api.get(
        f"{BASE_URL}/settings",
        payload={
            "wifi": {
                "primary": {
                    "enable": True,
                    "ssid": "MyNetwork",
                    "static_ip": False,
                    "ip": "",
                    "subnet": "",
                    "gateway": "",
                    "dns": "",
                },
                "secondary": {
                    "enable": False,
                    "ssid": "",
                    "static_ip": False,
                    "ip": "",
                    "subnet": "",
                    "gateway": "",
                    "dns": "",
                },
            },
            "accessPoint": {
                "enable": True,
                "password_enable": False,
                "ssid": "WattWaechter-1234",
            },
            "mqtt": {
                "enable": False,
                "host": "",
                "port": 1883,
                "use_tls": False,
                "user": "",
                "sendInterval": 10,
                "client_id": "",
                "topic_prefix": "wattwaechter",
            },
            "language": {
                "active": "de",
                "installed": [
                    {"code": "de", "name": "Deutsch"},
                    {"code": "en", "name": "English"},
                ],
            },
            "timezone": "Europe/Berlin",
            "ntp_server": "pool.ntp.org",
            "rebootCounter": 0,
            "rebootsTotal": 5,
            "rebootsAll": 10,
            "ledEnable": True,
            "api_auth_required": True,
            "device_name": "WattWaechter",
            "awsIotEnabled": False,
        },
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.settings()
    assert result.wifi_primary.ssid == "MyNetwork"
    assert result.wifi_primary.enable is True
    assert result.wifi_secondary.enable is False
    assert result.access_point.ssid == "WattWaechter-1234"
    assert result.mqtt.port == 1883
    assert result.language.active == "de"
    assert len(result.language.installed) == 2
    assert result.timezone == "Europe/Berlin"
    assert result.device_name == "WattWaechter"
    assert result.led_enable is True


async def test_update_settings(mock_api: aioresponses) -> None:
    """Test update settings endpoint."""
    mock_api.post(
        f"{BASE_URL}/settings",
        payload={"success": True, "applied": {"ledEnable": False}},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.update_settings({"ledEnable": False})
    assert result == {"ledEnable": False}


# --- Auth endpoints ---


async def test_generate_tokens(mock_api: aioresponses) -> None:
    """Test token generation endpoint."""
    mock_api.post(
        f"{BASE_URL}/auth/tokens/generate",
        payload={
            "success": True,
            "pending": {
                "token_read": "A1B2C3D4E5F6G7H8",
                "token_write": "X9Y8Z7W6V5U4T3S2",
            },
            "expires_in": 60,
        },
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.generate_tokens()
    assert result.success is True
    assert result.token_read == "A1B2C3D4E5F6G7H8"
    assert result.token_write == "X9Y8Z7W6V5U4T3S2"
    assert result.expires_in == 60


async def test_confirm_tokens(mock_api: aioresponses) -> None:
    """Test token confirmation endpoint."""
    mock_api.post(
        f"{BASE_URL}/auth/tokens/confirm",
        payload={"success": True, "message": "Tokens activated successfully."},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.confirm_tokens("X9Y8Z7W6V5U4T3S2")
    assert result is True


# --- MQTT CA endpoints ---


async def test_mqtt_ca_status(mock_api: aioresponses) -> None:
    """Test MQTT CA status endpoint."""
    mock_api.get(
        f"{BASE_URL}/mqtt/ca",
        payload={"has_custom_cert": False, "bundle_size": 5750, "custom_size": 0},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        result = await client.mqtt_ca_status()
    assert result.has_custom_cert is False
    assert result.bundle_size == 5750


async def test_mqtt_ca_upload(mock_api: aioresponses) -> None:
    """Test MQTT CA upload endpoint."""
    mock_api.post(
        f"{BASE_URL}/mqtt/ca",
        payload={"success": True, "message": "Certificate added", "bundle_size": 7500},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.mqtt_ca_upload("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")
    assert result is True


async def test_mqtt_ca_delete(mock_api: aioresponses) -> None:
    """Test MQTT CA delete endpoint."""
    mock_api.delete(
        f"{BASE_URL}/mqtt/ca",
        payload={"success": True, "message": "Custom certificate deleted", "bundle_size": 5750},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.mqtt_ca_delete()
    assert result is True


# --- Cloud pairing endpoints ---


async def test_cloud_pair(mock_api: aioresponses) -> None:
    """Test cloud pairing endpoint."""
    mock_api.post(
        f"{BASE_URL}/cloud/pair",
        payload={"success": True, "message": "Pairing wird durchgeführt..."},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.cloud_pair("WW-ABCD2345")
    assert result is True


async def test_cloud_unpair(mock_api: aioresponses) -> None:
    """Test cloud unpairing endpoint."""
    mock_api.delete(
        f"{BASE_URL}/cloud/pair",
        payload={"success": True, "message": "Pairing token removed."},
    )
    async with Wattwaechter("192.168.1.100", token="write") as client:
        result = await client.cloud_unpair()
    assert result is True


# --- Error handling ---


async def test_auth_error(mock_api: aioresponses) -> None:
    """Test 401 raises WattwaechterAuthenticationError."""
    mock_api.get(f"{BASE_URL}/system/info", status=401)
    async with Wattwaechter("192.168.1.100", token="bad") as client:
        with pytest.raises(WattwaechterAuthenticationError):
            await client.system_info()


async def test_forbidden_error(mock_api: aioresponses) -> None:
    """Test 403 raises WattwaechterAuthenticationError."""
    mock_api.post(f"{BASE_URL}/system/reboot", status=403)
    async with Wattwaechter("192.168.1.100", token="read") as client:
        with pytest.raises(WattwaechterAuthenticationError):
            await client.reboot()


async def test_rate_limit_error(mock_api: aioresponses) -> None:
    """Test 429 raises WattwaechterRateLimitError."""
    mock_api.get(
        f"{BASE_URL}/system/info",
        status=429,
        headers={"Retry-After": "5"},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        with pytest.raises(WattwaechterRateLimitError) as exc_info:
            await client.system_info()
    assert exc_info.value.retry_after == 5


async def test_connection_error(mock_api: aioresponses) -> None:
    """Test connection error raises WattwaechterConnectionError."""
    mock_api.get(
        f"{BASE_URL}/system/alive",
        exception=aiohttp.ClientError("Connection refused"),
    )
    async with Wattwaechter("192.168.1.100") as client:
        with pytest.raises(WattwaechterConnectionError):
            await client.alive()


async def test_unexpected_status(mock_api: aioresponses) -> None:
    """Test unexpected status raises WattwaechterConnectionError."""
    mock_api.get(f"{BASE_URL}/system/info", status=500)
    async with Wattwaechter("192.168.1.100", token="test") as client:
        with pytest.raises(WattwaechterConnectionError, match="Unexpected status 500"):
            await client.system_info()


async def test_service_unavailable(mock_api: aioresponses) -> None:
    """Test 503 raises WattwaechterConnectionError."""
    mock_api.get(
        f"{BASE_URL}/system/info",
        status=503,
        headers={"Retry-After": "1"},
    )
    async with Wattwaechter("192.168.1.100", token="test") as client:
        with pytest.raises(WattwaechterConnectionError, match="Device busy"):
            await client.system_info()


# --- Context manager / session ---


async def test_external_session(mock_api: aioresponses) -> None:
    """Test using an external session."""
    import aiohttp

    mock_api.get(
        f"{BASE_URL}/system/alive",
        payload={"alive": True, "version": "1.0.0"},
    )
    async with aiohttp.ClientSession() as session:
        client = Wattwaechter("192.168.1.100", session=session)
        result = await client.alive()
        assert result.alive is True
        # Session should NOT be closed by the client
        await client.close()
        assert not session.closed


async def test_host_property() -> None:
    """Test host property."""
    client = Wattwaechter("192.168.1.100")
    assert client.host == "192.168.1.100"
    await client.close()
