---
title: 101.43.49.78:8082 API 符合度检查与补齐清单
description: 对照线上 8082 OpenAPI 和当前文档要求，列出大屏、模拟器、Nacos 链路、后期硬件接入需要补齐的接口。
---

# 101.43.49.78:8082 API 符合度检查与补齐清单

| 项 | 内容 |
|---|---|
| 文档版本 | `DOC-API-GAP-101-8082-2026.05.09` |
| 检查对象 | `http://101.43.49.78:8082/openapi.json` |
| 检查时间 | `2026-05-09` |
| 当前 OpenAPI | `72 paths / 73 operations` |
| 结论 | 基础业务接口较完整，但没有完全符合我们最新的大屏聚合、模拟器写 Nacos、后期硬件接入文档要求 |

## 1. 总体结论

当前 `8082` 已经覆盖了门禁、车辆、行车、视频、报警、报表、设备状态、巡检、Nacos 配置桥、模拟器基础接口。

但和我们文档要求相比，核心差距集中在：

1. 大屏首屏还没有统一聚合接口。
2. 中间主画面、右侧事件看板、事件列表、风险预警还需要前端自己拼接口。
3. 底部四个子系统入口没有后端统一下发。
4. 模拟器能跑，但没有写入 Nacos 的专用接口和同步状态字段。
5. 后期真实硬件对接入口还没落地。

## 2. 符合度总表

| 模块 | 我们文档要求 | 8082 当前情况 | 是否符合 | 处理意见 |
|---|---|---|---|---|
| 基础响应结构 | 业务接口使用 `code/success/message/data` | 大多数接口已符合 | 基本符合 | 保留 |
| 8083 兼容设备状态 | `/api/device-status/options/records/summary` | 已存在，返回结构可用 | 符合 | 保留 |
| 区域/设备/视频/报表 | `/api/areas`、`/api/devices/list`、`/api/video/*`、`/api/reports/*` | 已存在 | 基本符合 | 作为聚合接口数据源 |
| 大屏首屏聚合 | `GET /api/dashboard/aggregate` | 不存在，404 | 不符合 | P0 新增 |
| 大屏旧概览 | `/api/dashboard/overview` 也应扩展聚合字段 | 只有顶部指标和设备记录 | 不符合 | P0 扩展或转调 aggregate |
| 中间主画面 | `data.centerScene` 或 `/api/dashboard/center-scene` | 不存在 | 不符合 | P0 补齐 |
| 事件看板 | `data.eventBoard` | 不存在 | 不符合 | P0 补齐 |
| 事件列表 | `data.eventList` 或 `GET /api/events` | 只有 `GET /api/events/{eventId}` | 不符合 | P0/P1 补齐列表 |
| 风险预警 | `data.riskWarnings` | 不存在 | 不符合 | P0 补齐 |
| 底部子系统 | `data.subsystems` 或 `GET /api/subsystems` | 不存在，404 | 不符合 | P0 新增 |
| 模拟器基础 | `/api/simulator/summary/devices/tick/command` | 已存在 | 部分符合 | 需统一字段 |
| 模拟器写 Nacos | `POST /api/simulator/nacos-sync` | 不存在 | 不符合 | P0 新增 |
| 模拟器同步状态 | `summary.data.nacosSync` | 不存在 | 不符合 | P0 扩展 |
| 真实硬件状态上报 | `POST /api/hardware/ingest/status` | 不存在 | 不符合 | P1 新增 |
| 真实硬件事件上报 | `POST /api/hardware/ingest/event` | 不存在 | 不符合 | P1 新增 |
| 命令回执 | `POST /api/hardware/command-results` | 不存在 | 不符合 | P1 新增 |
| 实时事件推送 | SSE/WebSocket | 不存在 | 未覆盖 | P2 新增 |
| 配置版本/备份 | `/api/config/versions`、`/api/config/backups` | 不存在 | 未覆盖 | P2 新增 |

## 3. P0 必须补齐 API

### 3.1 `GET /api/dashboard/aggregate`

给 8083 大屏首屏一次性返回顶部指标、设备状态、中间主画面、右侧事件、风险预警、硬件快照和底部四个子系统入口。

