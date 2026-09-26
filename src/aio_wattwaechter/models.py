"""Data models for the WattWächter API."""

from __future__ import annotations

from dataclasses import dataclass
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

    @property
    def device_id(self) -> str | None:
        """Bare device ID (MAC without separators), e.g. '9BFEFF453AB4'."""
        return self.get_value("esp", "esp_id") or None

    @property
    def firmware_version(self) -> str | None:
        """Installed firmware version."""
        return self.get_value("esp", "os_version") or None

    @property
    def model_id(self) -> str | None:
        """Hardware model ID, e.g. 'ww_plus', 'ww_gw_mf' or 'ww_gw_id'.

        None on firmware that does not report it yet (older WattWächter Plus).
        """
        return self.get_value("esp", "model_id") or None

    @property
    def product_name(self) -> str | None:
        """Product name, e.g. 'WattWächter Plus', 'WattWächter Gas'.

        On gas/water devices the name follows the configured medium and can
        change at runtime. None on firmware that does not report it yet.
        """
        return self.get_value("esp", "product_name") or None

    @property
    def is_gas_water(self) -> bool:
        """True for gas/water devices (GW-MF / GW-ID)."""
        return (self.model_id or "").startswith("ww_gw")


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


@dataclass(frozen=True)
class TimezoneEntry:
    """A supported timezone."""

    name: str
    gmt_offset: int
    daylight_offset: int


# --- History / Meter models ---


class Medium(StrEnum):
    """Metered medium."""

    ELECTRICITY = "electricity"
    GAS = "gas"
    WATER = "water"


# Gas/water devices report full OBIS codes (value group A = medium), because
# the short C.D.E form means something else for electricity.
OBIS_GAS_VOLUME = "7-0:3.0.0"
"""Gas volume (meter reading) in m³."""
OBIS_GAS_FLOW = "7-0:43.0.0"
"""Gas flow rate in m³/h."""
OBIS_WATER_VOLUME = "8-0:1.0.0"
"""Water volume (meter reading) in m³."""
OBIS_WATER_FLOW = "8-0:2.0.0"
"""Water flow rate in m³/h."""

VOLUME_OBIS: dict[Medium, str] = {
    Medium.GAS: OBIS_GAS_VOLUME,
    Medium.WATER: OBIS_WATER_VOLUME,
}
FLOW_OBIS: dict[Medium, str] = {
    Medium.GAS: OBIS_GAS_FLOW,
    Medium.WATER: OBIS_WATER_FLOW,
}


@dataclass(frozen=True)
class GwStatus:
    """Pulse sensor status of a gas/water device (``gw`` block of /history/latest).

    ``raw`` holds the complete block including driver specific diagnostics.
    """

    ok: bool
    medium: Medium | None
    revolutions: float
    coils: int
    active_coils: int
    energy_factor: float
    raw: dict[str, Any]


@dataclass(frozen=True)
class ObisValue:
    """A single OBIS code value from the smart meter."""

    value: float | str
    unit: str
    name: str


@dataclass(frozen=True)
class MeterData:
    """Response from GET /history/latest."""

    timestamp: int
    datetime_str: str
    values: dict[str, ObisValue]
    gw: GwStatus | None = None

    def get(self, obis_code: str) -> ObisValue | None:
        """Get a value by OBIS code (e.g. '16.7.0')."""
        return self.values.get(obis_code)

    def _as_float(self, obis_code: str) -> float | None:
        """Get a numeric OBIS value as float, or None."""
        val = self.get(obis_code)
        if val is None:
            return None
        try:
            return float(val.value)
        except (ValueError, TypeError):
            return None

    @property
    def power(self) -> float | None:
        """Total active power in W (OBIS 16.7.0)."""
        return self._as_float("16.7.0")

    @property
    def total_consumption(self) -> float | None:
        """Total consumption in kWh (OBIS 1.8.0)."""
        return self._as_float("1.8.0")

    @property
    def total_feed_in(self) -> float | None:
        """Total feed-in in kWh (OBIS 2.8.0)."""
        return self._as_float("2.8.0")

    @property
    def medium(self) -> Medium:
        """Metered medium.

        Gas/water devices can switch the medium at runtime, which also switches
        the reported OBIS codes. The ``gw`` block is authoritative; without it
        the medium is derived from the reported OBIS codes.
        """
        if self.gw is not None and self.gw.medium is not None:
            return self.gw.medium
        for medium in (Medium.GAS, Medium.WATER):
            if VOLUME_OBIS[medium] in self.values or FLOW_OBIS[medium] in self.values:
                return medium
        return Medium.ELECTRICITY

    @property
    def is_volume_meter(self) -> bool:
        """True for gas/water meters (values in m³ and m³/h)."""
        return self.medium is not Medium.ELECTRICITY

    @property
    def volume_obis(self) -> str | None:
        """OBIS code of the volume register for the current medium."""
        return VOLUME_OBIS.get(self.medium)

    @property
    def flow_obis(self) -> str | None:
        """OBIS code of the flow rate register for the current medium."""
        return FLOW_OBIS.get(self.medium)

    @property
    def volume(self) -> float | None:
        """Gas/water meter reading in m³ (None on electricity meters)."""
        obis = self.volume_obis
        return self._as_float(obis) if obis else None

    @property
    def flow(self) -> float | None:
        """Gas/water flow rate in m³/h (None on electricity meters)."""
        obis = self.flow_obis
        return self._as_float(obis) if obis else None


