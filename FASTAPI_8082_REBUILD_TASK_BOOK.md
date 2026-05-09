# FastAPI 8082 从零重构任务书

| 项 | 内容 |
|---|---|
| 文档版本 | `DOC-FASTAPI-8082-REBUILD-2026.05.09` |
| 目标系统 | 成品库区域全封闭管控系统 FastAPI 后端 |
| 新后端目标端口 | 先跑 `18082` 或 `8084`，验收后再切正式 `8082` |
| 当前旧后端 | `101.43.49.78:8082`，只作为参考和过渡，不直接覆盖 |
| 当前前端大屏 | `101.43.49.78:8083` |
| 树莓派 Demo | `10.0.0.172:9000` / `10.0.0.172:8000`，只作为硬件模拟演示环境 |
| 文档站 | `https://wpengu.top` |

## 0. 先把边界说清楚

现在混乱的原因是把四类东西放在一起看了：

| 名称 | 是什么 | 能不能改 | 作用 |
|---|---|---|---|
| 旧 8082 | `101.43.49.78:8082` 当前业务后端 | 先不直接动 | 作为旧接口参考和临时生产能力 |
| 8083 大屏 | `101.43.49.78:8083` 当前前端 | 只按接口逐步切 | 最终消费新后端接口 |
| 树莓派 Demo | `10.0.0.172` 上的 Docker 演示 | 可随时改 | 演示 Nacos、FastAPI、Python 硬件模拟器 |
| 新 8082 标准后端 | 这份任务书要重构出来的新 FastAPI | 从零做 | 最终替换旧 8082 |

重构原则：

```text
旧 8082 不直接推倒
新后端单独起服务
接口按文档标准重新实现
通过验收后再把 8082 切到新后端
```

## 1. 重构目标

新 FastAPI 后端要解决三件事：

1. 给 `8083` 大屏一个稳定、统一、少拼接的后端。
2. 把 Python 模拟设备、Nacos、FastAPI、大屏串成一条链。
3. 给后期真实硬件接入预留标准入口，不再让前端关心 PLC、门禁 SDK、摄像头协议。

最终链路：

```text
真实硬件 / Python 模拟器
        ↓
硬件状态标准化
        ↓
FastAPI 状态存储 / Nacos 配置
        ↓
Dashboard 聚合服务
        ↓
/api/dashboard/aggregate
        ↓
8083 大屏
```

## 2. 新旧接口处理原则

| 类型 | 处理方式 |
|---|---|
| 旧 8082 已有且前端正在用 | 保留兼容路径，内部可转调新 service |
| 新文档要求但旧 8082 没有 | 按本任务书新增 |
| 字段命名混乱 | 新接口统一 camelCase，旧字段只做兼容 |
| mock 数据 | 只能放在 simulator 或 fixtures，不能散落在业务 router |
| Nacos 读写 | 集中在 `NacosService`，业务代码不能到处拼 Nacos 请求 |
| 硬件协议 | 放到 adapter，不进大屏接口 |

不要再出现：

```text
一个 router 里同时写 mock、Nacos、硬件协议、前端聚合逻辑
```

## 3. 推荐目录结构

```text
backend/
  app/
    main.py
    core/
      config.py
      response.py
      time.py
      security.py
    schemas/
      common.py
      dashboard.py
      device_status.py
      event.py
      simulator.py
      subsystem.py
      hardware.py
      nacos.py
    routers/
      health.py
      dashboard.py
      device_status.py
      events.py
      subsystems.py
      simulator.py
      hardware_ingest.py
      nacos_config.py
      legacy.py
    services/
      dashboard_aggregate_service.py
      device_status_service.py
      event_service.py
      subsystem_service.py
      simulator_service.py
      hardware_state_store.py
      hardware_ingest_service.py
      nacos_service.py
      report_adapter.py
    adapters/
      old_8082_adapter.py
      nacos_adapter.py
      simulator_adapter.py
      hardware_adapter_base.py
    tests/
      test_dashboard_aggregate.py
      test_simulator_summary.py
      test_subsystems.py
      test_hardware_ingest.py
```

