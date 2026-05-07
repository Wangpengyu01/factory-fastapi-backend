---
id: backend-full-landing-task-book
title: 后端全量 API 落地任务书
slug: /backend-full-landing-task-book
---

# 后端全量 API 落地任务书

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-BE-TASK-1.1` |
| 文档集 | `DOC-2026.05.07` |
| 适用系统版本 | `API-TARGET-1.0` |
| 当前状态 | 后端全量接口落地任务 |
| 更新日期 | `2026-05-07` |

整理日期：`2026-05-07`

本文档给后端开发同学执行。目标不是讨论方案，而是把当前 API 全部落到可运行的 FastAPI 服务里。

## 1. 最终交付目标

必须完成：

| 项 | 标准 |
|---|---|
| API 数量 | 对齐当前 OpenAPI，共 `71` 个操作 |
| 当前已落地 | `12` 个操作继续保留并完善 |
| 待补齐 | `59` 个操作全部实现 |
| Swagger | `http://localhost:8000/docs` 能看到全部接口 |
| OpenAPI | `backend/openapi.json` 导出后包含全部接口 |
| 数据返回 | 所有接口必须返回可用 JSON，不允许空壳 |
| 8083 前端 | `/api/dashboard/overview` 和 `/api/device-status/*` 保持可用 |
| 硬件状态 | 先走 Python 状态机模拟器，真实硬件后续替换 provider |
| 测试 | 每个模块至少有 curl 自测结果 |

## 2. 执行原则

后端同学按下面规则执行：

1. 不再新增临时 demo 地址。
2. 不写只有 `pass` 或空数组的假接口。
3. 没有真实数据源的接口，先接 `services/mock_store.py` 或 `hardware_state_machine.py`。
4. 每个接口必须有 Pydantic 请求/响应模型。
5. 每个接口必须在 Swagger 可见。
6. 每个接口必须有固定字段，不允许前端猜字段。
7. 做完一个模块就导出一次 OpenAPI。

## 3. 统一目录结构

把当前单文件后端拆成以下结构。

```text
backend/
  app/
    main.py
    config.py
    dependencies.py
    routers/
      system.py
      auth.py
      dashboard.py
      nacos_config.py
      simulator.py
      areas.py
      devices.py
      access.py
      vehicle.py
      railway.py
      alarms.py
      events.py
      alarm_devices.py
      video.py
      ai.py
      reports.py
      audit.py
      inspection.py
      measurements.py
    schemas/
      common.py
      system.py
      dashboard.py
      nacos_config.py
      simulator.py
      areas.py
      devices.py
      access.py
      vehicle.py
      railway.py
      alarms.py
      events.py
      alarm_devices.py
      video.py
      ai.py
      reports.py
      audit.py
      inspection.py
      measurements.py
    services/
      mock_store.py
      nacos_client.py
      hardware_state_machine.py
      dashboard_service.py
      area_service.py
      device_service.py
      access_service.py
      vehicle_service.py
      railway_service.py
      alarm_service.py
      event_service.py
      video_service.py
      ai_service.py
      report_service.py
      audit_service.py
      inspection_service.py
      measurement_service.py
    utils/
      response.py
      time.py
      pagination.py
  tests/
    test_system.py
    test_dashboard.py
    test_device_status.py
    test_simulator.py
    test_access.py
    test_vehicle.py
    test_railway.py
    test_alarms_events.py
    test_video_ai_reports.py
```

## 4. 通用模型必须先落地

文件：`backend/app/schemas/common.py`

必须实现：

```py
from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    success: bool = True
    message: str = "操作成功"
    data: T
    trace_id: str | None = Field(default=None, alias="traceId")

    model_config = {"populate_by_name": True}

class PageResult(BaseModel, Generic[T]):
    items: list[T]
    page: int = 1
    page_size: int = Field(20, alias="pageSize")
    total: int

    model_config = {"populate_by_name": True}

class OptionItem(BaseModel):
    id: str
    name: str
```

统一返回：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

