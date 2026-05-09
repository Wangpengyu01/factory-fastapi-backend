"""FastAPI 后端主入口。

本文件负责把 Nacos 配置读写、8083 前端兼容接口、Dashboard 聚合接口、
硬件状态机模拟器接口统一注册到同一个 FastAPI 应用里。
"""

import asyncio
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.hardware_state_machine import SIMULATOR

try:
    import yaml
except Exception:  # pragma: no cover
    # PyYAML 是可选依赖；没有安装时只解析 JSON，接口仍然可以正常启动。
    yaml = None

load_dotenv()

# FastAPI 应用对象，所有路由都会挂载到这个 app 上。
app = FastAPI(
    title="Nacos FastAPI Bridge",
    version="1.1.0",
    description=(
        "FastAPI bridge for Nacos config read/write. "
        "Supports optional dataId for full read, field-level read, and publish key protection."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# 允许访问后端的前端来源，开发期默认包含旧静态页和 8083 Vue + Vite 前端。
raw_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:9000,http://localhost:8083",
)
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Nacos 和发布密钥配置全部来自环境变量，避免把真实地址或密钥写死进代码。
NACOS_BASE_URL = os.getenv("NACOS_BASE_URL", "http://127.0.0.1:8848/nacos").rstrip("/")
NACOS_USERNAME = os.getenv("NACOS_USERNAME", "").strip()
NACOS_PASSWORD = os.getenv("NACOS_PASSWORD", "").strip()
NACOS_API_VERSION = os.getenv("NACOS_API_VERSION", "v1").strip().lower()
PUBLISH_API_KEY = os.getenv("PUBLISH_API_KEY", "").strip()


def _env_bool(name: str, default: bool = False) -> bool:
    """把环境变量解析成布尔值，兼容 true/yes/on/1 等常见写法。"""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, *, minimum: int | None = None) -> int:
    """把环境变量解析成整数；非法值回退到默认值。"""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw.strip())
    except ValueError:
        return default
    if minimum is not None:
        value = max(minimum, value)
    return value


# 硬件状态机模拟器开关；真实硬件接入前，前端先通过这些模拟状态联调。
USE_STATE_MACHINE_SIMULATOR = _env_bool("USE_STATE_MACHINE_SIMULATOR", True)
SIMULATOR_AUTO_TICK = _env_bool("SIMULATOR_AUTO_TICK", True)
SIMULATOR_TICK_SECONDS = max(1.0, float(os.getenv("SIMULATOR_TICK_SECONDS", "5")))

# 设备状态默认数据源：
# simulator/demo 用于本地开发；nacos 用于“Python 模拟器 -> Nacos -> FastAPI -> 大屏”链路。
DEFAULT_SIMULATOR_NACOS_DATA_ID = "factory.hardware.snapshot.json"
SIMULATOR_NACOS_SYNC_ENABLED = _env_bool("SIMULATOR_NACOS_SYNC_ENABLED", False)
SIMULATOR_NACOS_SYNC_INTERVAL_TICKS = _env_int("SIMULATOR_NACOS_SYNC_INTERVAL_TICKS", 1, minimum=1)
SIMULATOR_NACOS_DATA_ID = (
    os.getenv("SIMULATOR_NACOS_DATA_ID", DEFAULT_SIMULATOR_NACOS_DATA_ID).strip()
    or DEFAULT_SIMULATOR_NACOS_DATA_ID
)
SIMULATOR_NACOS_GROUP = os.getenv("SIMULATOR_NACOS_GROUP", "DEFAULT_GROUP").strip() or "DEFAULT_GROUP"
SIMULATOR_NACOS_TENANT = os.getenv("SIMULATOR_NACOS_TENANT", "").strip() or None
SIMULATOR_NACOS_CONFIG_TYPE = os.getenv("SIMULATOR_NACOS_CONFIG_TYPE", "json").strip() or "json"

DEVICE_STATUS_SOURCE = os.getenv("DEVICE_STATUS_SOURCE", "simulator").strip().lower()
DEVICE_STATUS_NACOS_DATA_ID = (
    os.getenv("DEVICE_STATUS_NACOS_DATA_ID", SIMULATOR_NACOS_DATA_ID).strip()
    or SIMULATOR_NACOS_DATA_ID
)
DEVICE_STATUS_NACOS_GROUP = os.getenv("DEVICE_STATUS_NACOS_GROUP", SIMULATOR_NACOS_GROUP).strip() or SIMULATOR_NACOS_GROUP
DEVICE_STATUS_NACOS_TENANT = os.getenv("DEVICE_STATUS_NACOS_TENANT", "").strip() or SIMULATOR_NACOS_TENANT
DEVICE_STATUS_NACOS_FIELD = os.getenv("DEVICE_STATUS_NACOS_FIELD", "deviceStatus.records").strip()
NACOS_READ_FALLBACK_TO_SIMULATOR = _env_bool("NACOS_READ_FALLBACK_TO_SIMULATOR", True)

SUBSYSTEM_BASE_URL = os.getenv("SUBSYSTEM_BASE_URL", "").strip().rstrip("/")
SUBSYSTEM_FACE_URL = os.getenv("SUBSYSTEM_FACE_URL", "").strip()
SUBSYSTEM_VEHICLE_URL = os.getenv("SUBSYSTEM_VEHICLE_URL", "").strip()
SUBSYSTEM_RAIL_URL = os.getenv("SUBSYSTEM_RAIL_URL", "").strip()
SUBSYSTEM_FIRE_URL = os.getenv("SUBSYSTEM_FIRE_URL", "").strip()

_cached_token: str | None = None
_token_expire_at = 0.0
_auth_lock = asyncio.Lock()
_simulator_task: asyncio.Task[None] | None = None
_simulator_nacos_sync_status: dict[str, Any] = {
    "enabled": SIMULATOR_NACOS_SYNC_ENABLED,
    "dataId": SIMULATOR_NACOS_DATA_ID,
    "group": SIMULATOR_NACOS_GROUP,
    "tenant": SIMULATOR_NACOS_TENANT,
    "lastSuccessAt": None,
    "lastErrorAt": None,
    "lastError": None,
    "lastTick": None,
}


class PublishConfigBody(BaseModel):
    """发布 Nacos 配置时的请求体。"""

    data_id: str = Field(..., alias="dataId", min_length=1)
    group: str = Field(default="DEFAULT_GROUP")
    tenant: str | None = None
    content: str = Field(..., min_length=1)
    config_type: str = Field(default="text", alias="type")

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str


class ConfigItem(BaseModel):
    """Nacos 配置项读取后的统一结构。"""

    data_id: str = Field(..., alias="dataId")
    group: str
    tenant: str | None = None
    content: str
    parsed: Any | None = None
    value: Any | None = None

    model_config = {"populate_by_name": True}