目录职责：

| 目录 | 职责 |
|---|---|
| `routers` | 只处理 HTTP 参数和响应，不写复杂业务 |
| `services` | 业务聚合、状态计算、数据组装 |
| `schemas` | Pydantic 请求/响应模型 |
| `adapters` | 外部系统适配，包含旧 8082、Nacos、真实硬件 |
| `core` | 配置、响应、时间、安全 |
| `tests` | 契约和验收测试 |

## 4. 统一响应结构

除明确兼容旧前端的接口外，新接口统一：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

分页统一：

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 0
}
```

时间统一：

```text
2026-05-09T16:40:00+08:00
```

## 5. 环境变量标准

```env
PORT=18082
APP_ENV=staging
CORS_ALLOWED_ORIGINS=http://101.43.49.78:8083,http://localhost:8083

NACOS_BASE_URL=http://nacos:8080
NACOS_API_VERSION=v3
NACOS_USERNAME=
NACOS_PASSWORD=
PUBLISH_API_KEY=change-this-to-a-strong-key

DATA_SOURCE_MODE=simulator
DEVICE_STATUS_SOURCE=simulator
NACOS_READ_FALLBACK_TO_SIMULATOR=true

USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
SIMULATOR_NACOS_SYNC_ENABLED=false
SIMULATOR_NACOS_DATA_ID=factory.hardware.snapshot.json
SIMULATOR_NACOS_GROUP=DEFAULT_GROUP
SIMULATOR_NACOS_TENANT=

SUBSYSTEM_BASE_URL=
SUBSYSTEM_FACE_URL=
SUBSYSTEM_VEHICLE_URL=
SUBSYSTEM_RAIL_URL=
SUBSYSTEM_FIRE_URL=

HARDWARE_MODE=simulator
HARDWARE_OFFLINE_TIMEOUT_SECONDS=30
```

`DATA_SOURCE_MODE` 取值：

| 值 | 说明 |
|---|---|
| `simulator` | 只用 Python 模拟器 |
| `nacos` | 从 Nacos 读取设备状态 |
| `hardware` | 只读真实硬件状态存储 |
| `hybrid` | 真实硬件优先，模拟器兜底 |

## 6. P0 接口：第一阶段必须完成

### 6.1 健康检查

```http
GET /api/health
```

返回：

```json
{
  "status": "ok"
}
```

### 6.2 API 信息

```http
GET /api/info
```

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "name": "factory-fastapi-backend",
    "version": "api-rebuild-v1",
    "apiProfile": "DOC-FASTAPI-8082-REBUILD-2026.05.09",
    "dataSourceMode": "simulator",
    "updatedAt": "2026-05-09T16:40:00+08:00"
  }
}
```

### 6.3 大屏完整聚合

```http
GET /api/dashboard/aggregate
```

这是新 8082 的核心接口。8083 首屏优先只调这个接口。

必须返回：

```text
onlineAccess
areaTotal
vehiclesOnSite
railStatus
deviceStatus
deviceRecords
deviceRegions
deviceTypes
centerScene
areas
eventBoard
eventList
riskWarnings
hardware
subsystems
dataSource
updatedAt
```

返回示例：