例外：`/api/device-status/options`、`/api/device-status/summary`、`/api/device-status/records` 保持裸 JSON 兼容 8083。

## 5. 数据源必须先落地

文件：`backend/app/services/mock_store.py`

必须提供以下数据集合：

| 集合 | 用途 |
|---|---|
| `AREAS` | 区域列表 |
| `DEVICES` | 设备台账 |
| `ACCESS_DOORS` | 门禁 |
| `ACCESS_PASS_RECORDS` | 人员通行记录 |
| `VEHICLE_LANES` | 车道 |
| `VEHICLE_PASS_RECORDS` | 车辆通行记录 |
| `RAILWAY_LINKAGE_RECORDS` | 火车道联动记录 |
| `ALARMS` | 告警 |
| `EVENTS` | 事件 |
| `ALARM_DEVICES` | 报警设备 |
| `CAMERAS` | 摄像机 |
| `VIDEO_EVIDENCE` | 视频证据 |
| `VIDEO_RECORDINGS` | 录像 |
| `AI_RULES` | AI 规则 |
| `AI_DETECTIONS` | AI 检测 |
| `AUDIT_LOGS` | 审计日志 |
| `INSPECTION_TASKS` | 巡检任务 |
| `MEASUREMENT_POINTS` | 测点 |

要求：

1. 每个集合不少于 `20` 条，明显不适合 20 条的如区域不少于 `8` 条。
2. ID 固定，不要每次启动变化。
3. 时间字段使用 ISO 8601。
4. 分页接口必须真实分页。
5. 筛选参数必须真实生效。
6. 详情接口找不到返回 `404`。

## 6. 模块任务总表

| 任务编号 | 模块 | 文件 | 接口数量 | 完成状态 |
|---|---|---|---:|---|
| T00 | 基础结构 | `common/config/main` | - | 待做 |
| T01 | System/Auth | `system.py`、`auth.py` | 6 | 待做 |
| T02 | Dashboard | `dashboard.py` | 2 | 部分已做 |
| T03 | Device Status | `device_status.py` | 3 | 已做，需拆模块 |
| T04 | Simulator | `simulator.py` | 5 | 已做，需拆模块 |
| T05 | Nacos Config | `nacos_config.py` | 2 | 已做，需拆模块 |
| T06 | Areas/Devices | `areas.py`、`devices.py` | 6 | 待做 |
| T07 | Access | `access.py` | 4 | 待做 |
| T08 | Vehicle | `vehicle.py` | 3 | 待做 |
| T09 | Railway | `railway.py` | 3 | 待做 |
| T10 | Alarms/Events | `alarms.py`、`events.py`、`alarm_devices.py` | 11 | 待做 |
| T11 | Video | `video.py` | 6 | 待做 |
| T12 | AI | `ai.py` | 3 | 待做 |
| T13 | Reports/Audit | `reports.py`、`audit.py` | 6 | 待做 |
| T14 | Inspection/Measurements | `inspection.py`、`measurements.py` | 11 | 待做 |

## 7. T01 System/Auth

### 7.1 要建文件

```text
backend/app/routers/system.py
backend/app/routers/auth.py
backend/app/schemas/system.py
```

### 7.2 必须实现接口

| 方法 | 路径 | 返回 |
|---|---|---|
| `GET` | `/` | 根路径信息 |
| `GET` | `/api` | API 根信息 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/health` | 健康检查兼容 |
| `GET` | `/api/info` | 项目信息 |
| `GET` | `/api/test` | 测试连接 |
| `GET` | `/api/auth/me` | 当前用户 |

### 7.3 返回要求

`GET /api/info`：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "name": "成品库区域全封闭管控系统 API",
    "version": "v1",
    "description": "提供区域管控、门禁管理、车辆管理、火车道联动等功能"
  }
}
```