class ConfigReadResponse(BaseModel):
    """读取 Nacos 配置的响应，兼容单配置读取和全量列表读取。"""

    mode: Literal["single", "all"]
    data_id: str | None = Field(default=None, alias="dataId")
    group: str | None = None
    tenant: str | None = None
    field: str | None = None
    content: str | None = None
    parsed: Any | None = None
    value: Any | None = None
    total: int | None = None
    items: list[ConfigItem] | None = None
    merged_params: dict[str, Any] | None = Field(default=None, alias="mergedParams")

    model_config = {"populate_by_name": True}


class PublishConfigResponse(BaseModel):
    """发布 Nacos 配置的响应。"""

    success: bool
    message: str


class DeviceStatusRecord(BaseModel):
    """8083 设备状态组件需要的单行统计数据。"""

    region: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    online: int = Field(..., ge=0)
    offline: int = Field(..., ge=0)


class DeviceStatusOptionsResponse(BaseModel):
    """设备状态筛选项响应。"""

    regions: list[str]
    devices: list[str]


class DeviceStatusRecordsResponse(BaseModel):
    """设备状态列表响应。"""

    records: list[DeviceStatusRecord]
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class DeviceStatusSummary(BaseModel):
    """设备状态汇总数据。"""

    total_devices: int = Field(..., alias="totalDevices")
    online_devices: int = Field(..., alias="onlineDevices")
    offline_devices: int = Field(..., alias="offlineDevices")
    online_rate: float = Field(..., alias="onlineRate")

    model_config = {"populate_by_name": True}


class DeviceStatusSummaryResponse(BaseModel):
    """设备状态汇总接口响应。"""

    summary: DeviceStatusSummary
    records: list[DeviceStatusRecord]


class ApiResponse(BaseModel):
    """通用 JSON 响应结构，新接口优先使用该结构。"""

    code: int = 200
    success: bool = True
    message: str = "操作成功"
    data: Any


class HardwareCommandBody(BaseModel):
    """手动控制模拟硬件时的请求体。"""

    command: str = Field(..., min_length=1)
    reason: str = ""
    operator: str = "simulator"
    payload: dict[str, Any] = Field(default_factory=dict)


# 8083 旧前端使用“全部”作为筛选默认值，这里保持兼容。
ALL_OPTION = "全部"
DEFAULT_DEVICE_STATUS_FIELD = "deviceStatus.records"
SHANGHAI_TZ = timezone(timedelta(hours=8))

# 当未提供 Nacos dataId 时返回的兜底数据；开启模拟器后会优先从状态机聚合。
DEMO_DEVICE_STATUS_RECORDS: list[dict[str, Any]] = [
    {"region": "A区", "device": "人员智能门/联锁门", "online": 120, "offline": 12},
    {"region": "A区", "device": "摄像机", "online": 86, "offline": 6},
    {"region": "F区", "device": "车辆识别与道闸", "online": 42, "offline": 5},
    {"region": "F区", "device": "声光报警", "online": 24, "offline": 2},
    {"region": "L区", "device": "烟感器", "online": 65, "offline": 4},
    {"region": "L区", "device": "温感器", "online": 61, "offline": 3},
    {"region": "成品库", "device": "摄像机", "online": 48, "offline": 5},
    {"region": "成品库", "device": "光电报警", "online": 19, "offline": 1},
    {"region": "火车道", "device": "火车道联动门", "online": 12, "offline": 0},
    {"region": "道路", "device": "车辆识别与道闸", "online": 16, "offline": 2},
    {"region": "厂房", "device": "烟感器", "online": 94, "offline": 8},
    {"region": "作业区", "device": "摄像机", "online": 71, "offline": 9},
]


async def _run_simulator_loop() -> None:
    """后台循环推进模拟器状态，让前端看到持续变化的数据。"""
    while True:
        SIMULATOR.tick()
        if (
            SIMULATOR_NACOS_SYNC_ENABLED
            and SIMULATOR.tick_no % SIMULATOR_NACOS_SYNC_INTERVAL_TICKS == 0
        ):
            try:
                await _sync_simulator_snapshot_to_nacos()
            except Exception as exc:  # pragma: no cover - depends on external Nacos.
                _record_simulator_nacos_sync_error(exc)
        await asyncio.sleep(SIMULATOR_TICK_SECONDS)


@app.on_event("startup")
async def _start_simulator_loop() -> None:
    """服务启动时按配置启动模拟器后台任务。"""
    global _simulator_task
    if USE_STATE_MACHINE_SIMULATOR and SIMULATOR_AUTO_TICK and _simulator_task is None:
        _simulator_task = asyncio.create_task(_run_simulator_loop())


@app.on_event("shutdown")
async def _stop_simulator_loop() -> None:
    """服务关闭时取消模拟器后台任务，避免事件循环残留任务。"""
    global _simulator_task
    if _simulator_task is not None:
        _simulator_task.cancel()
        _simulator_task = None


def _join_url(path: str) -> str:
    """拼接 Nacos API 完整地址。"""
    return f"{NACOS_BASE_URL}{path}"


def _parse_content(content: str) -> Any | None:
    """把 Nacos 配置内容解析成 JSON/YAML 对象；解析失败返回 None。"""
    if not content:
        return None

    try:
        return json.loads(content)
    except Exception:
        pass

    if yaml is not None:
        try:
            return yaml.safe_load(content)
        except Exception:
            pass

    return None


def _extract_field(data: Any, field: str) -> tuple[Any, bool]:
    """按 a.b.0.c 形式从 dict/list 中提取字段。"""
    current: Any = data
    for part in field.split("."):
        if isinstance(current, dict):
            if part not in current:
                return None, False
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit():
            idx = int(part)
            if idx < 0 or idx >= len(current):
                return None, False
            current = current[idx]
            continue
        return None, False
    return current, True


def _check_publish_key(x_publish_key: str | None) -> None:
    """校验发布配置接口的 X-Publish-Key。"""
    if not PUBLISH_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Publish API key is not configured on server.",
        )
    if not x_publish_key or not secrets.compare_digest(x_publish_key, PUBLISH_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid X-Publish-Key.")


def _normalize_selector(value: str | None, *, default: str = ALL_OPTION) -> str:
    """统一处理前端筛选参数，空值按“全部”处理。"""
    normalized = (value or "").strip()
    return normalized or default


def _coerce_non_negative_int(value: Any, *, field_name: str, index: int) -> int:
    """把外部配置中的 online/offline 字段转换成非负整数。"""
    if isinstance(value, bool):
        raise HTTPException(
            status_code=422,
            detail=f"device status record[{index}].{field_name} must be a non-negative integer.",
        )

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"device status record[{index}].{field_name} must be a non-negative integer.",
        ) from exc

    if number < 0:
        raise HTTPException(
            status_code=422,
            detail=f"device status record[{index}].{field_name} must be a non-negative integer.",
        )
    return number