UNIT_KWH = "kWh"
UNIT_M3 = "m³"


@dataclass(frozen=True)
class HighResEntry:
    """A single entry in high-resolution history data.

    Electricity (WattWächter Plus) fills the ``*_kwh``/``*_kw``/``power_w``
    fields. Gas/water devices fill the ``*_m3*`` fields instead and leave the
    electricity fields at 0.0 (they have no export register).
    """

    date: str
    timestamp: int
    import_total_kwh: float = 0.0
    export_total_kwh: float = 0.0
    import_kw: float = 0.0
    export_kw: float = 0.0
    power_w: float = 0.0
    import_total_m3: float | None = None
    import_m3h: float | None = None
    flow_m3h: float | None = None

    @property
    def import_total(self) -> float:
        """Meter reading in the unit of the meter (kWh or m³)."""
        if self.import_total_m3 is not None:
            return self.import_total_m3
        return self.import_total_kwh


@dataclass(frozen=True)
class HighResHistory:
    """Response from GET /history/highRes.

    ``unit`` is the unit of the meter readings: ``kWh`` or ``m³``.
    """

    start: str
    days: int
    items: list[HighResEntry]
    import_total_kwh: float
    export_total_kwh: float
    consumption_m3: float | None = None
    unit: str = UNIT_KWH

    @property
    def is_volume(self) -> bool:
        """True if the history is in m³ (gas/water device)."""
        return self.unit == UNIT_M3

    @property
    def consumption(self) -> float:
        """Consumption over the whole response in ``unit``.

        On electricity the firmware reports it as ``import_total_kWh``.
        """
        if self.consumption_m3 is not None:
            return self.consumption_m3
        return self.import_total_kwh


@dataclass(frozen=True)
class LowResEntry:
    """A single entry (one day) in low-resolution history data.

    Electricity fills the ``*_kwh`` fields, gas/water the ``*_m3`` fields.
    """

    date: str
    timestamp: int
    import_total_kwh: float = 0.0
    export_total_kwh: float = 0.0
    import_kwh: float = 0.0
    export_kwh: float = 0.0
    import_total_m3: float | None = None
    import_m3: float | None = None

    @property
    def import_total(self) -> float:
        """Meter reading at the start of the day (kWh or m³)."""
        if self.import_total_m3 is not None:
            return self.import_total_m3
        return self.import_total_kwh

    @property
    def consumption(self) -> float:
        """Consumption of the day (kWh or m³)."""
        if self.import_m3 is not None:
            return self.import_m3
        return self.import_kwh


@dataclass(frozen=True)
class LowResHistory:
    """Response from GET /history/lowRes.

    ``unit`` is the unit of the meter readings: ``kWh`` or ``m³``.
    """

    start: str
    items: list[LowResEntry]
    import_total_kwh: float
    export_total_kwh: float
    consumption_m3: float | None = None
    unit: str = UNIT_KWH

    @property
    def is_volume(self) -> bool:
        """True if the history is in m³ (gas/water device)."""
        return self.unit == UNIT_M3

    @property
    def consumption(self) -> float:
        """Consumption over the whole response in ``unit``."""
        if self.consumption_m3 is not None:
            return self.consumption_m3
        return self.import_total_kwh


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
    url: str
    md5: str


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