`GET /api/auth/me`：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "userId": "u_admin",
    "username": "admin",
    "displayName": "系统管理员",
    "roles": ["admin"],
    "permissions": ["dashboard:read", "device:read", "access:command"]
  }
}
```

### 7.4 验收

```bash
curl "http://localhost:8000/"
curl "http://localhost:8000/api"
curl "http://localhost:8000/health"
curl "http://localhost:8000/api/info"
curl "http://localhost:8000/api/auth/me"
```

## 8. T02 Dashboard

### 8.1 要建文件

```text
backend/app/routers/dashboard.py
backend/app/schemas/dashboard.py
backend/app/services/dashboard_service.py
```

### 8.2 必须实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/dashboard/overview` | 8083 大屏概览 |
| `GET` | `/api/overview` | 旧概览兼容，返回同类数据 |

### 8.3 数据来源

| 字段 | 来源 |
|---|---|
| `onlineAccess` | 状态机里 `door` 且 `onlineStatus=online` 数量 |
| `areaTotal` | mock_store 区域人员统计 |
| `vehiclesOnSite` | mock_store 车辆在场统计 |
| `railStatus` | 状态机里 `rail` 设备聚合 |
| `deviceRecords` | 状态机聚合 |
| `deviceRegions` | 状态机聚合 |
| `deviceTypes` | 状态机聚合 |

### 8.4 验收

```bash
curl "http://localhost:8000/api/dashboard/overview"
curl "http://localhost:8000/api/overview"
```

## 9. T03 Device Status

### 9.1 要建文件

```text
backend/app/routers/device_status.py
backend/app/schemas/device_status.py
backend/app/services/device_status_service.py
```

### 9.2 必须实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/device-status/options` | 区域和设备筛选项 |
| `GET` | `/api/device-status/summary` | 在线率汇总 |
| `GET` | `/api/device-status/records` | 设备在线离线记录 |

### 9.3 必须保留的返回结构

`/api/device-status/options`：

```json
{
  "regions": ["全部", "A区", "F区"],
  "devices": ["全部", "摄像机", "烟感器"]
}
```

`/api/device-status/summary`：

```json
{
  "summary": {
    "totalDevices": 143,
    "onlineDevices": 140,
    "offlineDevices": 3,
    "onlineRate": 97.9
  },
  "records": []
}
```

`/api/device-status/records`：

```json
{
  "records": [
    {
      "region": "A区",
      "device": "摄像机",
      "online": 8,
      "offline": 0
    }
  ],
  "updatedAt": "2026-05-07T10:00:00+08:00"
}
```

### 9.4 验收

```bash
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/summary?region=A区"
curl "http://localhost:8000/api/device-status/records?region=A区&device=摄像机"
```

## 10. T04 Hardware Simulator

### 10.1 要建文件

```text
backend/app/routers/simulator.py
backend/app/schemas/simulator.py
backend/app/services/hardware_state_machine.py
```

### 10.2 必须实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/simulator/summary` | 模拟器汇总 |
| `GET` | `/api/simulator/devices` | 模拟设备列表 |
| `GET` | `/api/simulator/devices/{device_id}` | 模拟设备详情 |
| `POST` | `/api/simulator/tick` | 手动推进状态 |
| `POST` | `/api/simulator/devices/{device_id}/command` | 下发模拟命令 |

### 10.3 必须支持的命令

| 命令 | 结果 |
|---|---|
| `recover` | 设备恢复在线 |
| `offline` | 设备离线 |
| `fault` | 设备故障 |
| `maintenance` | 设备维护 |
| `set_alarm` | 设备告警 |
| `clear_alarm` | 清除告警 |
| `open` | 打开 |
| `close` | 关闭 |
| `lock` | 锁定 |
| `unlock` | 解锁 |
| `reset` | 复位 |

### 10.4 验收

```bash
curl "http://localhost:8000/api/simulator/summary"
curl "http://localhost:8000/api/simulator/devices?areaId=r01"
curl -X POST "http://localhost:8000/api/simulator/tick?steps=10"
curl -X POST "http://localhost:8000/api/simulator/devices/door_r01_001/command" ^
  -H "Content-Type: application/json" ^
  -d "{\"command\":\"fault\",\"reason\":\"联调测试\",\"operator\":\"tester\",\"payload\":{}}"
```