def _coerce_device_status_records(raw: Any) -> list[DeviceStatusRecord]:
    """把 Nacos 或模拟器数据转换成 8083 设备状态组件需要的记录列表。"""
    candidate = raw
    if isinstance(candidate, dict):
        if isinstance(candidate.get("records"), list):
            candidate = candidate["records"]
        elif (
            isinstance(candidate.get("deviceStatus"), dict)
            and isinstance(candidate["deviceStatus"].get("records"), list)
        ):
            candidate = candidate["deviceStatus"]["records"]

    if not isinstance(candidate, list):
        raise HTTPException(
            status_code=422,
            detail="Device status config must be a records array or an object containing records.",
        )

    records: list[DeviceStatusRecord] = []
    for index, item in enumerate(candidate):
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=422,
                detail=f"device status record[{index}] must be an object.",
            )

        region = str(item.get("region", "")).strip()
        device = str(item.get("device", "")).strip()
        if not region or not device:
            raise HTTPException(
                status_code=422,
                detail=f"device status record[{index}] must include region and device.",
            )

        records.append(
            DeviceStatusRecord(
                region=region,
                device=device,
                online=_coerce_non_negative_int(item.get("online"), field_name="online", index=index),
                offline=_coerce_non_negative_int(item.get("offline"), field_name="offline", index=index),
            )
        )

    return records


def _get_local_device_status_records() -> list[DeviceStatusRecord]:
    """获取本地设备状态数据；demo 强制兜底，simulator 使用状态机实时聚合。"""
    if DEVICE_STATUS_SOURCE != "demo" and USE_STATE_MACHINE_SIMULATOR:
        return [
            DeviceStatusRecord(**item)
            for item in SIMULATOR.aggregate_device_status_records()
        ]
    return [DeviceStatusRecord(**item) for item in DEMO_DEVICE_STATUS_RECORDS]


def _get_demo_device_status_records() -> list[DeviceStatusRecord]:
    """兼容旧调用名，返回当前本地数据源的设备状态记录。"""
    return _get_local_device_status_records()


def _build_device_status_document(records: list[DeviceStatusRecord]) -> dict[str, Any]:
    """把设备状态记录整理成前端和 Nacos 都能复用的结构。"""
    online = sum(record.online for record in records)
    offline = sum(record.offline for record in records)
    total = online + offline
    return {
        "summary": {
            "totalDevices": total,
            "onlineDevices": online,
            "offlineDevices": offline,
            "onlineRate": round((online / total * 100) if total else 0, 2),
        },
        "records": [record.model_dump() for record in records],
        "regions": _list_regions(records),
        "devices": _list_devices(records),
        "updatedAt": _current_timestamp(),
    }


def _list_regions(records: list[DeviceStatusRecord]) -> list[str]:
    """从设备状态记录中生成区域筛选项。"""
    seen: set[str] = set()
    regions = [ALL_OPTION]
    for record in records:
        if record.region in seen:
            continue
        seen.add(record.region)
        regions.append(record.region)
    return regions


def _list_devices(records: list[DeviceStatusRecord], region: str = ALL_OPTION) -> list[str]:
    """从设备状态记录中生成设备类型筛选项。"""
    seen: set[str] = set()
    devices = [ALL_OPTION]
    for record in records:
        if region != ALL_OPTION and record.region != region:
            continue
        if record.device in seen:
            continue
        seen.add(record.device)
        devices.append(record.device)
    return devices


def _validate_device_status_filters(
    records: list[DeviceStatusRecord],
    *,
    region: str,
    device: str,
) -> None:
    """校验前端传入的区域和设备筛选值是否存在。"""
    valid_regions = _list_regions(records)
    if region not in valid_regions:
        raise HTTPException(status_code=400, detail=f"Unknown region: {region}")

    valid_devices = _list_devices(records, region)
    if device not in valid_devices:
        raise HTTPException(status_code=400, detail=f"Unknown device: {device}")


def _filter_device_status_records(
    records: list[DeviceStatusRecord],
    *,
    region: str,
    device: str,
) -> list[DeviceStatusRecord]:
    """按区域和设备类型过滤设备状态记录。"""
    return [
        record
        for record in records
        if (region == ALL_OPTION or record.region == region)
        and (device == ALL_OPTION or record.device == device)
    ]


async def _load_device_status_records(
    *,
    data_id: str | None,
    group: str,
    tenant: str | None,
    field: str | None,
) -> list[DeviceStatusRecord]:
    """加载设备状态记录；无 dataId 时返回模拟/兜底数据，有 dataId 时读取 Nacos。"""
    normalized_data_id = (data_id or "").strip()
    normalized_field = (field or "").strip()

    if not normalized_data_id:
        return _get_demo_device_status_records()

    content = await _get_single_config_content(normalized_data_id, group, tenant)
    parsed = _parse_content(content)
    if parsed is None:
        raise HTTPException(
            status_code=422,
            detail="device status config is not JSON/YAML and cannot be parsed.",
        )

    source_data = parsed
    if normalized_field:
        source_data, found = _extract_field(parsed, normalized_field)
        if not found:
            raise HTTPException(
                status_code=404,
                detail=f"Field '{normalized_field}' not found in config '{normalized_data_id}'.",
            )
    elif isinstance(parsed, dict) and "deviceStatus" in parsed:
        source_data = parsed.get("deviceStatus")

    return _coerce_device_status_records(source_data)


async def _load_nacos_snapshot_document() -> dict[str, Any]:
    """读取模拟器写入 Nacos 的硬件快照文档。"""
    if not DEVICE_STATUS_NACOS_DATA_ID:
        raise HTTPException(status_code=503, detail="DEVICE_STATUS_NACOS_DATA_ID is not configured.")

    content = await _get_single_config_content(
        DEVICE_STATUS_NACOS_DATA_ID,
        DEVICE_STATUS_NACOS_GROUP,
        DEVICE_STATUS_NACOS_TENANT,
    )
    parsed = _parse_content(content)
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=422,
            detail=f"Nacos config '{DEVICE_STATUS_NACOS_DATA_ID}' is not a JSON/YAML object.",
        )
    return parsed


def _coerce_hardware_snapshots(raw: Any) -> list[dict[str, Any]]:
    """从 Nacos 快照文档中提取硬件明细列表。"""
    candidate = raw
    if isinstance(candidate, dict):
        if isinstance(candidate.get("items"), list):
            candidate = candidate["items"]
        elif (
            isinstance(candidate.get("hardware"), dict)
            and isinstance(candidate["hardware"].get("items"), list)
        ):
            candidate = candidate["hardware"]["items"]

    if not isinstance(candidate, list):
        raise HTTPException(
            status_code=422,
            detail="Hardware snapshot must be an items array or an object containing hardware.items.",
        )
    return [item for item in candidate if isinstance(item, dict)]