必须包含：

```text
centerScene
areas
eventBoard
eventList
riskWarnings
deviceStatus
hardware
subsystems
dataSource
updatedAt
```

### 3.2 `GET /api/subsystems`

替代前端写死 `localhost:5173`，统一下发四个子系统入口：

```text
face      人脸识别
vehicle   车辆管控
rail      行车管控
fire      火灾算法
```

### 3.3 `GET /api/events`

当前只有详情和关闭接口，缺列表接口。需要补：

```http
GET /api/events?areaId=&eventType=&level=&status=&page=1&pageSize=20
```

后端可以聚合：

```text
/api/alarms
/api/alerts
/api/ai/detections
/api/railway/linkage-records
```

### 3.4 `POST /api/simulator/nacos-sync`

把当前 Python 模拟设备快照写入 Nacos。

```http
POST /api/simulator/nacos-sync
X-Publish-Key: 你的PUBLISH_API_KEY
```

同时扩展：

```http
POST /api/simulator/tick?steps=1&syncNacos=true
```

### 3.5 扩展 `GET /api/simulator/summary`

当前字段偏旧，需要兼容新增：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `tick` | `number` | 是 | 模拟器当前步进序号。每次自动 tick 或手动 `POST /api/simulator/tick` 后递增，用来证明模拟状态在持续变化。 |
| `totalDevices` | `number` | 是 | 模拟器管理的设备总数。 |
| `onlineDevices` | `number` | 是 | 当前在线设备数量。 |
| `offlineDevices` | `number` | 是 | 当前离线、故障、维护等非正常在线设备数量。建议口径为 `totalDevices - onlineDevices`。 |
| `faultDevices` | `number` | 是 | 当前故障设备数量，来源于设备 `onlineStatus=fault` 或等价故障状态。 |
| `alarmDevices` | `number` | 是 | 当前告警设备数量，来源于设备 `alarmStatus=alarm`。 |
| `onlineRate` | `number` | 是 | 在线率百分比，保留两位小数，计算方式为 `onlineDevices / totalDevices * 100`。 |
| `updatedAt` | `string` | 是 | 后端生成本次统计的时间，使用 ISO 8601，建议带 `+08:00` 时区。 |
| `nacosSync` | `object` | 是 | 模拟器写入 Nacos 的状态摘要。即使未启用同步，也必须返回对象，方便前端稳定读取。 |

`nacosSync` 字段结构：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `enabled` | `boolean` | 是 | 是否启用模拟器自动写入 Nacos。 |
| `dataId` | `string` | 是 | 写入 Nacos 的 dataId，建议为 `factory.hardware.snapshot.json`。 |
| `group` | `string` | 是 | Nacos group，默认 `DEFAULT_GROUP`。 |
| `tenant` | `string/null` | 是 | Nacos 命名空间，未配置时为 `null`。 |
| `lastSuccessAt` | `string/null` | 是 | 最近一次写入成功时间。 |
| `lastErrorAt` | `string/null` | 是 | 最近一次写入失败时间。 |
| `lastError` | `string/null` | 是 | 最近一次失败原因。 |
| `lastTick` | `number/null` | 是 | 最近一次成功写入时的模拟器 tick。 |

目标返回示例：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "tick": 14520,
    "totalDevices": 143,
    "onlineDevices": 135,
    "offlineDevices": 8,
    "faultDevices": 3,
    "alarmDevices": 37,
    "onlineRate": 94.41,
    "updatedAt": "2026-05-09T16:40:00+08:00",
    "nacosSync": {
      "enabled": true,
      "dataId": "factory.hardware.snapshot.json",
      "group": "DEFAULT_GROUP",
      "tenant": null,
      "lastSuccessAt": "2026-05-09T16:39:55+08:00",
      "lastErrorAt": null,
      "lastError": null,
      "lastTick": 14520
    },
    "total_devices": 143,
    "online_devices": 135,
    "normal_devices": 103,
    "alarm_devices": 37,
    "simulation_running": true,
    "last_tick": "2026-05-09T16:40:00+08:00"
  }
}
```

处理要求：

- 不要直接删除旧字段，先兼容保留。
- 字段不能只写进文档，`http://101.43.49.78:8082/api/simulator/summary` 实际返回也必须包含这些字段。
- `nacosSync.enabled=false` 时也要返回完整对象，不能省略 `nacosSync`。