## 11. T05 Nacos Config

### 11.1 要建文件

```text
backend/app/routers/nacos_config.py
backend/app/schemas/nacos_config.py
backend/app/services/nacos_client.py
```

### 11.2 必须实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/nacos/config` | 读取 Nacos 配置 |
| `POST` | `/api/nacos/config` | 发布 Nacos 配置 |

### 11.3 验收

```bash
curl "http://localhost:8000/api/nacos/config?dataId=device-status.json"
curl -X POST "http://localhost:8000/api/nacos/config" ^
  -H "Content-Type: application/json" ^
  -H "X-Publish-Key: change-this-to-a-strong-key" ^
  -d "{\"dataId\":\"device-status.json\",\"group\":\"DEFAULT_GROUP\",\"type\":\"json\",\"content\":\"{}\"}"
```

## 12. T06 Areas/Devices

### 12.1 要建文件

```text
backend/app/routers/areas.py
backend/app/routers/devices.py
backend/app/schemas/areas.py
backend/app/schemas/devices.py
backend/app/services/area_service.py
backend/app/services/device_service.py
```

### 12.2 必须实现接口

| 方法 | 路径 | 参数 | 返回 |
|---|---|---|---|
| `GET` | `/api/areas` | `includeDisabled` | `ApiResponse<Area[]>` |
| `GET` | `/api/area/{area_id}` | `area_id` | `ApiResponse<AreaDetail>` |
| `GET` | `/api/areas/{areaId}/summary` | `areaId` | `ApiResponse<AreaSummary>` |
| `GET` | `/api/devices` | 无 | 旧设备列表兼容 |
| `GET` | `/api/devices/list` | `areaId, deviceType, onlineStatus, keyword, page, pageSize` | `ApiResponse<PageResult<Device>>` |
| `GET` | `/api/devices/{deviceId}` | `deviceId` | `ApiResponse<DeviceDetail>` |

### 12.3 必须字段

`Area`：

```json
{
  "id": "r01",
  "name": "A区",
  "type": "production",
  "enabled": true,
  "sort": 1
}
```

`Device`：

```json
{
  "id": "camera_r01_001",
  "name": "A区摄像机1",
  "deviceType": "camera",
  "deviceTypeName": "摄像机",
  "areaId": "r01",
  "areaName": "A区",
  "onlineStatus": "online",
  "lastHeartbeatAt": "2026-05-07T10:00:00+08:00"
}
```

### 12.4 验收

```bash
curl "http://localhost:8000/api/areas"
curl "http://localhost:8000/api/area/r01"
curl "http://localhost:8000/api/areas/r01/summary"
curl "http://localhost:8000/api/devices/list?page=1&pageSize=20"
curl "http://localhost:8000/api/devices/camera_r01_001"
```

## 13. T07 Access

### 13.1 要建文件

```text
backend/app/routers/access.py
backend/app/schemas/access.py
backend/app/services/access_service.py
```

### 13.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/access/doors` | `areaId, status, onlineStatus, page, pageSize` | 门禁分页 |
| `GET` | `/api/access/doors/{doorId}` | `doorId` | 门禁详情 |
| `POST` | `/api/access/doors/{doorId}/command` | `DoorCommandRequest` | 命令结果 |
| `GET` | `/api/access/pass-records` | `areaId, doorId, personName, cardNo, result, startTime, endTime, page, pageSize` | 通行记录分页 |

### 13.3 Body

```json
{
  "command": "open",
  "reason": "现场授权放行",
  "durationSeconds": 30,
  "operator": "admin"
}
```

### 13.4 验收

```bash
curl "http://localhost:8000/api/access/doors?page=1&pageSize=20"
curl "http://localhost:8000/api/access/doors/door_r01_001"
curl -X POST "http://localhost:8000/api/access/doors/door_r01_001/command" ^
  -H "Content-Type: application/json" ^
  -d "{\"command\":\"open\",\"reason\":\"测试\",\"durationSeconds\":30,\"operator\":\"tester\"}"
curl "http://localhost:8000/api/access/pass-records?page=1&pageSize=20"
```

