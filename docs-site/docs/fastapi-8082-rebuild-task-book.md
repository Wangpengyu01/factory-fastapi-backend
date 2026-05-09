---
title: FastAPI 8082 从零重构任务书
description: 将旧 8082、新标准后端、8083 大屏、树莓派 Demo 和文档站拆开，定义新 FastAPI 后端的接口、目录、阶段和验收标准。
---

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
```

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

## 6. P0 接口：第一阶段必须完成

### 6.1 `GET /api/health`

```json
{
  "status": "ok"
}
```

### 6.2 `GET /api/info`

返回后端名称、版本、数据源模式和当前文档 profile。

### 6.3 `GET /api/dashboard/aggregate`

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

### 6.4 `GET /api/dashboard/overview`

兼容旧前端：

- 保留旧字段。
- 同时返回 `centerScene/eventBoard/eventList/riskWarnings/subsystems`。
- 内部复用 `DashboardAggregateService`。

### 6.5 `GET /api/subsystems`

返回人脸识别、车辆管控、行车管控、火灾算法四个入口。

要求：

- 不能返回 `localhost:5173`。
- 未配置 URL 时返回 `url: null`、`enabled: false`。
- `/api/dashboard/aggregate.data.subsystems` 与本接口保持一致。

### 6.6 `GET /api/events`

```http
GET /api/events?areaId=&eventType=&level=&status=&page=1&pageSize=20
```

给右侧事件列表和事件页提供统一事件流。

来源：

```text
/api/alarms
/api/alerts
/api/ai/detections
/api/railway/linkage-records
硬件事件 store
```

### 6.7 `GET /api/events/{eventId}` 和 `PATCH /api/events/{eventId}/close`

统一使用 `PATCH` 关闭事件。必要时临时加 `POST` 别名做兼容。

### 6.8 `/api/device-status/*`

```http
GET /api/device-status/options
GET /api/device-status/records
GET /api/device-status/summary
```

要求：

- 保持 8083 已有结构可用。
- 数据来源改为 `DeviceStatusService`。
- 新增故障和告警统计时，不能破坏旧字段。

### 6.9 `GET /api/simulator/summary`

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

### 6.10 `/api/simulator/devices`

```http
GET /api/simulator/devices?areaId=&deviceType=&onlineStatus=
GET /api/simulator/devices/{deviceId}
```

### 6.11 `POST /api/simulator/tick`

```http
POST /api/simulator/tick?steps=1&syncNacos=false
```

### 6.12 `POST /api/simulator/devices/{deviceId}/command`

支持：

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

### 6.13 `POST /api/simulator/nacos-sync`

把当前 Python 模拟设备快照写入 Nacos。

Header：

```text
X-Publish-Key: 你的PUBLISH_API_KEY
```

## 7. P1 接口：真实硬件接入

### 7.1 `POST /api/hardware/ingest/status`

真实硬件适配器上报设备当前状态。

### 7.2 `POST /api/hardware/ingest/event`

真实硬件适配器上报告警、离线、恢复、门禁、车辆、行车联动等事件。

### 7.3 `POST /api/hardware/command-results`

真实硬件适配器把命令执行结果回传给后端，补齐命令闭环。

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

| 层 | 内容 | 策略 |
|---|---|---|
| 第一层 | 大屏核心接口 | 新写，不依赖旧 router |
| 第二层 | 设备、报警、区域、视频、报表 | 先用 adapter 复用旧数据结构，再逐步重构 |
| 第三层 | 巡检、测量、预制点等业务 | 保留旧接口，等大屏稳定后再迁移 |

## 10. 开发阶段计划

| 阶段 | 目标 | 验收 |
|---|---|---|
| 阶段 0 | 冻结旧后端 | 能访问旧 `/openapi.json` |
| 阶段 1 | 新 FastAPI 骨架 | `/api/health`、`/api/info`、`/openapi.json` 可访问 |
| 阶段 2 | 模拟器和大屏聚合 | `simulator/summary`、`dashboard/aggregate`、`subsystems`、`events` 可用 |
| 阶段 3 | Nacos 链路 | `simulator/nacos-sync` 可写入 Nacos |
| 阶段 4 | 真实硬件入口 | 三个 hardware ingest/command-results 接口可用 |
| 阶段 5 | 8083 联调 | Network 能看到 `dashboard/aggregate` 和 `subsystems` |
| 阶段 6 | 正式切换 8082 | 新后端接管正式端口，有旧服务备份 |

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
