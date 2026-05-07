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
    yaml = None

load_dotenv()

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

NACOS_BASE_URL = os.getenv("NACOS_BASE_URL", "http://127.0.0.1:8848/nacos").rstrip("/")
NACOS_USERNAME = os.getenv("NACOS_USERNAME", "").strip()
NACOS_PASSWORD = os.getenv("NACOS_PASSWORD", "").strip()
PUBLISH_API_KEY = os.getenv("PUBLISH_API_KEY", "").strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


USE_STATE_MACHINE_SIMULATOR = _env_bool("USE_STATE_MACHINE_SIMULATOR", True)
SIMULATOR_AUTO_TICK = _env_bool("SIMULATOR_AUTO_TICK", True)
SIMULATOR_TICK_SECONDS = max(1.0, float(os.getenv("SIMULATOR_TICK_SECONDS", "5")))

_cached_token: str | None = None
_token_expire_at = 0.0
_auth_lock = asyncio.Lock()
_simulator_task: asyncio.Task[None] | None = None


class PublishConfigBody(BaseModel):
    data_id: str = Field(..., alias="dataId", min_length=1)
    group: str = Field(default="DEFAULT_GROUP")
    tenant: str | None = None
    content: str = Field(..., min_length=1)
    config_type: str = Field(default="text", alias="type")

    model_config = {"populate_by_name": True}


class HealthResponse(BaseModel):
    status: str


class ConfigItem(BaseModel):
    data_id: str = Field(..., alias="dataId")
    group: str
    tenant: str | None = None
    content: str
    parsed: Any | None = None
    value: Any | None = None

    model_config = {"populate_by_name": True}


class ConfigReadResponse(BaseModel):
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
    success: bool
    message: str


class DeviceStatusRecord(BaseModel):
    region: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    online: int = Field(..., ge=0)
    offline: int = Field(..., ge=0)


class DeviceStatusOptionsResponse(BaseModel):
    regions: list[str]
    devices: list[str]


class DeviceStatusRecordsResponse(BaseModel):
    records: list[DeviceStatusRecord]
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


class DeviceStatusSummary(BaseModel):
    total_devices: int = Field(..., alias="totalDevices")
    online_devices: int = Field(..., alias="onlineDevices")
    offline_devices: int = Field(..., alias="offlineDevices")
    online_rate: float = Field(..., alias="onlineRate")

    model_config = {"populate_by_name": True}


class DeviceStatusSummaryResponse(BaseModel):
    summary: DeviceStatusSummary
    records: list[DeviceStatusRecord]


class ApiResponse(BaseModel):
    code: int = 200
    success: bool = True
    message: str = "操作成功"
    data: Any


class HardwareCommandBody(BaseModel):
    command: str = Field(..., min_length=1)
    reason: str = ""
    operator: str = "simulator"
    payload: dict[str, Any] = Field(default_factory=dict)


ALL_OPTION = "全部"
DEFAULT_DEVICE_STATUS_FIELD = "deviceStatus.records"
SHANGHAI_TZ = timezone(timedelta(hours=8))
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
    while True:
        SIMULATOR.tick()
        await asyncio.sleep(SIMULATOR_TICK_SECONDS)


@app.on_event("startup")
async def _start_simulator_loop() -> None:
    global _simulator_task
    if USE_STATE_MACHINE_SIMULATOR and SIMULATOR_AUTO_TICK and _simulator_task is None:
        _simulator_task = asyncio.create_task(_run_simulator_loop())


@app.on_event("shutdown")
async def _stop_simulator_loop() -> None:
    global _simulator_task
    if _simulator_task is not None:
        _simulator_task.cancel()
        _simulator_task = None


def _join_url(path: str) -> str:
    return f"{NACOS_BASE_URL}{path}"