## 14. T08 Vehicle

### 14.1 要建文件

```text
backend/app/routers/vehicle.py
backend/app/schemas/vehicle.py
backend/app/services/vehicle_service.py
```

### 14.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/vehicle/lanes` | `areaId, onlineStatus, barrierStatus, page, pageSize` | 车道分页 |
| `POST` | `/api/vehicle/lanes/{laneId}/command` | `VehicleCommandRequest` | 命令结果 |
| `GET` | `/api/vehicle/pass-records` | `areaId, laneId, plateNo, direction, result, startTime, endTime, page, pageSize` | 车辆通行记录 |

### 14.3 Body

```json
{
  "command": "open",
  "reason": "车辆授权通行",
  "operator": "admin"
}
```

### 14.4 验收

```bash
curl "http://localhost:8000/api/vehicle/lanes?page=1&pageSize=20"
curl -X POST "http://localhost:8000/api/vehicle/lanes/lane_r01_001/command" ^
  -H "Content-Type: application/json" ^
  -d "{\"command\":\"open\",\"reason\":\"测试\",\"operator\":\"tester\"}"
curl "http://localhost:8000/api/vehicle/pass-records?page=1&pageSize=20"
```

## 15. T09 Railway

### 15.1 要建文件

```text
backend/app/routers/railway.py
backend/app/schemas/railway.py
backend/app/services/railway_service.py
```

### 15.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/railway/status` | 无 | 火车道状态 |
| `POST` | `/api/railway/mode` | `RailwayModeRequest` | 模式切换结果 |
| `GET` | `/api/railway/linkage-records` | `status, startTime, endTime, page, pageSize` | 联动记录 |

### 15.3 Body

```json
{
  "mode": "manual",
  "reason": "现场检修",
  "operator": "admin"
}
```

### 15.4 验收

```bash
curl "http://localhost:8000/api/railway/status"
curl -X POST "http://localhost:8000/api/railway/mode" ^
  -H "Content-Type: application/json" ^
  -d "{\"mode\":\"manual\",\"reason\":\"测试\",\"operator\":\"tester\"}"
curl "http://localhost:8000/api/railway/linkage-records?page=1&pageSize=20"
```

## 16. T10 Alarms/Events/Alarm Devices

### 16.1 要建文件

```text
backend/app/routers/alarms.py
backend/app/routers/events.py
backend/app/routers/alarm_devices.py
backend/app/schemas/alarms.py
backend/app/schemas/events.py
backend/app/schemas/alarm_devices.py
backend/app/services/alarm_service.py
backend/app/services/event_service.py
```

### 16.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/alarms` | `areaId, severity, status, alarmType, startTime, endTime, page, pageSize` | 告警分页 |
| `GET` | `/api/alarms/{alarmId}` | `alarmId` | 告警详情 |
| `POST` | `/api/alarms/{alarmId}/actions` | `AlarmActionRequest` | 动作结果 |
| `GET` | `/api/events` | `areaId, eventType, status, startTime, endTime, page, pageSize` | 事件分页 |
| `GET` | `/api/events/{eventId}` | `eventId` | 事件详情 |
| `PATCH` | `/api/events/{eventId}/close` | `EventCloseRequest` | 关闭结果 |
| `GET` | `/api/alarm-devices` | `areaId, onlineStatus` | 报警设备列表 |
| `POST` | `/api/alarm-devices/{deviceId}/command` | `deviceId` | 命令结果 |
| `GET` | `/api/alarm-devices/{deviceId}/records` | `deviceId, startTime, endTime` | 报警记录 |
| `GET` | `/api/alerts` | 无 | 旧告警兼容 |

### 16.3 Body

告警动作：

```json
{
  "action": "ack",
  "comment": "已确认",
  "operator": "admin"
}
```

关闭事件：

```json
{
  "result": "resolved",
  "comment": "现场已恢复",
  "operator": "admin"
}
```