def _fallback_dashboard_source() -> tuple[list[DeviceStatusRecord], list[dict[str, Any]], str]:
    """返回本地模拟/兜底大屏数据源。"""
    records = _get_local_device_status_records()
    snapshots = SIMULATOR.snapshot() if USE_STATE_MACHINE_SIMULATOR else []
    source = "simulator" if USE_STATE_MACHINE_SIMULATOR and DEVICE_STATUS_SOURCE != "demo" else "demo"
    return records, snapshots, source


async def _load_effective_dashboard_source() -> tuple[list[DeviceStatusRecord], list[dict[str, Any]], str]:
    """按配置加载大屏数据源；nacos 失败时可回退本地模拟器。"""
    if DEVICE_STATUS_SOURCE == "nacos":
        try:
            document = await _load_nacos_snapshot_document()
            records_source: Any = document
            if DEVICE_STATUS_NACOS_FIELD:
                records_source, found = _extract_field(document, DEVICE_STATUS_NACOS_FIELD)
                if not found:
                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Field '{DEVICE_STATUS_NACOS_FIELD}' not found in "
                            f"config '{DEVICE_STATUS_NACOS_DATA_ID}'."
                        ),
                    )
            records = _coerce_device_status_records(records_source)
            snapshots = _coerce_hardware_snapshots(document)
            return records, snapshots, "nacos"
        except HTTPException:
            if not NACOS_READ_FALLBACK_TO_SIMULATOR:
                raise

    return _fallback_dashboard_source()


async def _load_effective_device_status_records() -> list[DeviceStatusRecord]:
    """加载前端默认设备状态数据，部署时可默认从 Nacos 读取。"""
    records, _, _ = await _load_effective_dashboard_source()
    return records


def _device_is_abnormal(item: dict[str, Any]) -> bool:
    """判断硬件快照是否需要进入事件/风险列表。"""
    return (
        item.get("onlineStatus") not in {None, "online"}
        or item.get("alarmStatus") == "alarm"
        or item.get("workStatus") in {"alarm", "fault"}
    )


def _event_level(item: dict[str, Any]) -> str:
    """把设备状态映射成大屏事件等级。"""
    if item.get("alarmStatus") == "alarm" or item.get("onlineStatus") == "fault":
        return "critical"
    if item.get("onlineStatus") in {"offline", "maintenance"}:
        return "warning"
    return "info"


