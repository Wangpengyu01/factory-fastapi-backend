---
id: hardware-state-machine-simulator
title: 硬件状态机与硬件接入落地文档
slug: /hardware-state-machine-simulator
---

# 硬件状态机与硬件接入落地文档

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-SIM-1.2` |
| 文档集 | `DOC-2026.05.07` |
| 当前代码版本 | `SIM-0.1` |
| 本轮落地目标 | `SIM-0.2` |
| 适用系统版本 | `API-CURRENT-0.1` + `API-TARGET-1.0` |
| 当前状态 | 模拟器已可运行，真实硬件接入按本文档落地 |
| 更新日期 | `2026-05-07` |

本文档给后端开发、硬件对接开发、前端联调人员执行使用。当前阶段先用 Python 状态机模拟所有硬件状态，真实硬件接入时只替换数据来源，不改 `8083` 前端页面调用方式。

## 0. 结论

| 问题 | 结论 |
|---|---|
| 硬件状态怎么抽象 | 所有硬件统一抽象成 `HardwareDevice` 状态机 |
| 前端怎么读 | 前端只读 `/api/...`，不直接连硬件、不直接连 Nacos |
| 后端怎么接 | FastAPI 读取统一状态源，当前是内存模拟器，后续换成真实硬件 provider |
| 硬件同学交付什么 | 交付状态上报、事件上报、命令执行回执，字段按本文档 JSON |
| 开发语言 | Python 优先，性能不是第一优先级，先保证联调速度 |
| 当前可用接口 | `/api/simulator/*`、`/api/device-status/*`、`/api/dashboard/overview` |
| 本轮新增目标 | `POST /api/hardware/ingest/status`、`POST /api/hardware/ingest/event`、`POST /api/hardware/command-results` |

## 1. 版本区分

| 版本 | 状态 | 内容 |
|---|---|---|
| `SIM-0.1` | 已落地 | 内存状态机、随机 tick、模拟器查询、模拟命令、8083 设备状态聚合 |
| `SIM-0.2` | 本轮落地 | 真实硬件状态上报入口、命令回执入口、状态快照存储、硬件 provider 拆分 |
| `SIM-1.0` | 后续正式版 | 接真实硬件协议、持久化、权限、审计、命令队列、断线检测、告警事件闭环 |

`SIM-0.1` 继续保留，用于没有真实硬件时联调。`SIM-0.2` 开始接真实硬件或硬件对接程序。

## 2. 当前已落地能力

当前代码已经具备：

| 能力 | 状态 | 文件 |
|---|---|---|
| Python 状态机 | 已落地 | `backend/app/hardware_state_machine.py` |
| 模拟器自动 tick | 已落地 | `backend/app/main.py` startup task |
| 模拟器查询接口 | 已落地 | `GET /api/simulator/summary`、`GET /api/simulator/devices` |
| 模拟设备详情 | 已落地 | `GET /api/simulator/devices/{device_id}` |
| 模拟器手动推进 | 已落地 | `POST /api/simulator/tick` |
| 模拟命令 | 已落地 | `POST /api/simulator/devices/{device_id}/command` |
| 8083 设备状态聚合 | 已落地 | `GET /api/device-status/summary`、`GET /api/device-status/records` |
| Dashboard 聚合 | 已落地 | `GET /api/dashboard/overview` |

当前环境变量：

```env
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
```

## 3. 本轮落地目标

本轮硬件落地不是继续只写模拟器，而是把“模拟器”和“真实硬件”都接到同一个状态源。

| 编号 | 目标 | 验收 |
|---|---|---|
| HW-D01 | 拆出硬件 provider 接口 | 业务 service 不直接依赖模拟器类 |
| HW-D02 | 支持真实硬件状态上报 | 硬件对接程序能 `POST` 状态到后端 |
| HW-D03 | 支持硬件事件上报 | 告警、通行、开门、道闸动作能上报 |
| HW-D04 | 支持命令回执 | 开门、关门、复位等命令有执行结果 |
| HW-D05 | 支持离线判断 | 超过心跳阈值自动标记 `offline` |
| HW-D06 | 支持状态快照存储 | 当前状态可重启恢复，不只存在内存 |
| HW-D07 | 保持 8083 兼容 | `/api/device-status/*` 返回结构不破坏 |
| HW-D08 | 保留模拟模式 | 没有硬件时仍可用模拟器联调 |

## 4. 总体架构

### 4.1 当前 `SIM-0.1`

```text
8083 Vue + Vite 前端
  -> /api/dashboard/overview
  -> /api/device-status/summary
  -> /api/device-status/records
    -> FastAPI
      -> HardwareStateMachineSimulator
        -> 内存设备状态
```

### 4.2 本轮 `SIM-0.2`

```text
真实硬件 / 硬件对接程序
  -> POST /api/hardware/ingest/status
  -> POST /api/hardware/ingest/event
  -> POST /api/hardware/command-results
    -> FastAPI
      -> HardwareProvider
        -> RealtimeStateStore
          -> 数据库 / Redis / 内存 fallback
            -> /api/device-status/*
            -> /api/dashboard/overview
            -> 8083 前端
```

命令下发链路：

```text
8083 前端
  -> FastAPI command 接口
    -> hardware_commands
      -> HardwareCommandDispatcher
        -> 硬件对接程序 / 厂商 SDK / HTTP / MQTT
          -> 真实硬件
            -> POST /api/hardware/command-results
```

## 5. 设备统一模型

所有硬件统一成 `HardwareDevice`。前端、报表、告警、Dashboard 都只认这套字段。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `deviceId` | `string` | 是 | 系统内唯一设备 ID |
| `vendorDeviceId` | `string` | 否 | 厂商设备 ID |
| `name` | `string` | 是 | 设备名称 |
| `areaId` | `string` | 是 | 区域 ID |
| `areaName` | `string` | 是 | 区域名称 |
| `deviceType` | `string` | 是 | 设备类型 |
| `deviceTypeName` | `string` | 是 | 设备类型中文名 |
| `onlineStatus` | `string` | 是 | 在线状态 |
| `workStatus` | `string` | 是 | 工作状态 |
| `alarmStatus` | `string` | 是 | 告警状态 |
| `value` | `number/null` | 否 | 传感器数值 |
| `unit` | `string/null` | 否 | 单位 |
| `battery` | `number/null` | 否 | 电量 |
| `signal` | `number/null` | 否 | 信号强度 |
| `sequence` | `number` | 是 | 状态序号，递增 |
| `lastHeartbeatAt` | `string` | 是 | 最后心跳时间 |
| `lastChangedAt` | `string` | 是 | 最后状态变化时间 |
| `rawStatus` | `object` | 否 | 厂商原始状态 |
| `metadata` | `object` | 否 | 扩展字段 |

时间统一使用 ISO 字符串，例如：`2026-05-07T11:30:00+08:00`。

## 6. 状态枚举

### 6.1 在线状态 `onlineStatus`

| 值 | 中文 | 触发条件 |
|---|---|---|
| `online` | 在线 | 正常心跳或正常状态上报 |
| `offline` | 离线 | 超过心跳阈值未上报 |
| `fault` | 故障 | 硬件故障、通信异常、设备自检失败 |
| `maintenance` | 维护中 | 人工切维护或设备检修 |

### 6.2 工作状态 `workStatus`

| 值 | 中文 | 适用设备 |
|---|---|---|
| `normal` | 正常 | 通用 |
| `open` | 打开 | 门禁、道闸、铁路联动门 |
| `closed` | 关闭 | 门禁、道闸、铁路联动门 |
| `locked` | 锁定 | 联锁门、门禁 |
| `alarm` | 告警态 | 报警器、传感器 |
| `warning` | 预警态 | 传感器、报警器 |
| `fault` | 故障态 | 通用 |
| `offline` | 离线态 | 通用 |
| `maintenance` | 维护态 | 通用 |

### 6.3 告警状态 `alarmStatus`

| 值 | 中文 | 说明 |
|---|---|---|
| `normal` | 无告警 | 当前无告警 |
| `warning` | 预警 | 未达到严重告警 |
| `alarm` | 告警 | 需要处置 |

## 7. 设备类型

| 类型 | 中文名 | 当前模拟 | 真实接入方式 |
|---|---|---|---|
| `door` | 人员智能门/联锁门 | 已模拟 | 门禁控制器 SDK、HTTP、串口网关 |
| `vehicle` | 车辆识别与道闸 | 已模拟 | 车牌识别平台、道闸控制器 HTTP/SDK |
| `rail` | 火车道联动门 | 已模拟 | PLC、IO 控制器、HTTP 网关 |
| `camera` | 摄像机 | 已模拟 | 视频平台、NVR、摄像机 SDK |
| `acoustic` | 声光报警 | 已模拟 | IO 控制器、报警主机 |
| `photoelectric` | 光电报警 | 已模拟 | 报警主机、IO 控制器 |
| `smoke` | 烟感器 | 已模拟 | 消防平台、传感器网关 |
| `temperature` | 温感器 | 已模拟 | 传感器网关、Modbus、MQTT |
| `nvr` | NVR | 已模拟 | 视频平台/NVR SDK |
| `ai` | AI 分析服务器 | 已模拟 | AI 平台 HTTP API |

设备 ID 规则：

```text
{deviceType}_{areaId}_{三位序号}
```

示例：

```text
door_r01_001
vehicle_r06_003
smoke_r07_008
camera_r04_002
```

真实硬件已有厂商 ID 时，保留 `vendorDeviceId`，系统内部仍生成 `deviceId`。

## 8. 硬件状态上报接口

### 8.1 状态上报

本轮新增：

```http
POST /api/hardware/ingest/status
```

Header：

```http
X-Hardware-Token: <后端分配的 token>
Content-Type: application/json
```

Body：

```json
{
  "source": "door-adapter-01",
  "reportedAt": "2026-05-07T11:30:00+08:00",
  "items": [
    {
      "deviceId": "door_r01_001",
      "vendorDeviceId": "D-0001",
      "name": "A区人员智能门1",
      "areaId": "r01",
      "areaName": "A区",
      "deviceType": "door",
      "deviceTypeName": "人员智能门/联锁门",
      "onlineStatus": "online",
      "workStatus": "closed",
      "alarmStatus": "normal",
      "value": null,
      "unit": null,
      "battery": 95,
      "signal": 88,
      "sequence": 1024,
      "lastHeartbeatAt": "2026-05-07T11:30:00+08:00",
      "lastChangedAt": "2026-05-07T11:29:40+08:00",
      "rawStatus": {
        "doorContact": 0,
        "lock": 1
      },
      "metadata": {
        "ip": "192.168.1.10",
        "gateway": "gw-r01"
      }
    }
  ]
}
```

Response：

```json
{
  "code": 200,
  "success": true,
  "message": "状态已接收",
  "data": {
    "accepted": 1,
    "rejected": 0,
    "updatedAt": "2026-05-07T11:30:01+08:00"
  }
}
```

### 8.2 事件上报

本轮新增：

```http
POST /api/hardware/ingest/event
```

Body：

```json
{
  "source": "alarm-adapter-01",
  "eventId": "evt_20260507113000001",
  "deviceId": "smoke_r07_001",
  "eventType": "alarm",
  "eventLevel": "critical",
  "eventTime": "2026-05-07T11:30:00+08:00",
  "title": "烟感浓度超限",
  "description": "烟感器 ppm 超过阈值",
  "value": 720,
  "unit": "ppm",
  "rawPayload": {
    "channel": 1,
    "code": "SMOKE_HIGH"
  }
}
```

事件类型：

| `eventType` | 说明 |
|---|---|
| `heartbeat` | 心跳 |
| `status_change` | 状态变化 |
| `alarm` | 告警 |
| `fault` | 故障 |
| `command_result` | 命令回执 |
| `pass_record` | 通行记录 |
| `video_event` | 视频事件 |

事件等级：

| `eventLevel` | 说明 |
|---|---|
| `info` | 普通信息 |
| `warning` | 预警 |
| `critical` | 严重 |

### 8.3 命令回执

本轮新增：

```http
POST /api/hardware/command-results
```

Body：

```json
{
  "commandId": "cmd_20260507113000001",
  "deviceId": "door_r01_001",
  "command": "open",
  "status": "success",
  "message": "开门成功",
  "startedAt": "2026-05-07T11:30:00+08:00",
  "finishedAt": "2026-05-07T11:30:02+08:00",
  "rawResult": {
    "vendorCode": 0
  }
}
```

命令执行状态：

| `status` | 说明 |
|---|---|
| `pending` | 等待执行 |
| `running` | 执行中 |
| `success` | 成功 |
| `failed` | 失败 |
| `timeout` | 超时 |

## 9. 控制命令

当前模拟器支持：

| 命令 | 说明 | 适用设备 |
|---|---|---|
| `recover` | 恢复在线正常 | 通用 |
| `offline` | 强制离线 | 通用 |
| `fault` | 强制故障 | 通用 |
| `maintenance` | 强制维护 | 通用 |
| `set_alarm` | 强制告警 | 报警器、传感器 |
| `clear_alarm` | 清除告警 | 报警器、传感器 |
| `open` | 打开 | 门禁、道闸、铁路联动门 |
| `close` | 关闭 | 门禁、道闸、铁路联动门 |
| `lock` | 锁定 | 联锁门 |
| `unlock` | 解锁 | 联锁门 |
| `reset` | 复位 | 通用 |

真实硬件命令目标接口按模块复用：

| 模块 | 接口 |
|---|---|
| 门禁 | `POST /api/access/doors/{doorId}/command` |
| 车辆道闸 | `POST /api/vehicle/lanes/{laneId}/command` |
| 报警设备 | `POST /api/alarm-devices/{deviceId}/command` |
| 铁路联动 | `POST /api/railway/mode` |
| 模拟器 | `POST /api/simulator/devices/{device_id}/command` |

命令接口返回后只代表“后端已接收或已下发”，最终成功失败以 `/api/hardware/command-results` 回执为准。

## 10. 后端文件落地

本轮建议按以下文件拆分，避免把所有逻辑继续放在 `main.py`。

```text
backend/app/
  hardware/
    __init__.py
    schemas.py
    enums.py
    provider_base.py
    simulator_provider.py
    realtime_store.py
    command_dispatcher.py
    ingest_service.py
    offline_detector.py
  routers/
    hardware_ingest.py
    simulator.py
  services/
    device_status_service.py
```

文件职责：

| 文件 | 职责 |
|---|---|
| `hardware/schemas.py` | Pydantic 请求、响应、状态快照模型 |
| `hardware/enums.py` | 设备类型、在线状态、工作状态、告警状态、命令状态 |
| `hardware/provider_base.py` | `HardwareProvider` 抽象接口 |
| `hardware/simulator_provider.py` | 当前状态机模拟器 provider |
| `hardware/realtime_store.py` | 当前状态快照读写 |
| `hardware/command_dispatcher.py` | 命令下发、命令状态管理 |
| `hardware/ingest_service.py` | 状态上报和事件上报处理 |
| `hardware/offline_detector.py` | 心跳超时离线判断 |
| `routers/hardware_ingest.py` | `/api/hardware/ingest/*` 接口 |
| `routers/simulator.py` | `/api/simulator/*` 接口 |
| `services/device_status_service.py` | 聚合成 8083 兼容结构 |

`main.py` 只保留 app 初始化和 router 注册。

## 11. Provider 接口

后端 service 层只依赖这个接口。

```py
from typing import Protocol, Any

class HardwareProvider(Protocol):
    def list_devices(
        self,
        *,
        area_id: str | None = None,
        device_type: str | None = None,
        online_status: str | None = None,
    ) -> list[dict[str, Any]]:
        ...

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        ...

    def upsert_states(self, items: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
        ...

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        ...

    def dispatch_command(
        self,
        device_id: str,
        *,
        command: str,
        operator: str,
        reason: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        ...
```

Provider 选择规则：

```env
HARDWARE_MODE=simulator
```

| `HARDWARE_MODE` | 行为 |
|---|---|
| `simulator` | 只用模拟器 |
| `real` | 只用真实硬件状态源 |
| `hybrid` | 真实硬件优先，没有真实数据时使用模拟器补位 |

## 12. 状态存储

`SIM-0.2` 至少要支持当前状态快照持久化。数据库表建议如下。

### 12.1 设备表 `hardware_devices`

| 字段 | 类型 | 说明 |
|---|---|---|
| `device_id` | varchar | 主键 |
| `vendor_device_id` | varchar | 厂商设备 ID |
| `name` | varchar | 设备名称 |
| `area_id` | varchar | 区域 ID |
| `area_name` | varchar | 区域名称 |
| `device_type` | varchar | 设备类型 |
| `device_type_name` | varchar | 设备类型中文 |
| `enabled` | boolean | 是否启用 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

### 12.2 状态快照表 `hardware_state_snapshots`

| 字段 | 类型 | 说明 |
|---|---|---|
| `device_id` | varchar | 主键 |
| `online_status` | varchar | 在线状态 |
| `work_status` | varchar | 工作状态 |
| `alarm_status` | varchar | 告警状态 |
| `value` | decimal/null | 数值 |
| `unit` | varchar/null | 单位 |
| `battery` | int/null | 电量 |
| `signal` | int/null | 信号 |
| `sequence` | bigint | 状态序号 |
| `last_heartbeat_at` | datetime | 最后心跳 |
| `last_changed_at` | datetime | 最后变化 |
| `raw_status` | json | 原始状态 |
| `metadata` | json | 扩展信息 |
| `updated_at` | datetime | 更新时间 |

### 12.3 事件表 `hardware_events`

| 字段 | 类型 | 说明 |
|---|---|---|
| `event_id` | varchar | 主键 |
| `device_id` | varchar | 设备 ID |
| `event_type` | varchar | 事件类型 |
| `event_level` | varchar | 事件等级 |
| `title` | varchar | 标题 |
| `description` | text | 描述 |
| `value` | decimal/null | 数值 |
| `unit` | varchar/null | 单位 |
| `raw_payload` | json | 原始事件 |
| `event_time` | datetime | 事件时间 |
| `created_at` | datetime | 入库时间 |

### 12.4 命令表 `hardware_commands`

| 字段 | 类型 | 说明 |
|---|---|---|
| `command_id` | varchar | 主键 |
| `device_id` | varchar | 设备 ID |
| `command` | varchar | 命令 |
| `status` | varchar | 命令状态 |
| `operator` | varchar | 操作人 |
| `reason` | varchar | 原因 |
| `payload` | json | 命令参数 |
| `result_message` | varchar | 回执信息 |
| `raw_result` | json | 原始回执 |
| `created_at` | datetime | 创建时间 |
| `started_at` | datetime/null | 开始时间 |
| `finished_at` | datetime/null | 完成时间 |

## 13. 离线判断

环境变量：

```env
HARDWARE_HEARTBEAT_TIMEOUT_SECONDS=30
HARDWARE_OFFLINE_SCAN_SECONDS=10
```

规则：

| 条件 | 处理 |
|---|---|
| `now - lastHeartbeatAt <= timeout` | 保持原状态 |
| `now - lastHeartbeatAt > timeout` | `onlineStatus=offline`、`workStatus=offline`、`alarmStatus=warning` |
| 重新收到状态 | 恢复上报状态 |
| 人工维护中 | 不自动改成离线，除非明确收到故障或维护结束 |

## 14. 与 8083 前端关系

前端不需要知道状态来自模拟器还是真实硬件。

| 前端使用接口 | 后端数据来源 |
|---|---|
| `GET /api/dashboard/overview` | `HardwareProvider` 聚合 |
| `GET /api/device-status/options` | `HardwareProvider` 聚合 |
| `GET /api/device-status/summary` | `HardwareProvider` 聚合 |
| `GET /api/device-status/records` | `HardwareProvider` 聚合成 8083 兼容结构 |
| `GET /api/simulator/devices` | 只用于模拟器管理页 |
| `POST /api/simulator/tick` | 只用于开发和演示 |

`/api/device-status/records` 必须继续输出 8083 当前需要的格式：

```json
{
  "records": [
    {
      "region": "A区",
      "device": "烟感器",
      "online": 3,
      "offline": 1
    }
  ],
  "updatedAt": "2026-05-07T11:30:00+08:00"
}
```

## 15. 硬件对接程序要求

硬件同学只需要保证三件事。

### 15.1 状态上报

每 `5` 到 `10` 秒上报一次当前状态。没有变化也要上报心跳。

最低字段：

```json
{
  "deviceId": "door_r01_001",
  "deviceType": "door",
  "onlineStatus": "online",
  "workStatus": "closed",
  "alarmStatus": "normal",
  "lastHeartbeatAt": "2026-05-07T11:30:00+08:00",
  "lastChangedAt": "2026-05-07T11:29:40+08:00",
  "sequence": 1024
}
```

### 15.2 事件上报

发生告警、故障、开门、关门、车辆通行、视频识别等事件时立即上报。

### 15.3 命令回执

收到后端命令后必须回传 `commandId`、`status`、`message`。

## 16. 本轮任务拆分

| 任务编号 | 负责人 | 任务 | 输出 |
|---|---|---|---|
| HW-001 | 后端 | 拆分 `hardware/` 目录 | 文件结构落地 |
| HW-002 | 后端 | 定义 `schemas.py` 和 `enums.py` | Pydantic 模型和枚举 |
| HW-003 | 后端 | 抽象 `HardwareProvider` | service 层不直接依赖模拟器 |
| HW-004 | 后端 | 改造模拟器为 `SimulatorProvider` | 原 `/api/simulator/*` 不破坏 |
| HW-005 | 后端 | 实现 `RealtimeStateStore` | 支持内存和数据库实现 |
| HW-006 | 后端 | 新增状态上报接口 | `POST /api/hardware/ingest/status` |
| HW-007 | 后端 | 新增事件上报接口 | `POST /api/hardware/ingest/event` |
| HW-008 | 后端 | 新增命令回执接口 | `POST /api/hardware/command-results` |
| HW-009 | 后端 | 实现离线扫描 | 心跳超时自动离线 |
| HW-010 | 后端 | 改造设备状态聚合 | `/api/device-status/*` 从 provider 读取 |
| HW-011 | 硬件 | 编写硬件适配器 | 能按本文档 JSON 上报 |
| HW-012 | 硬件 | 对接门禁/道闸/传感器至少一种真实设备 | 状态可进入系统 |
| HW-013 | 前端 | 模拟器页面接入 | 可查看状态、手动 tick、发命令 |
| HW-014 | 测试 | 联调验收 | 输出状态、事件、命令、离线测试记录 |

## 17. 验收清单

| 检查项 | 必须结果 |
|---|---|
| `GET /api/simulator/summary` | 可用 |
| `GET /api/simulator/devices` | 可用 |
| `POST /api/simulator/tick` | 可推进状态 |
| `POST /api/simulator/devices/{device_id}/command` | 可改变模拟设备状态 |
| `POST /api/hardware/ingest/status` | 可接收真实/适配器状态 |
| `POST /api/hardware/ingest/event` | 可接收事件 |
| `POST /api/hardware/command-results` | 可接收命令回执 |
| `/api/device-status/summary` | 兼容 8083 |
| `/api/device-status/records` | 兼容 8083 |
| 心跳超时 | 自动离线 |
| 恢复上报 | 自动恢复在线 |
| 无真实硬件 | 仍可用模拟器联调 |
| `openapi.json` | 包含本轮新增硬件接口 |

## 18. 联调顺序

1. 后端启动 `HARDWARE_MODE=simulator`，确认原模拟器接口正常。
2. 前端 `8083` 读取 `/api/device-status/*`，确认页面不受影响。
3. 后端开启 `HARDWARE_MODE=hybrid`。
4. 硬件适配器调用 `POST /api/hardware/ingest/status` 上报一台设备。
5. 前端设备状态页面看到该设备状态。
6. 硬件适配器停止上报，等待超时后设备变成 `offline`。
7. 硬件适配器恢复上报，设备恢复 `online`。
8. 前端或后端下发命令，硬件适配器回传命令结果。
9. 告警事件上报后，告警中心或事件中心可查询。
10. 导出联调记录，作为本轮验收附件。

## 19. 安全规则

| 项 | 要求 |
|---|---|
| 上报鉴权 | 使用 `X-Hardware-Token` |
| Token 配置 | 放环境变量，不写死代码 |
| 原始报文 | 存 `rawStatus` 或 `rawPayload`，便于排查 |
| 命令接口 | 必须记录操作人、原因、时间 |
| 命令幂等 | 同一个 `commandId` 重复回执不能重复执行 |
| 日志 | 状态上报失败、命令失败、字段不合法必须记录 |

环境变量：

```env
HARDWARE_MODE=hybrid
HARDWARE_INGEST_TOKEN=change-this-token
HARDWARE_HEARTBEAT_TIMEOUT_SECONDS=30
HARDWARE_OFFLINE_SCAN_SECONDS=10
HARDWARE_STATE_STORE=memory
```

## 20. 当前文件与后续文件

| 文件 | 当前状态 | 说明 |
|---|---|---|
| `backend/app/hardware_state_machine.py` | 已有 | `SIM-0.1` 状态机核心 |
| `backend/app/main.py` | 已有 | 当前包含 simulator API 和设备状态聚合 |
| `backend/.env.example` | 已有 | 模拟器开关 |
| `docs/hardware-state-machine-simulator.md` | 已更新 | 当前硬件落地文档 |
| `backend/app/hardware/*` | 待新增 | `SIM-0.2` 拆分目标 |
| `backend/app/routers/hardware_ingest.py` | 待新增 | 硬件状态、事件、命令回执入口 |