@dataclass(frozen=True)
class CaCertActionResponse:
    """Response from POST/DELETE /mqtt/ca."""

    success: bool
    message: str
    bundle_size: int


# --- MQTT status models ---


class MqttState(StrEnum):
    """MQTT connection state."""

    OFF = "OFF"
    INIT = "INIT"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    WAIT_RETRY = "WAIT_RETRY"
    FAILED = "FAILED"


@dataclass(frozen=True)
class MqttStatus:
    """Response from GET /mqtt/status."""

    enabled: bool
    state: MqttState
    host: str
    port: int
    client_id: str
    use_tls: bool
    last_error: int
    last_error_message: str
    reconnect_attempts: int

    @property
    def connected(self) -> bool:
        """True if MQTT is currently connected to the broker."""
        return self.state == MqttState.CONNECTED


# --- Modbus status models ---


@dataclass(frozen=True)
class ModbusRegisterInfo:
    """A single Modbus register entry in the status response."""

    register: int
    name: str
    obis: str
    value: float | None
    unit: str
    valid: bool


@dataclass(frozen=True)
class ModbusStatus:
    """Response from GET /modbus/status."""

    enabled: bool
    running: bool
    port: int
    active_connections: int
    registers: list[ModbusRegisterInfo]


# --- Parsing helpers ---


def _parse_alive(data: dict[str, Any]) -> AliveResponse:
    """Parse alive response.

    The firmware reports only ``alive`` and ``version``; unknown keys are
    ignored and missing ones fall back to defaults.
    """
    return AliveResponse(
        alive=bool(data.get("alive", False)),
        version=str(data.get("version", "")),
    )


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


def _parse_timezones(data: list[dict[str, Any]]) -> list[TimezoneEntry]:
    """Parse timezones response."""
    return [
        TimezoneEntry(
            name=tz["name"],
            gmt_offset=tz["gmtOffset"],
            daylight_offset=tz["daylightOffset"],
        )
        for tz in data
    ]


def _parse_medium(value: object) -> Medium | None:
    """Parse a medium name, None if unknown."""
    if not isinstance(value, str):
        return None
    try:
        return Medium(value)
    except ValueError:
        return None


def _parse_gw_status(data: dict[str, Any]) -> GwStatus:
    """Parse the ``gw`` status block of a gas/water device."""
    return GwStatus(
        ok=bool(data.get("ok", False)),
        medium=_parse_medium(data.get("medium")),
        revolutions=float(data.get("revolutions", 0.0)),
        coils=int(data.get("coils", 0)),
        active_coils=int(data.get("activeCoils", 0)),
        energy_factor=float(data.get("energyFactor", 0.0)),
        raw=dict(data),
    )


def _parse_meter_data(data: dict[str, Any]) -> MeterData:
    """Parse meter data response."""
    values: dict[str, ObisValue] = {}
    timestamp = data.get("timestamp", 0)
    datetime_str = data.get("datetime", "")
    gw: GwStatus | None = None
    for key, val in data.items():
        if key in ("timestamp", "datetime"):
            continue
        if key == "gw" and isinstance(val, dict):
            gw = _parse_gw_status(val)
            continue
        if isinstance(val, dict) and "value" in val:
            values[key] = ObisValue(
                value=val["value"],
                unit=val.get("unit", ""),
                name=val.get("name", ""),
            )
    return MeterData(
        timestamp=timestamp,
        datetime_str=datetime_str,
        values=values,
        gw=gw,
    )


def _optional_float(data: dict[str, Any], key: str) -> float | None:
    """Return data[key] as float, or None if missing."""
    value = data.get(key)
    return None if value is None else float(value)


def _is_volume_history(data: dict[str, Any]) -> bool:
    """Return True if a history response carries m³ keys (gas/water device)."""
    if "consumption_m3" in data:
        return True
    return any("import_total_m3" in item for item in data.get("items", []))