### 16.4 验收

```bash
curl "http://localhost:8000/api/alarms?page=1&pageSize=20"
curl "http://localhost:8000/api/alarms/alarm_001"
curl -X POST "http://localhost:8000/api/alarms/alarm_001/actions" ^
  -H "Content-Type: application/json" ^
  -d "{\"action\":\"ack\",\"comment\":\"测试\",\"operator\":\"tester\"}"
curl "http://localhost:8000/api/events?page=1&pageSize=20"
curl -X PATCH "http://localhost:8000/api/events/event_001/close" ^
  -H "Content-Type: application/json" ^
  -d "{\"result\":\"resolved\",\"comment\":\"测试\",\"operator\":\"tester\"}"
curl "http://localhost:8000/api/alarm-devices"
```

## 17. T11 Video

### 17.1 要建文件

```text
backend/app/routers/video.py
backend/app/schemas/video.py
backend/app/services/video_service.py
```

### 17.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/video/cameras` | `areaId, onlineStatus, cameraType` | 摄像机列表 |
| `GET` | `/api/video/cameras/{cameraId}/stream-url` | `cameraId, protocol, expireSeconds` | 播放地址 |
| `GET` | `/api/video/recordings` | `cameraId, startTime, endTime` | 录像列表 |
| `GET` | `/api/video/evidence` | `alarmId, eventId, cameraId, page, pageSize` | 证据分页 |
| `GET` | `/api/video/evidence/{evidenceId}` | `evidenceId` | 证据详情 |
| `POST` | `/api/video/evidence/export` | 导出条件 | 导出任务 |

### 17.3 验收

```bash
curl "http://localhost:8000/api/video/cameras"
curl "http://localhost:8000/api/video/cameras/camera_r01_001/stream-url?protocol=hls"
curl "http://localhost:8000/api/video/recordings?cameraId=camera_r01_001&startTime=2026-05-07T00:00:00+08:00&endTime=2026-05-07T23:59:59+08:00"
curl "http://localhost:8000/api/video/evidence?page=1&pageSize=20"
curl "http://localhost:8000/api/video/evidence/evidence_001"
curl -X POST "http://localhost:8000/api/video/evidence/export"
```

## 18. T12 AI

### 18.1 要建文件

```text
backend/app/routers/ai.py
backend/app/schemas/ai.py
backend/app/services/ai_service.py
```

### 18.2 必须实现接口

| 方法 | 路径 | 参数 | 返回 |
|---|---|---|---|
| `GET` | `/api/ai/rules` | 无 | AI 规则 |
| `PATCH` | `/api/ai/rules/{ruleId}` | `enabled, threshold` | 更新规则 |
| `GET` | `/api/ai/detections` | `ruleId, minConfidence, startTime, endTime, page, pageSize` | 检测记录 |

### 18.3 验收

```bash
curl "http://localhost:8000/api/ai/rules"
curl -X PATCH "http://localhost:8000/api/ai/rules/rule_001?enabled=true&threshold=0.85"
curl "http://localhost:8000/api/ai/detections?page=1&pageSize=20"
```

## 19. T13 Reports/Audit

### 19.1 要建文件

```text
backend/app/routers/reports.py
backend/app/routers/audit.py
backend/app/schemas/reports.py
backend/app/schemas/audit.py
backend/app/services/report_service.py
backend/app/services/audit_service.py
```

### 19.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/reports/alarm-statistics` | `startTime, endTime, groupBy` | 告警统计 |
| `GET` | `/api/reports/device-status` | `startTime, endTime` | 设备状态报表 |
| `GET` | `/api/reports/pass-statistics` | `startTime, endTime` | 通行统计 |
| `GET` | `/api/reports/vehicle-statistics` | `startTime, endTime` | 车辆统计 |
| `POST` | `/api/reports/export` | 导出条件 | 导出任务 |
| `GET` | `/api/audit/logs` | `operator, action, targetType, targetId, startTime, endTime, page, pageSize` | 审计分页 |

### 19.3 验收