def _build_dashboard_events(
    records: list[DeviceStatusRecord],
    snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """生成右侧事件列表数据。"""
    events: list[dict[str, Any]] = []
    for item in snapshots:
        if not _device_is_abnormal(item):
            continue

        level = _event_level(item)
        event_type = "device_alarm" if level == "critical" else "device_status"
        occurred_at = str(item.get("lastChangedAt") or item.get("lastHeartbeatAt") or _current_timestamp())
        device_name = str(item.get("name") or item.get("deviceTypeName") or "未知设备")
        area_name = str(item.get("areaName") or "未知区域")
        events.append(
            {
                "id": f"{event_type}-{item.get('id', device_name)}-{item.get('sequence', 0)}",
                "eventType": event_type,
                "level": level,
                "title": f"{device_name}状态异常",
                "areaName": area_name,
                "deviceId": item.get("id"),
                "deviceName": device_name,
                "deviceType": item.get("deviceType"),
                "deviceTypeName": item.get("deviceTypeName"),
                "status": "active",
                "description": (
                    f"在线状态={item.get('onlineStatus')}, "
                    f"工作状态={item.get('workStatus')}, "
                    f"告警状态={item.get('alarmStatus')}"
                ),
                "occurredAt": occurred_at,
                "updatedAt": occurred_at,
            }
        )

    # 没有硬件明细时，根据聚合记录里的 offline 数量生成区域级事件，避免右侧面板空白。
    if not events:
        for index, record in enumerate(records):
            if record.offline <= 0:
                continue
            events.append(
                {
                    "id": f"device-offline-{index}",
                    "eventType": "device_status",
                    "level": "warning",
                    "title": f"{record.region}{record.device}存在离线设备",
                    "areaName": record.region,
                    "deviceName": record.device,
                    "deviceTypeName": record.device,
                    "status": "active",
                    "description": f"在线 {record.online} 台，离线/异常 {record.offline} 台",
                    "occurredAt": _current_timestamp(),
                    "updatedAt": _current_timestamp(),
                }
            )

    return sorted(events, key=lambda item: str(item.get("updatedAt", "")), reverse=True)


def _build_area_summaries(
    records: list[DeviceStatusRecord],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """生成中间区域态势数据。"""
    buckets: dict[str, dict[str, Any]] = {}
    for record in records:
        bucket = buckets.setdefault(
            record.region,
            {
                "id": f"area-{len(buckets) + 1:02d}",
                "name": record.region,
                "onlineDevices": 0,
                "offlineDevices": 0,
                "totalDevices": 0,
                "eventCount": 0,
                "riskLevel": "normal",
                "deviceTypes": [],
            },
        )
        bucket["onlineDevices"] += record.online
        bucket["offlineDevices"] += record.offline
        bucket["totalDevices"] += record.online + record.offline
        if record.device not in bucket["deviceTypes"]:
            bucket["deviceTypes"].append(record.device)

    event_count_by_area: dict[str, int] = {}
    critical_by_area: set[str] = set()
    for event in events:
        area_name = str(event.get("areaName") or "")
        if not area_name:
            continue
        event_count_by_area[area_name] = event_count_by_area.get(area_name, 0) + 1
        if event.get("level") == "critical":
            critical_by_area.add(area_name)

    for area_name, bucket in buckets.items():
        total = bucket["totalDevices"]
        online_rate = round((bucket["onlineDevices"] / total * 100) if total else 0, 2)
        bucket["onlineRate"] = online_rate
        bucket["eventCount"] = event_count_by_area.get(area_name, 0)
        if area_name in critical_by_area or online_rate < 80:
            bucket["riskLevel"] = "critical"
        elif bucket["eventCount"] > 0 or online_rate < 95:
            bucket["riskLevel"] = "warning"

    return sorted(buckets.values(), key=lambda item: item["id"])


def _build_risk_warnings(
    area_summaries: list[dict[str, Any]],
    rail_status: str,
) -> list[dict[str, Any]]:
    """生成右侧风险预警数据。"""
    warnings: list[dict[str, Any]] = []
    for area in area_summaries:
        if area["riskLevel"] == "normal":
            continue
        warnings.append(
            {
                "id": f"risk-{area['id']}",
                "level": area["riskLevel"],
                "title": f"{area['name']}设备在线率偏低",
                "areaName": area["name"],
                "metric": "onlineRate",
                "value": area["onlineRate"],
                "threshold": 95,
                "description": (
                    f"在线 {area['onlineDevices']} 台，"
                    f"离线/异常 {area['offlineDevices']} 台，"
                    f"在线率 {area['onlineRate']}%"
                ),
                "status": "active",
                "updatedAt": _current_timestamp(),
            }
        )

    if rail_status in {"blocked", "maintenance"}:
        warnings.insert(
            0,
            {
                "id": "risk-railway",
                "level": "critical" if rail_status == "blocked" else "warning",
                "title": "火车道联动状态需关注",
                "areaName": "火车道",
                "metric": "railStatus",
                "value": rail_status,
                "threshold": "idle",
                "description": f"当前火车道状态为 {rail_status}",
                "status": "active",
                "updatedAt": _current_timestamp(),
            },
        )

    return warnings[:12]


def _build_center_scene(area_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """生成中间主画面区域数据，前端可直接用于厂区平面图/态势图。"""
    positions = [
        (18, 24),
        (42, 18),
        (66, 24),
        (82, 45),
        (66, 68),
        (42, 74),
        (18, 66),
        (32, 46),
    ]
    nodes: list[dict[str, Any]] = []
    for index, area in enumerate(area_summaries):
        x, y = positions[index % len(positions)]
        nodes.append(
            {
                "id": area["id"],
                "name": area["name"],
                "x": x,
                "y": y,
                "status": area["riskLevel"],
                "onlineRate": area["onlineRate"],
                "totalDevices": area["totalDevices"],
                "eventCount": area["eventCount"],
            }
        )

    return {
        "sceneType": "factory-area-overview",
        "mapMode": "2d",
        "updatedAt": _current_timestamp(),
        "nodes": nodes,
        "links": [
            {"source": nodes[index]["id"], "target": nodes[index + 1]["id"], "status": "normal"}
            for index in range(max(0, len(nodes) - 1))
        ],
    }


def _resolve_subsystem_url(explicit_url: str, default_path: str) -> str | None:
    """Return configured subsystem URL without falling back to localhost."""
    if explicit_url:
        return explicit_url
    if SUBSYSTEM_BASE_URL:
        return f"{SUBSYSTEM_BASE_URL}/{default_path.strip('/')}/"
    return None


def _build_subsystems() -> list[dict[str, Any]]:
    """Build footer subsystem entries for the 8083 dashboard."""
    definitions = [
        {
            "id": "face",
            "name": "人脸识别",
            "key": "faceRecognition",
            "url": _resolve_subsystem_url(SUBSYSTEM_FACE_URL, "face"),
            "description": "人员进出、识别记录和门禁联动",
        },
        {
            "id": "vehicle",
            "name": "车辆管控",
            "key": "vehicleControl",
            "url": _resolve_subsystem_url(SUBSYSTEM_VEHICLE_URL, "vehicle"),
            "description": "车辆识别、道闸、场内车辆状态",
        },
        {
            "id": "rail",
            "name": "行车管控",
            "key": "railControl",
            "url": _resolve_subsystem_url(SUBSYSTEM_RAIL_URL, "rail"),
            "description": "铁路道口、行车状态和道闸安全联动",
        },
        {
            "id": "fire",
            "name": "火灾算法",
            "key": "fireAlgorithm",
            "url": _resolve_subsystem_url(SUBSYSTEM_FIRE_URL, "fire"),
            "description": "烟感温感、视频算法和火灾预警",
        },
    ]

    return [
        {
            **item,
            "enabled": bool(item["url"]),
        }
        for item in definitions
    ]


def _build_dashboard_payload(
    *,
    records: list[DeviceStatusRecord],
    snapshots: list[dict[str, Any]],
    source: str,
) -> dict[str, Any]:
    """聚合大屏首屏、右侧事件/风险、中间区域态势所需的完整数据。"""
    door_online = sum(
        1
        for item in snapshots
        if item.get("deviceType") == "door" and item.get("onlineStatus") == "online"
    )
    if not door_online:
        door_online = sum(record.online for record in records if "门" in record.device)

    vehicle_online = sum(record.online for record in records if "车辆" in record.device or "道闸" in record.device)
    rail_records = [record for record in records if "火车道" in record.region or "火车道" in record.device]
    rail_items = [item for item in snapshots if item.get("deviceType") == "rail"]
    if any(item.get("alarmStatus") == "alarm" for item in rail_items) or any(record.offline for record in rail_records):
        rail_status = "blocked"
    elif any(item.get("onlineStatus") != "online" for item in rail_items):
        rail_status = "maintenance"
    else:
        rail_status = "idle"

    events = _build_dashboard_events(records, snapshots)
    area_summaries = _build_area_summaries(records, events)
    risk_warnings = _build_risk_warnings(area_summaries, rail_status)
    device_status = _build_device_status_document(records)

    return {
        "onlineAccess": door_online,
        "areaTotal": sum(area["onlineDevices"] for area in area_summaries),
        "vehiclesOnSite": vehicle_online,
        "railStatus": rail_status,
        "deviceRecords": [record.model_dump() for record in records],
        "deviceRegions": _list_regions(records),
        "deviceTypes": _list_devices(records),
        "deviceStatus": device_status,
        "centerScene": _build_center_scene(area_summaries),
        "areas": area_summaries,
        "eventBoard": {
            "total": len(events),
            "unhandled": sum(1 for event in events if event.get("status") == "active"),
            "critical": sum(1 for event in events if event.get("level") == "critical"),
            "warning": sum(1 for event in events if event.get("level") == "warning"),
            "items": events[:6],
        },
        "eventList": events[:20],
        "riskWarnings": risk_warnings,
        "hardware": {
            "total": len(snapshots),
            "items": snapshots[:100],
        },
        "subsystems": _build_subsystems(),
        "dataSource": source,
        "nacos": {
            "enabled": DEVICE_STATUS_SOURCE == "nacos",
            "dataId": DEVICE_STATUS_NACOS_DATA_ID if DEVICE_STATUS_SOURCE == "nacos" else None,
            "group": DEVICE_STATUS_NACOS_GROUP if DEVICE_STATUS_SOURCE == "nacos" else None,
            "field": DEVICE_STATUS_NACOS_FIELD if DEVICE_STATUS_SOURCE == "nacos" else None,
        },
        "updatedAt": _current_timestamp(),
    }


def _current_timestamp() -> str:
    """返回上海时区 ISO 时间，用于接口 updatedAt 字段。"""
    return datetime.now(SHANGHAI_TZ).replace(microsecond=0).isoformat()


async def _get_access_token(client: httpx.AsyncClient) -> str | None:
    """按需登录 Nacos 并缓存 accessToken。"""
    global _cached_token, _token_expire_at

    if not NACOS_USERNAME or not NACOS_PASSWORD:
        return None

    now = asyncio.get_event_loop().time()
    if _cached_token and now < _token_expire_at:
        return _cached_token

    async with _auth_lock:
        now = asyncio.get_event_loop().time()
        if _cached_token and now < _token_expire_at:
            return _cached_token

        login_resp = await client.post(
            _join_url("/v1/auth/users/login"),
            data={"username": NACOS_USERNAME, "password": NACOS_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if login_resp.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Nacos auth failed: HTTP {login_resp.status_code} {login_resp.text}",
            )

        payload = login_resp.json()
        access_token = payload.get("accessToken")
        token_ttl = int(payload.get("tokenTtl", 18000))

        if not access_token:
            raise HTTPException(status_code=502, detail="Nacos auth failed: missing accessToken")

        _cached_token = access_token
        _token_expire_at = asyncio.get_event_loop().time() + max(token_ttl - 30, 60)
        return _cached_token


async def _nacos_request(
    method: str,
    path: str,
    *,
    query: dict[str, Any] | None = None,
    form: dict[str, Any] | None = None,
    include_nacos_auth: bool = False,
) -> httpx.Response:
    """统一封装 Nacos HTTP 请求，避免各接口重复处理鉴权和表单头。"""
    query = query or {}
    form = form or {}

    async with httpx.AsyncClient(timeout=20.0) as client:
        if include_nacos_auth:
            token = await _get_access_token(client)
            if token:
                query["accessToken"] = token

        headers: dict[str, str] = {}
        if form:
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            response = await client.request(
                method=method,
                url=_join_url(path),
                params=query,
                data=form if form else None,
                headers=headers,
            )
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Nacos request failed: {exc}") from exc
        return response


async def _get_single_config_content(data_id: str, group: str, tenant: str | None) -> str:
    """读取单个 Nacos 配置内容。"""
    if NACOS_API_VERSION == "v3":
        query: dict[str, Any] = {"dataId": data_id, "groupName": group}
        if tenant:
            query["namespaceId"] = tenant

        resp = await _nacos_request(
            "GET",
            "/v3/console/cs/config",
            query=query,
            include_nacos_auth=False,
        )
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Nacos read config failed: {resp.text}",
            )
        try:
            payload = resp.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Unexpected Nacos v3 response: {resp.text}") from exc
        if payload.get("code") != 0:
            raise HTTPException(status_code=502, detail=f"Nacos read config failed: {resp.text}")
        data = payload.get("data") or {}
        return str(data.get("content", ""))

    query: dict[str, Any] = {"dataId": data_id, "group": group}
    if tenant:
        query["tenant"] = tenant

    resp = await _nacos_request(
        "GET",
        "/v1/cs/configs",
        query=query,
        include_nacos_auth=False,
    )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Nacos read config failed: {resp.text}",
        )
    return resp.text


async def _publish_nacos_config(
    *,
    data_id: str,
    group: str,
    tenant: str | None,
    content: str,
    config_type: str = "json",
) -> None:
    """发布配置到 Nacos，兼容 Nacos 2.x v1 API 和 Nacos 3.x 控制台 API。"""
    if NACOS_API_VERSION == "v3":
        form: dict[str, Any] = {
            "dataId": data_id,
            "groupName": group,
            "content": content,
            "type": config_type,
        }
        if tenant:
            form["namespaceId"] = tenant
        resp = await _nacos_request(
            "POST",
            "/v3/console/cs/config",
            form=form,
            include_nacos_auth=True,
        )
    else:
        form = {
            "dataId": data_id,
            "group": group,
            "content": content,
            "type": config_type,
        }
        if tenant:
            form["tenant"] = tenant
        resp = await _nacos_request(
            "POST",
            "/v1/cs/configs",
            form=form,
            include_nacos_auth=True,
        )

    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Nacos publish config failed: {resp.text}",
        )

    if NACOS_API_VERSION == "v3":
        try:
            payload = resp.json()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Unexpected Nacos v3 response: {resp.text}") from exc
        success = payload.get("code") == 0 and payload.get("data") is True
    else:
        # Nacos 2.x / v1 API returns "true"; some compatibility layers return
        # HTTP 200 with an empty body after a successful publish.
        response_text = resp.text.strip().lower()
        success = response_text in {"", "true"}

    if not success:
        raise HTTPException(status_code=502, detail=f"Nacos publish failed: {resp.text}")


def _build_simulator_nacos_document() -> dict[str, Any]:
    """生成写入 Nacos 的模拟硬件快照文档。"""
    records = _get_local_device_status_records()
    items = SIMULATOR.snapshot() if USE_STATE_MACHINE_SIMULATOR else []
    updated_at = _current_timestamp()
    return {
        "schemaVersion": "factory.hardware.snapshot.v1",
        "source": "python-simulator",
        "tick": SIMULATOR.tick_no,
        "updatedAt": updated_at,
        "hardware": {
            "summary": SIMULATOR.summary() if USE_STATE_MACHINE_SIMULATOR else {},
            "items": items,
            "total": len(items),
        },
        "deviceStatus": _build_device_status_document(records),
    }


async def _sync_simulator_snapshot_to_nacos() -> dict[str, Any]:
    """把当前 Python 模拟设备快照写入 Nacos。"""
    document = _build_simulator_nacos_document()
    content = json.dumps(document, ensure_ascii=False, separators=(",", ":"))
    await _publish_nacos_config(
        data_id=SIMULATOR_NACOS_DATA_ID,
        group=SIMULATOR_NACOS_GROUP,
        tenant=SIMULATOR_NACOS_TENANT,
        content=content,
        config_type=SIMULATOR_NACOS_CONFIG_TYPE,
    )

    _simulator_nacos_sync_status.update(
        {
            "enabled": SIMULATOR_NACOS_SYNC_ENABLED,
            "dataId": SIMULATOR_NACOS_DATA_ID,
            "group": SIMULATOR_NACOS_GROUP,
            "tenant": SIMULATOR_NACOS_TENANT,
            "lastSuccessAt": _current_timestamp(),
            "lastError": None,
            "lastTick": SIMULATOR.tick_no,
        }
    )
    return {
        "dataId": SIMULATOR_NACOS_DATA_ID,
        "group": SIMULATOR_NACOS_GROUP,
        "tenant": SIMULATOR_NACOS_TENANT,
        "tick": SIMULATOR.tick_no,
        "updatedAt": document["updatedAt"],
        "bytes": len(content.encode("utf-8")),
    }


def _record_simulator_nacos_sync_error(exc: Exception) -> None:
    """记录模拟器同步 Nacos 的最近一次错误，不中断后台模拟器。"""
    detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
    _simulator_nacos_sync_status.update(
        {
            "enabled": SIMULATOR_NACOS_SYNC_ENABLED,
            "dataId": SIMULATOR_NACOS_DATA_ID,
            "group": SIMULATOR_NACOS_GROUP,
            "tenant": SIMULATOR_NACOS_TENANT,
            "lastErrorAt": _current_timestamp(),
            "lastError": detail,
            "lastTick": SIMULATOR.tick_no,
        }
    )


@app.get(
    "/api/health",
    tags=["system"],
    summary="Health check",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
    """健康检查接口，部署和负载均衡探活都调用这里。"""
    return HealthResponse(status="ok")


@app.get(
    "/api/nacos/config",
    tags=["nacos-config"],
    summary="Read Nacos config",
    description=(
        "If dataId is empty, return all config items in current group/tenant. "
        "If field is provided, parse content (json/yaml) and return field-level value."
    ),
    response_model=ConfigReadResponse,
)
async def get_config(
    data_id: str = Query("", alias="dataId"),
    group: str = Query("DEFAULT_GROUP"),
    tenant: str | None = Query(None),
    field: str | None = Query(None),
    page_no: int = Query(1, alias="pageNo", ge=1),
    page_size: int = Query(200, alias="pageSize", ge=1, le=1000),
) -> ConfigReadResponse:
    """读取 Nacos 配置。

    dataId 为空时读取配置列表；dataId 不为空时读取单个配置。
    field 参数用于在 JSON/YAML 配置里读取指定字段。
    """
    data_id = data_id.strip()

    if data_id:
        content = await _get_single_config_content(data_id, group, tenant)
        parsed = _parse_content(content)
        value: Any | None = None

        if field:
            if parsed is None:
                raise HTTPException(
                    status_code=422,
                    detail="field is provided but content is not JSON/YAML.",
                )
            value, found = _extract_field(parsed, field)
            if not found:
                raise HTTPException(
                    status_code=404,
                    detail=f"Field '{field}' not found in config '{data_id}'.",
                )

        return ConfigReadResponse(
            mode="single",
            dataId=data_id,
            group=group,
            tenant=tenant,
            field=field,
            content=content,
            parsed=parsed,
            value=value,
        )

    if NACOS_API_VERSION == "v3":
        list_query: dict[str, Any] = {
            "search": "blur",
            "dataId": "",
            "groupName": group,
            "pageNo": page_no,
            "pageSize": page_size,
        }
        if tenant:
            list_query["namespaceId"] = tenant
        resp = await _nacos_request(
            "GET",
            "/v3/console/cs/config/list",
            query=list_query,
            include_nacos_auth=False,
        )
    else:
        list_query = {
            "search": "blur",
            "dataId": "",
            "group": group,
            "pageNo": page_no,
            "pageSize": page_size,
        }
        if tenant:
            list_query["tenant"] = tenant
        resp = await _nacos_request(
            "GET",
            "/v1/cs/configs",
            query=list_query,
            include_nacos_auth=False,
        )
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Nacos list configs failed: {resp.text}",
        )

    try:
        payload = resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail=f"Unexpected list response: {resp.text}")

    list_payload = payload.get("data") if NACOS_API_VERSION == "v3" else payload
    if not isinstance(list_payload, dict):
        raise HTTPException(status_code=502, detail=f"Unexpected list response: {resp.text}")

    raw_items = list_payload.get("pageItems") or []
    items: list[ConfigItem] = []
    merged_params: dict[str, Any] = {}

    for raw_item in raw_items:
        item_data_id = str(raw_item.get("dataId", "")).strip()
        if not item_data_id:
            continue

        item_group = str(raw_item.get("groupName" if NACOS_API_VERSION == "v3" else "group", group))
        item_tenant = raw_item.get("namespaceId" if NACOS_API_VERSION == "v3" else "tenant")

        content = raw_item.get("content")
        if content is None:
            content = await _get_single_config_content(item_data_id, item_group, item_tenant)

        parsed = _parse_content(content)
        item_value: Any | None = None
        if field and parsed is not None:
            item_value, _ = _extract_field(parsed, field)

        if isinstance(parsed, dict):
            merged_params.update(parsed)

        items.append(
            ConfigItem(
                dataId=item_data_id,
                group=item_group,
                tenant=item_tenant,
                content=content,
                parsed=parsed,
                value=item_value,
            )
        )

    return ConfigReadResponse(
        mode="all",
        dataId=None,
        group=group,
        tenant=tenant,
        field=field,
        total=len(items),
        items=items,
        mergedParams=merged_params or None,
    )


