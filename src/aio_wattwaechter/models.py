"""Data models for the WattWächter API."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


# --- System models ---


@dataclass(frozen=True)
class AliveResponse:
    """Response from GET /system/alive."""

    alive: bool
    version: str


@dataclass(frozen=True)
class InfoEntry:
    """Single entry in a system info section."""

    name: str
    value: str
    unit: str


@dataclass(frozen=True)
class SystemInfo:
    """Response from GET /system/info."""

    uptime: list[InfoEntry]
    wifi: list[InfoEntry]
    ap: list[InfoEntry]
    esp: list[InfoEntry]
    heap: list[InfoEntry]

    def get_value(self, section: str, name: str) -> str | None:
        """Get a value by section and name."""
        entries: list[InfoEntry] = getattr(self, section, [])
        for entry in entries:
            if entry.name == name:
                return entry.value
        return None


class LedStatus(StrEnum):
    """LED status codes."""

    NONE = "NONE"
    OK = "OK"
    STARTUP = "STARTUP"
    INFO = "INFO"
    BLE_ACTIVE = "BLE_ACTIVE"
    BLE_CONNECTED = "BLE_CONNECTED"
    OTA_ACTIVE = "OTA_ACTIVE"
    ERROR = "ERROR"
    RESET_PENDING = "RESET_PENDING"


class LedColor(StrEnum):
    """LED colors."""

    OFF = "off"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    RED = "red"


class LedMode(StrEnum):
    """LED display modes."""

    SOLID = "solid"
    PULSE = "pulse"
    DIMMED = "dimmed"
    OFF = "off"


@dataclass(frozen=True)
class RgbColor:
    """RGB color value."""

    r: int
    g: int
    b: int


@dataclass(frozen=True)
class LedInfo:
    """Response from GET /system/led."""

    status: LedStatus
    priority: int
    color: LedColor
    mode: LedMode
    rgb: RgbColor
    enabled: bool
    active_statuses: dict[str, bool]


@dataclass(frozen=True)
class SelfTestResult:
    """Response from POST /system/selftest."""

    success: bool
    result: str
    message: str


@dataclass(frozen=True)
class WifiNetwork:
    """A discovered WiFi network."""

    ssid: str
    rssi: int


@dataclass(frozen=True)
class WifiScanResponse:
    """Response from GET /system/wifi_scan."""

    networks: list[WifiNetwork]
    count: int
    scanning: bool = False


# --- History / Meter models ---


@dataclass(frozen=True)
class ObisValue:
    """A single OBIS code value from the smart meter."""

    value: float
    unit: str


@dataclass(frozen=True)
class MeterData:
    """Response from GET /history/latest."""

    timestamp: int
    datetime_str: str
    values: dict[str, ObisValue]

    def get(self, obis_code: str) -> ObisValue | None:
        """Get a value by OBIS code (e.g. '1-0:1.8.0')."""
        return self.values.get(obis_code)

    @property
    def power(self) -> float | None:
        """Total active power in W (OBIS 1-0:16.7.0)."""
        val = self.get("1-0:16.7.0")
        return val.value if val else None

    @property
    def total_consumption(self) -> float | None:
        """Total consumption in kWh (OBIS 1-0:1.8.0)."""
        val = self.get("1-0:1.8.0")
        return val.value if val else None

    @property
    def total_feed_in(self) -> float | None:
        """Total feed-in in kWh (OBIS 1-0:2.8.0)."""
        val = self.get("1-0:2.8.0")
        return val.value if val else None


@dataclass(frozen=True)
class HighResEntry:
    """A single entry in high-resolution history data."""

    date: str
    timestamp: int
    imp: float
    exp: float
    pwr: float
    di: float
    de: float


@dataclass(frozen=True)
class HighResSummary:
    """Summary of high-resolution history data."""

    total_import: float
    total_export: float


@dataclass(frozen=True)
class HighResHistory:
    """Response from GET /history/highRes."""

    start: str
    days: int
    items: list[HighResEntry]
    summary: HighResSummary


@dataclass(frozen=True)
class LowResEntry:
    """A single entry in low-resolution history data."""

    date: str
    imp: float
    exp: float
    di: float
    de: float


@dataclass(frozen=True)
class LowResHistory:
    """Response from GET /history/lowRes."""

    start: str
    days: int
    items: list[LowResEntry]
    summary: HighResSummary


# --- OTA models ---


@dataclass(frozen=True)
class OtaData:
    """OTA update information."""

    update_available: bool
    version: str
    tag: str
    release_date: str
    release_note_de: str
    release_note_en: str
    last_checked: int


@dataclass(frozen=True)
class OtaCheckResponse:
    """Response from GET /ota/check."""

    ok: bool
    data: OtaData


# --- Settings models ---


@dataclass(frozen=True)
class WifiConfig:
    """WiFi network configuration."""

    enable: bool
    ssid: str
    static_ip: bool
    ip: str
    subnet: str
    gateway: str
    dns: str


@dataclass(frozen=True)
class AccessPointConfig:
    """Access point configuration."""

    enable: bool
    password_enable: bool
    ssid: str


@dataclass(frozen=True)
class MqttConfig:
    """MQTT configuration."""

    enable: bool
    host: str
    port: int
    use_tls: bool
    user: str
    sendInterval: int
    client_id: str
    topic_prefix: str


@dataclass(frozen=True)
class LanguageEntry:
    """An installed language."""

    code: str
    name: str


@dataclass(frozen=True)
class LanguageConfig:
    """Language configuration."""

    active: str
    installed: list[LanguageEntry]


@dataclass(frozen=True)
class Settings:
    """Response from GET /settings."""

    wifi_primary: WifiConfig
    wifi_secondary: WifiConfig
    access_point: AccessPointConfig
    mqtt: MqttConfig
    language: LanguageConfig
    timezone: str
    ntp_server: str
    reboot_counter: int
    reboots_total: int
    reboots_all: int
    led_enable: bool
    api_auth_required: bool
    device_name: str
    aws_iot_enabled: bool


# --- Auth models ---


@dataclass(frozen=True)
class TokenGenerateResponse:
    """Response from POST /auth/tokens/generate."""

    success: bool
    token_read: str
    token_write: str
    expires_in: int


# --- MQTT CA models ---


@dataclass(frozen=True)
class CaCertStatus:
    """Response from GET /mqtt/ca."""

    has_custom_cert: bool
    bundle_size: int
    custom_size: int


# --- Parsing helpers ---


def _parse_alive(data: dict[str, Any]) -> AliveResponse:
    """Parse alive response."""
    return AliveResponse(alive=data["alive"], version=data["version"])


def _parse_info_entries(items: list[dict[str, Any]]) -> list[InfoEntry]:
    """Parse a list of info entries."""
    return [
        InfoEntry(
            name=item["name"],
            value=str(item["value"]),
            unit=item.get("unit", ""),
        )
        for item in items
    ]


def _parse_system_info(data: dict[str, Any]) -> SystemInfo:
    """Parse system info response."""
    return SystemInfo(
        uptime=_parse_info_entries(data.get("uptime", [])),
        wifi=_parse_info_entries(data.get("wifi", [])),
        ap=_parse_info_entries(data.get("ap", [])),
        esp=_parse_info_entries(data.get("esp", [])),
        heap=_parse_info_entries(data.get("heap", [])),
    )


def _parse_led_info(data: dict[str, Any]) -> LedInfo:
    """Parse LED info response."""
    rgb = data.get("rgb", {})
    return LedInfo(
        status=LedStatus(data["status"]),
        priority=data["priority"],
        color=LedColor(data["color"]),
        mode=LedMode(data["mode"]),
        rgb=RgbColor(r=rgb.get("r", 0), g=rgb.get("g", 0), b=rgb.get("b", 0)),
        enabled=data["enabled"],
        active_statuses=data.get("active_statuses", {}),
    )


def _parse_self_test(data: dict[str, Any]) -> SelfTestResult:
    """Parse self-test response."""
    return SelfTestResult(
        success=data["success"],
        result=data["result"],
        message=data["message"],
    )


def _parse_wifi_scan(data: dict[str, Any]) -> WifiScanResponse:
    """Parse WiFi scan response."""
    return WifiScanResponse(
        networks=[
            WifiNetwork(ssid=n["ssid"], rssi=n["rssi"])
            for n in data.get("networks", [])
        ],
        count=data.get("count", 0),
        scanning=data.get("scanning", False),
    )


def _parse_meter_data(data: dict[str, Any]) -> MeterData:
    """Parse meter data response."""
    values: dict[str, ObisValue] = {}
    timestamp = data.get("timestamp", 0)
    datetime_str = data.get("datetime", "")
    for key, val in data.items():
        if key in ("timestamp", "datetime"):
            continue
        if isinstance(val, dict) and "value" in val:
            values[key] = ObisValue(value=val["value"], unit=val.get("unit", ""))
    return MeterData(
        timestamp=timestamp,
        datetime_str=datetime_str,
        values=values,
    )


def _parse_high_res_history(data: dict[str, Any]) -> HighResHistory:
    """Parse high-resolution history response."""
    summary_data = data.get("summary", {})
    return HighResHistory(
        start=data["start"],
        days=data["days"],
        items=[
            HighResEntry(
                date=item["date"],
                timestamp=item["timestamp"],
                imp=item["imp"],
                exp=item["exp"],
                pwr=item["pwr"],
                di=item["di"],
                de=item["de"],
            )
            for item in data.get("items", [])
        ],
        summary=HighResSummary(
            total_import=summary_data.get("total_import", 0.0),
            total_export=summary_data.get("total_export", 0.0),
        ),
    )


def _parse_low_res_history(data: dict[str, Any]) -> LowResHistory:
    """Parse low-resolution history response."""
    summary_data = data.get("summary", {})
    return LowResHistory(
        start=data["start"],
        days=data["days"],
        items=[
            LowResEntry(
                date=item["date"],
                imp=item["imp"],
                exp=item["exp"],
                di=item["di"],
                de=item["de"],
            )
            for item in data.get("items", [])
        ],
        summary=HighResSummary(
            total_import=summary_data.get("total_import", 0.0),
            total_export=summary_data.get("total_export", 0.0),
        ),
    )


def _parse_ota_check(data: dict[str, Any]) -> OtaCheckResponse:
    """Parse OTA check response."""
    ota = data.get("data", {})
    return OtaCheckResponse(
        ok=data["ok"],
        data=OtaData(
            update_available=ota.get("update_available", False),
            version=ota.get("version", ""),
            tag=ota.get("tag", ""),
            release_date=ota.get("release_date", ""),
            release_note_de=ota.get("release_note_de", ""),
            release_note_en=ota.get("release_note_en", ""),
            last_checked=ota.get("last_checked", 0),
        ),
    )


def _parse_wifi_config(data: dict[str, Any]) -> WifiConfig:
    """Parse a WiFi config block."""
    return WifiConfig(
        enable=data.get("enable", False),
        ssid=data.get("ssid", ""),
        static_ip=data.get("static_ip", False),
        ip=data.get("ip", ""),
        subnet=data.get("subnet", ""),
        gateway=data.get("gateway", ""),
        dns=data.get("dns", ""),
    )


def _parse_settings(data: dict[str, Any]) -> Settings:
    """Parse settings response."""
    wifi = data.get("wifi", {})
    ap = data.get("accessPoint", {})
    mqtt = data.get("mqtt", {})
    lang = data.get("language", {})
    return Settings(
        wifi_primary=_parse_wifi_config(wifi.get("primary", {})),
        wifi_secondary=_parse_wifi_config(wifi.get("secondary", {})),
        access_point=AccessPointConfig(
            enable=ap.get("enable", False),
            password_enable=ap.get("password_enable", False),
            ssid=ap.get("ssid", ""),
        ),
        mqtt=MqttConfig(
            enable=mqtt.get("enable", False),
            host=mqtt.get("host", ""),
            port=mqtt.get("port", 1883),
            use_tls=mqtt.get("use_tls", False),
            user=mqtt.get("user", ""),
            sendInterval=mqtt.get("sendInterval", 10),
            client_id=mqtt.get("client_id", ""),
            topic_prefix=mqtt.get("topic_prefix", ""),
        ),
        language=LanguageConfig(
            active=lang.get("active", ""),
            installed=[
                LanguageEntry(code=l["code"], name=l["name"])
                for l in lang.get("installed", [])
            ],
        ),
        timezone=data.get("timezone", ""),
        ntp_server=data.get("ntp_server", ""),
        reboot_counter=data.get("rebootCounter", 0),
        reboots_total=data.get("rebootsTotal", 0),
        reboots_all=data.get("rebootsAll", 0),
        led_enable=data.get("ledEnable", True),
        api_auth_required=data.get("api_auth_required", True),
        device_name=data.get("device_name", ""),
        aws_iot_enabled=data.get("awsIotEnabled", False),
    )


def _parse_token_generate(data: dict[str, Any]) -> TokenGenerateResponse:
    """Parse token generate response."""
    pending = data.get("pending", {})
    return TokenGenerateResponse(
        success=data["success"],
        token_read=pending["token_read"],
        token_write=pending["token_write"],
        expires_in=data.get("expires_in", 60),
    )


def _parse_ca_cert_status(data: dict[str, Any]) -> CaCertStatus:
    """Parse CA certificate status response."""
    return CaCertStatus(
        has_custom_cert=data["has_custom_cert"],
        bundle_size=data["bundle_size"],
        custom_size=data["custom_size"],
    )