```bash
curl "http://localhost:8000/api/reports/alarm-statistics"
curl "http://localhost:8000/api/reports/device-status"
curl "http://localhost:8000/api/reports/pass-statistics"
curl "http://localhost:8000/api/reports/vehicle-statistics"
curl -X POST "http://localhost:8000/api/reports/export"
curl "http://localhost:8000/api/audit/logs?page=1&pageSize=20"
```

## 20. T14 Inspection/Measurements

### 20.1 要建文件

```text
backend/app/routers/inspection.py
backend/app/routers/measurements.py
backend/app/schemas/inspection.py
backend/app/schemas/measurements.py
backend/app/services/inspection_service.py
backend/app/services/measurement_service.py
```

### 20.2 必须实现接口

| 方法 | 路径 | 参数/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/tree-menu` | 无 | 测点树 |
| `GET` | `/api/latest-measurements` | `since` | 最新测量 |
| `GET` | `/api/point/{point_id}/latest-measurement` | `point_id` | 单点最新测量 |
| `GET` | `/api/point/{point_id}/history-measurements` | `point_id, days, start_date, end_date` | 历史测量 |
| `GET` | `/api/premade-point/{premade_point_id}/latest-image` | `premade_point_id` | 最新图片 |
| `GET` | `/api/v1/inspection/list` | `status, page, per_page, start_date, end_date` | 巡检任务分页 |
| `GET` | `/api/v1/inspection/tasks` | `status, page, per_page, start_date, end_date` | 巡检任务分页兼容 |
| `POST` | `/api/v1/inspection/create-task` | `CreateTaskRequest` | 创建任务 |
| `POST` | `/api/v1/inspection/start-task/{task_id}` | `task_id` | 启动任务 |
| `POST` | `/api/v1/inspection/cancel-task/{task_id}` | `task_id` | 取消任务 |
| `GET` | `/api/v1/inspection/task/{task_id}` | `task_id` | 任务详情 |
| `DELETE` | `/api/v1/inspection/tasks/{task_id}` | `task_id` | 删除任务 |

### 20.3 创建任务 Body

```json
{
  "task_name": "日常巡检任务",
  "detection_type": "opening",
  "selected_points": ["2-4-6"],
  "screw_alarm_threshold": 5.0,
  "opening_alarm_threshold": 135.0,
  "auto_start": false,
  "schedule_config": {},
  "metadata": {}
}
```

### 20.4 验收

```bash
curl "http://localhost:8000/api/tree-menu"
curl "http://localhost:8000/api/latest-measurements"
curl "http://localhost:8000/api/point/OP001/latest-measurement"
curl "http://localhost:8000/api/point/OP001/history-measurements?days=7"
curl "http://localhost:8000/api/premade-point/2-4-6/latest-image"
curl "http://localhost:8000/api/v1/inspection/list?page=1&per_page=20"
curl -X POST "http://localhost:8000/api/v1/inspection/create-task" ^
  -H "Content-Type: application/json" ^
  -d "{\"task_name\":\"日常巡检任务\",\"detection_type\":\"opening\",\"selected_points\":[\"2-4-6\"],\"auto_start\":false}"