最小验收：

```bash
curl http://101.43.49.78:8082/api/simulator/summary
```

验收条件：

```text
data.tick 存在
data.totalDevices 存在
data.onlineDevices 存在
data.offlineDevices 存在
data.faultDevices 存在
data.alarmDevices 存在
data.onlineRate 存在
data.updatedAt 存在
data.nacosSync 存在
data.nacosSync.enabled 存在
data.nacosSync.dataId 存在
data.nacosSync.group 存在
```

## 4. P1 后期硬件对接 API

### 4.1 `POST /api/hardware/ingest/status`

真实硬件适配器上报设备当前状态。

### 4.2 `POST /api/hardware/ingest/event`

真实硬件适配器上报告警、离线、恢复、门禁、车辆、行车联动等事件。

### 4.3 `POST /api/hardware/command-results`

真实硬件适配器把命令执行结果回传给后端，补齐命令闭环。

## 5. P2 可后补 API

| API | 用途 |
|---|---|
| `GET /api/hardware/devices` | 统一查询真实硬件和模拟硬件 |
| `GET /api/hardware/events` | 查询硬件原始事件 |
| `GET /api/events/stream` 或 WebSocket | 大屏实时推送事件 |
| `GET /api/config/versions` | Nacos 配置版本列表 |
| `POST /api/config/versions/{versionId}/rollback` | 配置回滚 |
| `GET /api/config/backups` | 配置备份列表 |
| `POST /api/config/backups` | 创建配置备份 |

## 6. 字段和方法需要统一的地方

| 问题 | 当前 8082 | 文档要求 | 建议 |
|---|---|---|---|
| 模拟器 summary 字段 | `total_devices`、`online_devices` | `totalDevices`、`onlineDevices` | 保留旧字段，同时新增 camelCase |
| 事件关闭方法 | `PATCH /api/events/{eventId}/close` | 文档部分位置写过 `POST` | 统一使用 `PATCH`，必要时加 `POST` 别名 |
| 大屏首屏接口 | `/api/dashboard/overview` | `/api/dashboard/aggregate` | 新增 aggregate，overview 兼容 |
| 子系统入口 | 无 | `/api/subsystems` | 后端统一下发 URL，前端禁止写死 localhost |
| 模拟器 Nacos 链路 | 无专用接口 | `/api/simulator/nacos-sync` | 新增接口和 `nacosSync` 状态 |

## 7. 后端补齐顺序

| 顺序 | 任务 | 验收 |
|---|---|---|
| 1 | 新增 `/api/dashboard/aggregate` | 返回 `centerScene/eventBoard/eventList/riskWarnings/subsystems` |
| 2 | 新增 `/api/subsystems` | 四个底部入口不再写死 localhost |
| 3 | 新增 `/api/events` | 右侧事件列表和事件页可分页查询 |
| 4 | 新增 `/api/simulator/nacos-sync` | 模拟器快照能写入 Nacos |
| 5 | 扩展 `/api/simulator/summary` | 返回 `nacosSync` 和 camelCase 字段 |
| 6 | 新增 `/api/hardware/ingest/status` | 硬件适配器可上报状态 |
| 7 | 新增 `/api/hardware/ingest/event` | 硬件适配器可上报事件 |
| 8 | 新增 `/api/hardware/command-results` | 命令可形成闭环 |

## 8. 最小验收命令

```bash
curl http://101.43.49.78:8082/api/dashboard/aggregate
curl http://101.43.49.78:8082/api/subsystems
curl "http://101.43.49.78:8082/api/events?page=1&pageSize=20"
curl http://101.43.49.78:8082/api/simulator/summary
curl -X POST http://101.43.49.78:8082/api/simulator/nacos-sync -H "X-Publish-Key: 你的PUBLISH_API_KEY"
```

以上接口全部返回 `200` 后，才算满足我们最新文档对 8082 的补齐要求。