```json
{
  "code": 200,
  "success": true,
  "message": "获取大屏聚合数据成功",
  "data": {
    "onlineAccess": 32,
    "areaTotal": 52,
    "vehiclesOnSite": 4,
    "railStatus": "passing",
    "deviceStatus": {
      "summary": {
        "totalDevices": 143,
        "onlineDevices": 135,
        "offlineDevices": 8,
        "faultDevices": 3,
        "alarmDevices": 37,
        "onlineRate": 94.41
      },
      "records": [],
      "regions": [],
      "devices": [],
      "updatedAt": "2026-05-09T16:40:00+08:00"
    },
    "centerScene": {
      "sceneType": "factory-area-overview",
      "mapMode": "2d",
      "nodes": [],
      "links": [],
      "updatedAt": "2026-05-09T16:40:00+08:00"
    },
    "areas": [],
    "eventBoard": {
      "total": 0,
      "unhandled": 0,
      "critical": 0,
      "warning": 0,
      "items": []
    },
    "eventList": [],
    "riskWarnings": [],
    "hardware": {
      "total": 0,
      "items": []
    },
    "subsystems": [],
    "dataSource": "simulator",
    "updatedAt": "2026-05-09T16:40:00+08:00"
  }
}
```

实现要求：

- `DashboardAggregateService` 负责组装。
- 旧 `/api/dashboard/overview` 可以调用同一个 service。
- 前端不得再自己拼 `alarms + areas + devices + reports`。

### 6.4 大屏旧概览兼容

```http
GET /api/dashboard/overview
```

要求：

- 保留旧字段，避免旧前端断掉。
- 同时返回 `centerScene/eventBoard/eventList/riskWarnings/subsystems`。
- 内部复用 `DashboardAggregateService`。

### 6.5 底部四个子系统入口