@app.get(
    "/api/device-status/options",
    tags=["device-status"],
    summary="Get device status filter options",
    description="Return available regions and devices for the 8083 device-status widget.",
    response_model=DeviceStatusOptionsResponse,
)
async def get_device_status_options(
    region: str = Query(ALL_OPTION),
    region_id: str | None = Query(None, alias="regionId"),
) -> DeviceStatusOptionsResponse:
    """返回 8083 设备状态组件的筛选项。"""
    records = await _load_effective_device_status_records()
    effective_region = _normalize_selector(region_id or region)
    _validate_device_status_filters(records, region=effective_region, device=ALL_OPTION)

    return DeviceStatusOptionsResponse(
        regions=_list_regions(records),
        devices=_list_devices(records, effective_region),
    )


@app.get(
    "/api/device-status/records",
    tags=["device-status"],
    summary="Get device status records",
    description=(
        "Return records for the 8083 device-status widget. "
        "When dataId is empty, demo data is returned. "
        f"When dataId is provided, field defaults to {DEFAULT_DEVICE_STATUS_FIELD!r}."
    ),
    response_model=DeviceStatusRecordsResponse,
)
async def get_device_status_records(
    region: str = Query(ALL_OPTION),
    region_id: str | None = Query(None, alias="regionId"),
    device: str = Query(ALL_OPTION),
    device_type: str | None = Query(None, alias="deviceType"),
    data_id: str = Query("", alias="dataId"),
    group: str = Query("DEFAULT_GROUP"),
    tenant: str | None = Query(None),
    field: str | None = Query(DEFAULT_DEVICE_STATUS_FIELD),
) -> DeviceStatusRecordsResponse:
    """返回 8083 设备状态组件的表格记录。"""
    effective_region = _normalize_selector(region_id or region)
    effective_device = _normalize_selector(device_type or device)
    if data_id.strip():
        records = await _load_device_status_records(
            data_id=data_id,
            group=group,
            tenant=tenant,
            field=field,
        )
    else:
        records = await _load_effective_device_status_records()
    _validate_device_status_filters(records, region=effective_region, device=effective_device)

    return DeviceStatusRecordsResponse(
        records=_filter_device_status_records(
            records,
            region=effective_region,
            device=effective_device,
        ),
        updatedAt=_current_timestamp(),
    )