def _parse_content(content: str) -> Any | None:
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
    if not PUBLISH_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Publish API key is not configured on server.",
        )
    if not x_publish_key or not secrets.compare_digest(x_publish_key, PUBLISH_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid X-Publish-Key.")


def _normalize_selector(value: str | None, *, default: str = ALL_OPTION) -> str:
    normalized = (value or "").strip()
    return normalized or default


def _coerce_non_negative_int(value: Any, *, field_name: str, index: int) -> int:
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


def _get_demo_device_status_records() -> list[DeviceStatusRecord]:
    if USE_STATE_MACHINE_SIMULATOR:
        return [
            DeviceStatusRecord(**item)
            for item in SIMULATOR.aggregate_device_status_records()
        ]
    return [DeviceStatusRecord(**item) for item in DEMO_DEVICE_STATUS_RECORDS]


def _list_regions(records: list[DeviceStatusRecord]) -> list[str]:
    seen: set[str] = set()
    regions = [ALL_OPTION]
    for record in records:
        if record.region in seen:
            continue
        seen.add(record.region)
        regions.append(record.region)
    return regions


def _list_devices(records: list[DeviceStatusRecord], region: str = ALL_OPTION) -> list[str]:
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


def _current_timestamp() -> str:
    return datetime.now(SHANGHAI_TZ).replace(microsecond=0).isoformat()


async def _get_access_token(client: httpx.AsyncClient) -> str | None:
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

        response = await client.request(
            method=method,
            url=_join_url(path),
            params=query,
            data=form if form else None,
            headers=headers,
        )
        return response


async def _get_single_config_content(data_id: str, group: str, tenant: str | None) -> str:
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


@app.get(
    "/api/health",
    tags=["system"],
    summary="Health check",
    response_model=HealthResponse,
)
async def health() -> HealthResponse:
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

    list_query: dict[str, Any] = {
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

    raw_items = payload.get("pageItems") or []
    items: list[ConfigItem] = []
    merged_params: dict[str, Any] = {}

    for raw_item in raw_items:
        item_data_id = str(raw_item.get("dataId", "")).strip()
        if not item_data_id:
            continue

        item_group = str(raw_item.get("group", group))
        item_tenant = raw_item.get("tenant")

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
    records = _get_demo_device_status_records()
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
    effective_region = _normalize_selector(region_id or region)
    effective_device = _normalize_selector(device_type or device)
    records = await _load_device_status_records(
        data_id=data_id,
        group=group,
        tenant=tenant,
        field=field,
    )
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
    effective_region = _normalize_selector(region_id or region)
    effective_device = _normalize_selector(device_type or device)
    records = _get_demo_device_status_records()
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
    description="Return the minimum overview payload required by the retained 8083 frontend.",
    response_model=ApiResponse,
)
async def get_dashboard_overview() -> ApiResponse:
    records = _get_demo_device_status_records()
    snapshots = SIMULATOR.snapshot() if USE_STATE_MACHINE_SIMULATOR else []
    online_access = sum(
        1
        for item in snapshots
        if item.get("deviceType") == "door" and item.get("onlineStatus") == "online"
    )
    rail_items = [item for item in snapshots if item.get("deviceType") == "rail"]
    if any(item.get("alarmStatus") == "alarm" for item in rail_items):
        rail_status = "blocked"
    elif any(item.get("onlineStatus") != "online" for item in rail_items):
        rail_status = "maintenance"
    else:
        rail_status = "idle"

    device_regions = _list_regions(records)
    device_types = _list_devices(records)
    tick = SIMULATOR.tick_no if USE_STATE_MACHINE_SIMULATOR else 0

    return ApiResponse(
        code=200,
        success=True,
        message="获取大屏概览数据成功",
        data={
            "onlineAccess": online_access or 19,
            "areaTotal": 139 + (tick % 17),
            "vehiclesOnSite": 22 + (tick % 9),
            "railStatus": rail_status,
            "deviceRecords": [record.model_dump() for record in records],
            "deviceRegions": device_regions,
            "deviceTypes": device_types,
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
    return ApiResponse(data=SIMULATOR.summary())


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
) -> ApiResponse:
    return ApiResponse(message="模拟器状态已推进", data=SIMULATOR.tick(steps=steps))


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
    _check_publish_key(x_publish_key)

    form: dict[str, Any] = {
        "dataId": body.data_id,
        "group": body.group,
        "content": body.content,
        "type": body.config_type,
    }
    if body.tenant:
        form["tenant"] = body.tenant

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

    success = resp.text.strip().lower() == "true"
    if not success:
        raise HTTPException(status_code=502, detail=f"Nacos publish failed: {resp.text}")

    return PublishConfigResponse(success=True, message="Config published to Nacos")