```http
GET /api/subsystems
```

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "获取子系统入口成功",
  "data": {
    "items": [
      {
        "id": "face",
        "name": "人脸识别",
        "key": "faceRecognition",
        "url": "http://服务器IP/face/",
        "enabled": true,
        "description": "人员进出、识别记录和门禁联动"
      },
      {
        "id": "vehicle",
        "name": "车辆管控",
        "key": "vehicleControl",
        "url": "http://服务器IP/vehicle/",
        "enabled": true,
        "description": "车辆识别、道闸、场内车辆状态"
      },
      {
        "id": "rail",
        "name": "行车管控",
        "key": "railControl",
        "url": "http://服务器IP/rail/",
        "enabled": true,
        "description": "铁路道口、行车状态和道闸安全联动"
      },
      {
        "id": "fire",
        "name": "火灾算法",
        "key": "fireAlgorithm",
        "url": "http://服务器IP/fire/",
        "enabled": true,
        "description": "烟感温感、视频算法和火灾预警"
      }
    ],
    "total": 4,
    "updatedAt": "2026-05-09T16:40:00+08:00"
  }
}
```

要求：

- 不能返回 `localhost:5173`。
- 未配置 URL 时返回 `url: null`、`enabled: false`。
- `/api/dashboard/aggregate.data.subsystems` 与本接口保持一致。

### 6.6 统一事件列表

```http
GET /api/events?areaId=&eventType=&level=&status=&page=1&pageSize=20
```

用途：

给右侧事件列表和事件页提供统一事件流。

来源：

```text
/api/alarms
/api/alerts
/api/ai/detections
/api/railway/linkage-records
硬件事件 store
```

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "获取事件列表成功",
  "data": {
    "items": [
      {
        "id": "evt_00001",
        "eventType": "device_offline",
        "level": "warning",
        "status": "active",
        "title": "A区摄像机离线",
        "areaId": "r01",
        "areaName": "A区",
        "deviceId": "camera_r01_001",
        "deviceName": "A区摄像机1",
        "source": "alarm",
        "occurredAt": "2026-05-09T16:40:00+08:00",
        "updatedAt": "2026-05-09T16:40:00+08:00"
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

### 6.7 事件详情和关闭

```http
GET /api/events/{eventId}
PATCH /api/events/{eventId}/close
```

兼容要求：

- 当前旧文档里有些地方写过 `POST close`，新标准统一用 `PATCH`。
- 如需兼容，可以临时加 `POST /api/events/{eventId}/close` 别名。

### 6.8 设备状态兼容接口

```http
GET /api/device-status/options
GET /api/device-status/records
GET /api/device-status/summary
```

要求：

- 保持 8083 已有结构可用。
- 数据来源改为 `DeviceStatusService`。
- 新增故障和告警统计时，不能破坏旧字段。

`summary` 建议返回：

```json
{
  "summary": {
    "totalDevices": 143,
    "onlineDevices": 135,
    "offlineDevices": 8,
    "faultDevices": 3,
    "alarmDevices": 37,
    "onlineRate": 94.41
  },
  "records": []
}
```

### 6.9 模拟器汇总

```http
GET /api/simulator/summary
```

必须返回：

| 字段 | 类型 | 说明 |
|---|---|---|
| `tick` | `number` | 当前模拟步进序号 |
| `totalDevices` | `number` | 模拟设备总数 |
| `onlineDevices` | `number` | 在线设备数 |
| `offlineDevices` | `number` | 非在线设备数 |
| `faultDevices` | `number` | 故障设备数 |
| `alarmDevices` | `number` | 告警设备数 |
| `onlineRate` | `number` | 在线率 |
| `updatedAt` | `string` | 更新时间 |
| `nacosSync` | `object` | 写 Nacos 状态 |

`nacosSync`：

```json
{
  "enabled": true,
  "dataId": "factory.hardware.snapshot.json",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "lastSuccessAt": "2026-05-09T16:39:55+08:00",
  "lastErrorAt": null,
  "lastError": null,
  "lastTick": 14520
}
```

兼容要求：

- 可以保留 `total_devices`、`online_devices` 等旧字段。
- 新字段必须真实返回，不能只写文档。

### 6.10 模拟器设备列表

```http
GET /api/simulator/devices?areaId=&deviceType=&onlineStatus=
GET /api/simulator/devices/{deviceId}
```

设备字段：

```text
id
name
areaId
areaName
deviceType
deviceTypeName
onlineStatus
workStatus
alarmStatus
value
unit
battery
signal
sequence
lastHeartbeatAt
lastChangedAt
metadata
```

### 6.11 模拟器步进

```http
POST /api/simulator/tick?steps=1&syncNacos=false
```

要求：

- `steps` 默认 `1`。
- `syncNacos=true` 时，tick 后立即写 Nacos。

### 6.12 模拟器命令

```http
POST /api/simulator/devices/{deviceId}/command
```

Body：

```json
{
  "command": "set_alarm",
  "reason": "现场演示告警",
  "operator": "demo",
  "payload": {}
}
```

命令：

```text
recover
offline
fault
maintenance
set_alarm
clear_alarm
open
close
lock
unlock
reset
```

### 6.13 模拟器写 Nacos

```http
POST /api/simulator/nacos-sync
```

Header：

```text
X-Publish-Key: 你的PUBLISH_API_KEY
```

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "模拟器快照已写入 Nacos",
  "data": {
    "dataId": "factory.hardware.snapshot.json",
    "group": "DEFAULT_GROUP",
    "tenant": null,
    "tick": 14520,
    "records": 40,
    "hardwareItems": 143,
    "updatedAt": "2026-05-09T16:40:00+08:00"
  }
}
```

## 7. P1 接口：真实硬件接入

### 7.1 真实硬件状态上报

```http
POST /api/hardware/ingest/status
```

Body：

```json
{
  "deviceId": "smoke_r01_001",
  "deviceType": "smoke",
  "deviceTypeName": "烟感器",
  "areaId": "r01",
  "areaName": "A区",
  "onlineStatus": "online",
  "workStatus": "normal",
  "alarmStatus": "normal",
  "value": 320,
  "unit": "ppm",
  "battery": 92,
  "signal": 88,
  "reportedAt": "2026-05-09T16:40:00+08:00"
}
```

### 7.2 真实硬件事件上报

```http
POST /api/hardware/ingest/event
```

Body：