@app.get(
    "/api/device-status/summary",
    tags=["device-status"],
    summary="Get device status summary",
    description="Return device status totals and records for the 8083 dashboard.",
    response_model=DeviceStatusSummaryResponse,
)
async def get_device_status_summary(
    region: str = Query(ALL_OPTION),
    region_id: str | None = Query(None, alias="regionId"),
    device: str = Query(ALL_OPTION),
    device_type: str | None = Query(None, alias="deviceType"),
) -> DeviceStatusSummaryResponse:
    """返回设备状态汇总和过滤后的记录。"""
    effective_region = _normalize_selector(region_id or region)
    effective_device = _normalize_selector(device_type or device)
    records = await _load_effective_device_status_records()
    _validate_device_status_filters(records, region=effective_region, device=effective_device)
    filtered_records = _filter_device_status_records(
        records,
        region=effective_region,
        device=effective_device,
    )
    online = sum(record.online for record in filtered_records)
    offline = sum(record.offline for record in filtered_records)
    total = online + offline

    return DeviceStatusSummaryResponse(
        summary=DeviceStatusSummary(
            totalDevices=total,
            onlineDevices=online,
            offlineDevices=offline,
            onlineRate=round((online / total * 100) if total else 0, 2),
        ),
        records=filtered_records,
    )