def _parse_high_res_history(data: dict[str, Any]) -> HighResHistory:
    """Parse high-resolution history response.

    Electricity: import_total_kWh, export_total_kWh, import_kW, export_kW,
    power_W. Gas/water: import_total_m3, import_m3h, flow_m3h and the footer
    consumption_m3 (no export keys).
    """
    return HighResHistory(
        start=data["start"],
        days=data.get("days", 1),
        items=[
            HighResEntry(
                date=item["date"],
                timestamp=item["timestamp"],
                import_total_kwh=item.get("import_total_kWh", 0.0),
                export_total_kwh=item.get("export_total_kWh", 0.0),
                import_kw=item.get("import_kW", 0.0),
                export_kw=item.get("export_kW", 0.0),
                power_w=item.get("power_W", 0.0),
                import_total_m3=_optional_float(item, "import_total_m3"),
                import_m3h=_optional_float(item, "import_m3h"),
                flow_m3h=_optional_float(item, "flow_m3h"),
            )
            for item in data.get("items", [])
        ],
        import_total_kwh=data.get("import_total_kWh", 0.0),
        export_total_kwh=data.get("export_total_kWh", 0.0),
        consumption_m3=_optional_float(data, "consumption_m3"),
        unit=UNIT_M3 if _is_volume_history(data) else UNIT_KWH,
    )


def _parse_low_res_history(data: dict[str, Any]) -> LowResHistory:
    """Parse low-resolution history response.

    Electricity: import_total_kWh, export_total_kWh, import_kWh, export_kWh.
    Gas/water: import_total_m3, import_m3 and the footer consumption_m3.
    """
    return LowResHistory(
        start=data["start"],
        items=[
            LowResEntry(
                date=item["date"],
                timestamp=item.get("timestamp", 0),
                import_total_kwh=item.get("import_total_kWh", 0.0),
                export_total_kwh=item.get("export_total_kWh", 0.0),
                import_kwh=item.get("import_kWh", 0.0),
                export_kwh=item.get("export_kWh", 0.0),
                import_total_m3=_optional_float(item, "import_total_m3"),
                import_m3=_optional_float(item, "import_m3"),
            )
            for item in data.get("items", [])
        ],
        import_total_kwh=data.get("import_total_kWh", 0.0),
        export_total_kwh=data.get("export_total_kWh", 0.0),
        consumption_m3=_optional_float(data, "consumption_m3"),
        unit=UNIT_M3 if _is_volume_history(data) else UNIT_KWH,
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
            url=ota.get("url", ""),
            md5=ota.get("md5", ""),
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
            port=mqtt.get("port", 8883),
            use_tls=mqtt.get("use_tls", True),
            user=mqtt.get("user", ""),
            sendInterval=mqtt.get("sendInterval", 60),
            client_id=mqtt.get("client_id", ""),
            topic_prefix=mqtt.get("topic_prefix", ""),
        ),
        language=LanguageConfig(
            active=lang.get("active", ""),
            installed=[
                LanguageEntry(code=entry["code"], name=entry["name"])
                for entry in lang.get("installed", [])
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


def _parse_ca_cert_action(data: dict[str, Any]) -> CaCertActionResponse:
    """Parse CA certificate upload/delete response."""
    return CaCertActionResponse(
        success=data.get("success", False),
        message=data.get("message", ""),
        bundle_size=data.get("bundle_size", 0),
    )


def _parse_mqtt_status(data: dict[str, Any]) -> MqttStatus:
    """Parse MQTT status response."""
    return MqttStatus(
        enabled=data["enabled"],
        state=MqttState(data["state"]),
        host=data.get("host", ""),
        port=data.get("port", 0),
        client_id=data.get("client_id", ""),
        use_tls=data.get("use_tls", False),
        last_error=data.get("last_error", 0),
        last_error_message=data.get("last_error_message", ""),
        reconnect_attempts=data.get("reconnect_attempts", 0),
    )


def _parse_modbus_status(data: dict[str, Any]) -> ModbusStatus:
    """Parse Modbus TCP status response."""
    registers = [
        ModbusRegisterInfo(
            register=r["register"],
            name=r.get("name", ""),
            obis=r.get("obis", ""),
            value=r.get("value"),
            unit=r.get("unit", ""),
            valid=r.get("valid", False),
        )
        for r in data.get("registers", [])
    ]
    return ModbusStatus(
        enabled=data["enabled"],
        running=data["running"],
        port=data["port"],
        active_connections=data.get("active_connections", 0),
        registers=registers,
    )