```json
{
  "eventId": "evt_20260509_0001",
  "deviceId": "smoke_r01_001",
  "eventType": "alarm",
  "level": "critical",
  "areaId": "r01",
  "areaName": "A区",
  "title": "A区烟感器告警",
  "description": "烟雾浓度超过阈值",
  "occurredAt": "2026-05-09T16:41:00+08:00"
}
```

### 7.3 命令执行回执

```http
POST /api/hardware/command-results
```

Body：

```json
{
  "commandId": "cmd_20260509_0001",
  "deviceId": "door_r01_001",
  "command": "open",
  "status": "success",
  "message": "门禁已打开",
  "finishedAt": "2026-05-09T16:42:00+08:00"
}
```

## 8. P2 接口：后续增强

| API | 用途 |
|---|---|
| `GET /api/hardware/devices` | 统一查询真实硬件和模拟硬件 |
| `GET /api/hardware/events` | 查询硬件原始事件 |
| `GET /api/events/stream` | 大屏 SSE 实时事件 |
| `GET /api/config/versions` | Nacos 配置版本 |
| `POST /api/config/versions/{versionId}/rollback` | 配置回滚 |
| `GET /api/config/backups` | 配置备份 |
| `POST /api/config/backups` | 创建备份 |

## 9. 旧 8082 接口迁移策略

旧 8082 当前已有很多业务接口，不建议第一天全部重写。

迁移分三层：

| 层 | 内容 | 策略 |
|---|---|---|
| 第一层 | 大屏核心接口 | 新写，不依赖旧 router |
| 第二层 | 设备、报警、区域、视频、报表 | 先用 adapter 复用旧数据结构，再逐步重构 |
| 第三层 | 巡检、测量、预制点等业务 | 保留旧接口，等大屏稳定后再迁移 |

兼容路径：

```text
/api/access/*
/api/vehicle/*
/api/railway/*
/api/video/*
/api/alarms*
/api/reports/*
/api/v1/inspection/*
```

这些可以先挂在 `routers/legacy.py` 或对应模块里，但不要污染 dashboard 聚合逻辑。

## 10. 开发阶段计划

### 阶段 0：冻结旧后端

目标：

- 旧 `101.43.49.78:8082` 只做参考。
- 拉取旧 OpenAPI 保存。
- 不直接覆盖旧容器。

验收：

```bash
curl http://101.43.49.78:8082/openapi.json
```

### 阶段 1：新 FastAPI 骨架

目标：

- 新服务跑 `18082`。
- 有 `/api/health`、`/api/info`。
- 生成 OpenAPI。

验收：

```bash
curl http://101.43.49.78:18082/api/health
curl http://101.43.49.78:18082/api/info
curl http://101.43.49.78:18082/openapi.json
```

### 阶段 2：模拟器和大屏聚合

目标：

- 完成 `/api/simulator/*`。
- 完成 `/api/dashboard/aggregate`。
- 完成 `/api/subsystems`。
- 完成 `/api/events`。

验收：

```bash
curl http://101.43.49.78:18082/api/simulator/summary
curl http://101.43.49.78:18082/api/dashboard/aggregate
curl http://101.43.49.78:18082/api/subsystems
curl "http://101.43.49.78:18082/api/events?page=1&pageSize=20"
```

### 阶段 3：Nacos 链路

目标：

- 完成 `/api/nacos/config`。
- 完成 `/api/simulator/nacos-sync`。
- `simulator -> Nacos -> FastAPI -> aggregate` 可跑通。

验收：

```bash
curl -X POST http://101.43.49.78:18082/api/simulator/nacos-sync -H "X-Publish-Key: 你的PUBLISH_API_KEY"
curl "http://101.43.49.78:18082/api/nacos/config?dataId=factory.hardware.snapshot.json&group=DEFAULT_GROUP"
curl http://101.43.49.78:18082/api/dashboard/aggregate
```

### 阶段 4：真实硬件入口

目标：

- 完成 `hardware/ingest/status`。
- 完成 `hardware/ingest/event`。
- 完成 `hardware/command-results`。

验收：