@app.get(
    "/api/dashboard/overview",
    tags=["dashboard"],
    summary="Get dashboard overview",
    description="Return dashboard overview plus center scene, event board, event list, and risk warnings.",
    response_model=ApiResponse,
)
async def get_dashboard_overview() -> ApiResponse:
    """返回 8083 大屏首页聚合数据，兼容旧字段并补齐事件/风险/区域态势。"""
    records, snapshots, source = await _load_effective_dashboard_source()
    return ApiResponse(
        code=200,
        success=True,
        message="获取大屏概览数据成功",
        data=_build_dashboard_payload(records=records, snapshots=snapshots, source=source),
    )


@app.get(
    "/api/dashboard/aggregate",
    tags=["dashboard"],
    summary="Get full dashboard aggregate payload",
    description="Alias of /api/dashboard/overview for frontend teams that want an explicit aggregate endpoint.",
    response_model=ApiResponse,
)
async def get_dashboard_aggregate() -> ApiResponse:
    """显式大屏聚合接口，给后续前端改造使用。"""
    records, snapshots, source = await _load_effective_dashboard_source()
    return ApiResponse(
        code=200,
        success=True,
        message="获取大屏聚合数据成功",
        data=_build_dashboard_payload(records=records, snapshots=snapshots, source=source),
    )


@app.get(
    "/api/subsystems",
    tags=["dashboard"],
    summary="Get dashboard footer subsystem links",
    description="Return the four footer subsystem entries. URLs come from SUBSYSTEM_* env vars and never default to localhost.",
    response_model=ApiResponse,
)
async def get_subsystems() -> ApiResponse:
    """返回大屏底部四个子系统入口，避免前端写死 localhost 链接。"""
    items = _build_subsystems()
    return ApiResponse(
        code=200,
        success=True,
        message="获取子系统入口成功",
        data={
            "items": items,
            "total": len(items),
            "updatedAt": _current_timestamp(),
        },
    )


@app.get(
    "/api/simulator/summary",
    tags=["hardware-simulator"],
    summary="Get hardware simulator summary",
    response_model=ApiResponse,
)
async def get_simulator_summary() -> ApiResponse:
    """查询硬件状态机模拟器整体统计。"""
    return ApiResponse(
        data={
            **SIMULATOR.summary(),
            "nacosSync": _simulator_nacos_sync_status,
        }
    )


@app.get(
    "/api/simulator/devices",
    tags=["hardware-simulator"],
    summary="List simulated hardware devices",
    response_model=ApiResponse,
)
async def list_simulator_devices(
    area_id: str | None = Query(None, alias="areaId"),
    device_type: str | None = Query(None, alias="deviceType"),
    online_status: str | None = Query(None, alias="onlineStatus"),
) -> ApiResponse:
    """按区域、设备类型、在线状态查询模拟设备列表。"""
    items = SIMULATOR.snapshot(
        area_id=area_id,
        device_type=device_type,
        online_status=online_status,
    )
    return ApiResponse(
        data={
            "items": items,
            "total": len(items),
            "tick": SIMULATOR.tick_no,
            "updatedAt": _current_timestamp(),
        }
    )


@app.get(
    "/api/simulator/devices/{device_id}",
    tags=["hardware-simulator"],
    summary="Get simulated hardware device detail",
    response_model=ApiResponse,
)
async def get_simulator_device(device_id: str) -> ApiResponse:
    """查询单个模拟设备详情。"""
    device = SIMULATOR.get_device(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    return ApiResponse(data=device)


@app.post(
    "/api/simulator/tick",
    tags=["hardware-simulator"],
    summary="Advance simulator state",
    response_model=ApiResponse,
)
async def tick_simulator(
    steps: int = Query(1, ge=1, le=100),
    sync_nacos: bool = Query(False, alias="syncNacos"),
) -> ApiResponse:
    """手动推进模拟器状态，主要用于开发调试和演示。"""
    data: dict[str, Any] = {"tickResult": SIMULATOR.tick(steps=steps)}
    if sync_nacos:
        data["nacosSync"] = await _sync_simulator_snapshot_to_nacos()
    return ApiResponse(message="模拟器状态已推进", data=data)


@app.post(
    "/api/simulator/nacos-sync",
    tags=["hardware-simulator"],
    summary="Publish simulator snapshot to Nacos",
    response_model=ApiResponse,
)
async def sync_simulator_to_nacos(
    x_publish_key: str | None = Header(default=None, alias="X-Publish-Key"),
) -> ApiResponse:
    """手动把 Python 模拟设备快照写入 Nacos，必须携带 X-Publish-Key。"""
    _check_publish_key(x_publish_key)
    return ApiResponse(message="模拟器快照已写入 Nacos", data=await _sync_simulator_snapshot_to_nacos())


@app.post(
    "/api/simulator/devices/{device_id}/command",
    tags=["hardware-simulator"],
    summary="Send command to a simulated hardware device",
    response_model=ApiResponse,
)
async def command_simulator_device(
    device_id: str,
    body: HardwareCommandBody,
) -> ApiResponse:
    """向模拟设备下发命令，用于验证前端控制流程。"""
    result = SIMULATOR.apply_command(
        device_id,
        command=body.command,
        operator=body.operator,
        reason=body.reason,
        payload=body.payload,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Device not found: {device_id}")
    if not result.get("accepted"):
        raise HTTPException(status_code=400, detail=result.get("message", "Unsupported command"))
    return ApiResponse(message="模拟器命令已执行", data=result)


@app.post(
    "/api/nacos/config",
    tags=["nacos-config"],
    summary="Publish Nacos config",
    description="Publish config to Nacos. Requires header X-Publish-Key.",
    response_model=PublishConfigResponse,
)
async def publish_config(
    body: PublishConfigBody,
    x_publish_key: str | None = Header(default=None, alias="X-Publish-Key"),
) -> PublishConfigResponse:
    """发布配置到 Nacos，必须携带正确的 X-Publish-Key。"""
    _check_publish_key(x_publish_key)
    await _publish_nacos_config(
        data_id=body.data_id,
        group=body.group,
        tenant=body.tenant,
        content=body.content,
        config_type=body.config_type,
    )
    return PublishConfigResponse(success=True, message="Config published to Nacos")