```

## 21. 全量接口清单

### 21.1 基础

```text
GET    /
GET    /api
GET    /health
GET    /api/health
GET    /api/info
GET    /api/test
GET    /api/auth/me
```

### 21.2 大屏、设备、区域

```text
GET    /api/dashboard/overview
GET    /api/overview
GET    /api/areas
GET    /api/area/{area_id}
GET    /api/areas/{areaId}/summary
GET    /api/devices
GET    /api/devices/list
GET    /api/devices/{deviceId}
GET    /api/device-status/options
GET    /api/device-status/summary
GET    /api/device-status/records
```

### 21.3 Nacos 和模拟器

```text
GET    /api/nacos/config
POST   /api/nacos/config
GET    /api/simulator/summary
GET    /api/simulator/devices
GET    /api/simulator/devices/{device_id}
POST   /api/simulator/tick
POST   /api/simulator/devices/{device_id}/command
```

### 21.4 门禁、车辆、火车道

```text
GET    /api/access/doors
GET    /api/access/doors/{doorId}
POST   /api/access/doors/{doorId}/command
GET    /api/access/pass-records
GET    /api/vehicle/lanes
POST   /api/vehicle/lanes/{laneId}/command
GET    /api/vehicle/pass-records
GET    /api/railway/status
POST   /api/railway/mode
GET    /api/railway/linkage-records
```

### 21.5 告警、事件、报警设备

```text
GET    /api/alarms
GET    /api/alarms/{alarmId}
POST   /api/alarms/{alarmId}/actions
GET    /api/events
GET    /api/events/{eventId}
PATCH  /api/events/{eventId}/close
GET    /api/alarm-devices
POST   /api/alarm-devices/{deviceId}/command
GET    /api/alarm-devices/{deviceId}/records
GET    /api/alerts
```

### 21.6 视频、AI、报表、审计

```text
GET    /api/video/cameras
GET    /api/video/cameras/{cameraId}/stream-url
GET    /api/video/recordings
GET    /api/video/evidence
GET    /api/video/evidence/{evidenceId}
POST   /api/video/evidence/export
GET    /api/ai/rules
PATCH  /api/ai/rules/{ruleId}
GET    /api/ai/detections
GET    /api/reports/alarm-statistics
GET    /api/reports/device-status
GET    /api/reports/pass-statistics
GET    /api/reports/vehicle-statistics
POST   /api/reports/export
GET    /api/audit/logs
```

### 21.7 巡检、测量

```text
GET    /api/tree-menu
GET    /api/latest-measurements
GET    /api/point/{point_id}/latest-measurement
GET    /api/point/{point_id}/history-measurements
GET    /api/premade-point/{premade_point_id}/latest-image
GET    /api/v1/inspection/list
GET    /api/v1/inspection/tasks
POST   /api/v1/inspection/create-task
POST   /api/v1/inspection/start-task/{task_id}
POST   /api/v1/inspection/cancel-task/{task_id}
GET    /api/v1/inspection/task/{task_id}
DELETE /api/v1/inspection/tasks/{task_id}
```

## 22. 完成定义

每个任务完成必须满足：

1. 接口代码已写。
2. 请求模型已写。
3. 响应模型已写。
4. mock 数据可返回。
5. 筛选、分页、详情、404 生效。
6. 控制类接口能改变 mock_store 或状态机里的状态。
7. Swagger 可见。
8. curl 自测通过。
9. `python backend/scripts/generate_openapi.py` 已执行。
10. `backend/openapi.json` 已更新。

## 23. 最后总验收命令

全部模块做完后跑：

```bash
curl "http://localhost:8000/api/health"
curl "http://localhost:8000/api/info"
curl "http://localhost:8000/api/dashboard/overview"
curl "http://localhost:8000/api/device-status/records"
curl "http://localhost:8000/api/areas"
curl "http://localhost:8000/api/devices/list"
curl "http://localhost:8000/api/access/doors"
curl "http://localhost:8000/api/vehicle/lanes"
curl "http://localhost:8000/api/railway/status"
curl "http://localhost:8000/api/alarms"
curl "http://localhost:8000/api/events"
curl "http://localhost:8000/api/video/cameras"
curl "http://localhost:8000/api/ai/rules"
curl "http://localhost:8000/api/reports/alarm-statistics"
curl "http://localhost:8000/api/audit/logs"
curl "http://localhost:8000/api/tree-menu"
curl "http://localhost:8000/api/v1/inspection/list"
```

生成 OpenAPI：

```powershell
cd backend
python .\scripts\generate_openapi.py
```

检查 OpenAPI 操作数量：

```powershell
python - <<'PY'
import json
data=json.load(open("backend/openapi.json", encoding="utf-8"))
ops=0
for item in data["paths"].values():
    ops += sum(1 for m in ["get","post","put","patch","delete"] if m in item)
print(ops)
PY
```

输出必须不少于：

```text
71
```