```bash
curl -X POST http://101.43.49.78:18082/api/hardware/ingest/status -H "Content-Type: application/json" -d "{}"
curl -X POST http://101.43.49.78:18082/api/hardware/ingest/event -H "Content-Type: application/json" -d "{}"
curl -X POST http://101.43.49.78:18082/api/hardware/command-results -H "Content-Type: application/json" -d "{}"
```

### 阶段 5：8083 联调

目标：

- 8083 默认数据源改接口模式。
- 首屏请求 `/api/dashboard/aggregate`。
- 底部按钮请求 `/api/subsystems`。
- 右侧事件使用 `eventBoard/eventList/riskWarnings`。

验收：

浏览器 Network 能看到：

```text
/api/dashboard/aggregate
/api/subsystems
```

页面不再出现：

```text
localhost:5173
```

### 阶段 6：正式切换 8082

目标：

- 新服务验收后切正式端口。
- 旧服务保留备份。

切换方式：

```text
Nginx / Docker 端口
8082 -> 新 FastAPI
```

回滚方式：

```text
保留旧 compose / 旧镜像 / 旧数据目录
```

## 11. 测试要求

必须有这些测试：

| 测试 | 要求 |
|---|---|
| OpenAPI 生成 | 能导出 `openapi.json` |
| 健康检查 | `/api/health` 200 |
| 大屏聚合 | `aggregate` 包含所有必填字段 |
| 子系统 | 不返回 localhost |
| 模拟器 summary | 包含 `tick/totalDevices/nacosSync` |
| 模拟器命令 | `set_alarm/recover` 可改变状态 |
| Nacos sync | 密钥错误 401/403，密钥正确可写入 |
| 硬件上报 | status/event 可写入 state store |

最低测试命令：

```bash
python -m py_compile app/main.py
pytest
curl http://127.0.0.1:18082/api/health
curl http://127.0.0.1:18082/api/dashboard/aggregate
curl http://127.0.0.1:18082/api/subsystems
curl http://127.0.0.1:18082/api/simulator/summary
```

## 12. 验收清单

| 检查项 | 通过标准 |
|---|---|
| 新服务不影响旧 8082 | 新服务先跑 `18082` |
| OpenAPI 清晰 | `/openapi.json` 可访问 |
| 大屏聚合完整 | `aggregate` 返回所有 P0 字段 |
| 前端不拼接口 | 首屏主要请求 `aggregate` |
| 子系统不写死 | 不出现 `localhost:5173` |
| 模拟器可演示 | tick、告警、恢复、故障可演示 |
| Nacos 链路可演示 | `nacos-sync` 成功写入 |
| 硬件接入可扩展 | 三个 ingest/command-results 接口存在 |
| 旧接口可过渡 | 旧 8082 常用路径有兼容或迁移说明 |

## 13. 不能做的事

1. 不能直接删掉旧 `101.43.49.78:8082`。
2. 不能让前端继续写死 `localhost:5173`。
3. 不能让 dashboard router 直接查一堆外部接口再临时拼字符串。
4. 不能把真实硬件协议写进前端。
5. 不能把 Nacos 密码、发布密钥写进代码仓库。
6. 不能只写文档不让接口真实返回字段。

## 14. 新后端完成后的最终形态

最终外部只需要记住：

```text
101.43.49.78:8083  大屏前端
101.43.49.78:8082  新 FastAPI 后端
wpengu.top          文档站
10.0.0.172          本地树莓派演示环境
```

8083 大屏首屏：

```text
GET /api/dashboard/aggregate
```

硬件模拟演示：

```text
GET  /api/simulator/summary
POST /api/simulator/tick
POST /api/simulator/nacos-sync
```

后期真实硬件：

```text
POST /api/hardware/ingest/status
POST /api/hardware/ingest/event
POST /api/hardware/command-results
```

这才是干净的新标准，不再把旧接口、demo、Nacos 桥、大屏接口混成一团。
