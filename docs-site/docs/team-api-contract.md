---
id: team-api-contract
title: 8082/8083 正式 API 契约汇总
slug: /team-api-contract
---

# 8082/8083 正式 API 契约汇总

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-CONTRACT-1.1` |
| 文档集 | `DOC-2026.05.07` |
| 适用系统版本 | `LEGACY-FE-8083` + `OPENAPI-8082-CURRENT-2026.05.07` |
| 当前状态 | 前后端联调契约 |
| 更新日期 | `2026-05-07` |

整理日期：`2026-05-06`

接口来源：

- 当前 Swagger：`http://101.43.49.78:8082/docs`
- 当前 OpenAPI：`http://101.43.49.78:8082/openapi.json`
- 当前前端入口：`http://101.43.49.78:8083`

本文档用于后端、前端、测试人员统一接口口径。`8083` 前端保持原访问入口不变，接口统一通过 `/api/...` 调用后端。

## 1. 基础约定

### 1.1 Base URL

| 环境 | Base URL |
|---|---|
| 线上参考 API | `http://101.43.49.78:8082` |
| 线上前端入口 | `http://101.43.49.78:8083` |
| 前端页面内调用 | `/api/...` |
| 本地后端 | `http://localhost:8000` |

前端代码禁止写死同学本地 demo 地址。页面内请求统一使用相对路径：

```ts
fetch("/api/dashboard/overview")
fetch("/api/device-status/records?regionId=all&deviceType=all")
```

### 1.2 标准响应结构

正式业务接口统一使用以下结构：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {},
  "traceId": "optional-trace-id"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `code` | `number` | 是 | HTTP 业务状态码 |
| `success` | `boolean` | 是 | 是否成功 |
| `message` | `string` | 是 | 人类可读提示 |
| `data` | `object/array/null` | 是 | 业务数据 |
| `traceId` | `string` | 否 | 链路追踪 ID |

### 1.3 8083 兼容裸 JSON 接口

以下接口为了兼容现有 `8083` 大屏控件，可以保持裸 JSON，不强制套 `code/success/data`：

| 方法 | 路径 | 返回结构 |
|---|---|---|
| `GET` | `/api/device-status/options` | `{ regions, devices }` |
| `GET` | `/api/device-status/summary` | `{ summary, records }` |
| `GET` | `/api/device-status/records` | `{ records, updatedAt }` |

`GET /api/dashboard/overview` 当前使用标准包装，前端读取时取 `response.data`。

### 1.4 分页结构

分页统一放在 `data` 内：

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 0
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | `array` | 当前页数据 |
| `page` | `number` | 当前页，从 `1` 开始 |
| `pageSize` | `number` | 每页数量 |
| `total` | `number` | 总数量 |

巡检接口当前 Swagger 使用 `per_page`，新实现统一兼容：

- 入参允许 `pageSize`
- 入参兼容 `per_page`
- 出参统一返回 `pageSize`

### 1.5 时间格式

所有新业务接口统一使用 ISO 8601：

```json
"2026-05-06T14:30:00+08:00"
```

历史巡检接口如已有 `created_at`、`measurement_time`，新代码可保留兼容字段，但新增字段使用 `camelCase`。

## 2. 状态码

| HTTP 状态码 | `code` | 含义 | 使用场景 |
|---:|---:|---|---|
| `200` | `200` | 成功 | 查询成功、命令已处理 |
| `201` | `201` | 创建成功 | 新增任务、创建导出任务 |
| `202` | `202` | 已接收 | 异步控制、报表导出、视频证据导出 |
| `204` | `204` | 成功无内容 | 删除成功 |
| `400` | `400` | 业务参数错误 | 未知区域、未知设备类型、非法命令 |
| `401` | `401` | 未认证 | 未登录、发布密钥错误 |
| `403` | `403` | 无权限 | 无门禁控制、无报表导出权限 |
| `404` | `404` | 资源不存在 | 设备、区域、告警、事件不存在 |
| `409` | `409` | 状态冲突 | 重复关闭事件、重复启动任务 |
| `422` | `422` | 字段校验失败 | 必填缺失、类型错误、Pydantic 校验失败 |
| `429` | `429` | 请求过频 | 高频轮询、重复下发控制 |
| `500` | `500` | 服务端异常 | 未预期代码错误 |
| `502` | `502` | 下游异常 | Nacos、视频平台、外部业务系统异常 |
| `503` | `503` | 服务不可用 | 依赖未配置、服务未启动 |
| `504` | `504` | 下游超时 | Nacos 或第三方接口超时 |

错误响应：

```json
{
  "code": 404,
  "success": false,
  "message": "设备不存在",
  "data": null,
  "traceId": "trace-202605060001"
}
```

字段校验错误兼容 FastAPI 默认结构：

```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "Input should be greater than or equal to 1",
      "type": "greater_than_equal"
    }
  ]
}
```

## 3. 全局枚举

### 3.1 区域

| id | name |
|---|---|
| `all` | 全部 |
| `r01` | A区 |
| `r02` | F区 |
| `r03` | L区 |
| `r04` | 成品库 |
| `r05` | 火车道 |
| `r06` | 道路 |
| `r07` | 厂房 |
| `r08` | 作业区 |

### 3.2 设备类型

| id | name |
|---|---|
| `all` | 全部 |
| `door` | 人员智能门/联锁门 |
| `vehicle` | 车辆识别与道闸 |
| `rail` | 火车道联动门 |
| `camera` | 摄像机 |
| `acoustic` | 声光报警 |
| `photoelectric` | 光电报警 |
| `smoke` | 烟感温感 |
| `nvr` | NVR |
| `ai` | AI分析服务器 |

### 3.3 通用在线状态

| 值 | 说明 |
|---|---|
| `online` | 在线 |
| `offline` | 离线 |
| `fault` | 故障 |
| `unknown` | 未知 |

### 3.4 门禁状态

| 值 | 说明 |
|---|---|
| `open` | 开启 |
| `closed` | 关闭 |
| `locked` | 锁定 |
| `opening` | 开启中 |
| `closing` | 关闭中 |
| `fault` | 故障 |

### 3.5 门禁命令

| 值 | 说明 |
|---|---|
| `open` | 开门 |
| `close` | 关门 |
| `lock` | 锁定 |
| `unlock` | 解锁 |
| `reset` | 复位 |

### 3.6 车辆道闸状态和命令

| 类型 | 值 | 说明 |
|---|---|---|
| `barrierStatus` | `open` | 已抬杆 |
| `barrierStatus` | `closed` | 已落杆 |
| `barrierStatus` | `opening` | 抬杆中 |
| `barrierStatus` | `closing` | 落杆中 |
| `barrierStatus` | `fault` | 故障 |
| `command` | `open` | 抬杆 |
| `command` | `close` | 落杆 |
| `command` | `reset` | 复位 |

### 3.7 火车道状态

| 字段 | 值 | 说明 |
|---|---|---|
| `railStatus` | `idle` | 空闲 |
| `railStatus` | `approaching` | 火车接近 |
| `railStatus` | `passing` | 火车通行中 |
| `railStatus` | `blocked` | 阻塞 |
| `signalStatus` | `none` | 无信号 |
| `signalStatus` | `green` | 允许 |
| `signalStatus` | `yellow` | 预警 |
| `signalStatus` | `red` | 禁止 |
| `mode` | `auto` | 自动模式 |
| `mode` | `manual` | 手动模式 |
| `mode` | `maintenance` | 维护模式 |

### 3.8 告警和事件

| 字段 | 值 | 说明 |
|---|---|---|
| `severity` | `low` | 低 |
| `severity` | `medium` | 中 |
| `severity` | `high` | 高 |
| `severity` | `critical` | 严重 |
| `status` | `pending` | 待处理 |
| `status` | `processing` | 处理中 |
| `status` | `closed` | 已关闭 |
| `action` | `ack` | 确认 |
| `action` | `dispatch` | 派单 |
| `action` | `close` | 关闭 |
| `action` | `ignore` | 忽略 |

### 3.9 通行结果

| 值 | 说明 |
|---|---|
| `allowed` | 允许 |
| `denied` | 拒绝 |
| `manual` | 人工放行 |
| `timeout` | 超时 |
| `unknown` | 未知 |

### 3.10 视频和 AI

| 字段 | 值 | 说明 |
|---|---|---|
| `cameraType` | `fixed` | 固定摄像机 |
| `cameraType` | `ptz` | 云台摄像机 |
| `cameraType` | `thermal` | 热成像 |
| `protocol` | `hls` | HLS 地址 |
| `protocol` | `flv` | FLV 地址 |
| `protocol` | `rtsp` | RTSP 地址 |
| `detectionStatus` | `new` | 新检测 |
| `detectionStatus` | `confirmed` | 已确认 |
| `detectionStatus` | `ignored` | 已忽略 |

## 4. 8083 大屏核心接口

### 4.1 大屏概览

`GET /api/dashboard/overview`

返回结构：`ApiResponse<DashboardOverview>`

```json
{
  "code": 200,
  "success": true,
  "message": "获取大屏概览数据成功",
  "data": {
    "onlineAccess": 19,
    "areaTotal": 139,
    "vehiclesOnSite": 22,
    "railStatus": "idle",
    "deviceRecords": [
      {
        "region": "A区",
        "device": "摄像机",
        "online": 12,
        "offline": 4
      }
    ],
    "deviceRegions": ["A区", "F区", "L区", "成品库"],
    "deviceTypes": ["摄像机", "人员智能门/联锁门"],
    "updatedAt": "2026-05-06T14:30:00+08:00"
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `onlineAccess` | `number` | 在线门禁数量 |
| `areaTotal` | `number` | 区域总人数或管控总量 |
| `vehiclesOnSite` | `number` | 场内车辆数 |
| `railStatus` | `string` | 火车道状态 |
| `deviceRecords` | `DeviceStatusRecord[]` | 设备在线离线统计 |
| `deviceRegions` | `string[]` | 设备统计涉及区域 |
| `deviceTypes` | `string[]` | 设备统计涉及类型 |
| `updatedAt` | `string` | 更新时间 |

### 4.2 设备状态筛选项

`GET /api/device-status/options`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `regionId` | `string` | `all` | 区域 ID |
| `region` | `string` | 无 | 兼容中文区域名，例如 `A区` |

返回结构：裸 JSON。

```json
{
  "regions": [
    { "id": "all", "name": "全部" },
    { "id": "r01", "name": "A区" }
  ],
  "devices": [
    { "id": "all", "name": "全部" },
    { "id": "camera", "name": "摄像机" }
  ]
}
```

兼容规则：

- 当前 `8082` 返回 `regions/devices` 为 `{ id, name }` 数组。
- 如果现有 `8083` 控件需要字符串数组，前端适配层使用 `regions.map(item => item.name)` 和 `devices.map(item => item.name)`。
- 后端筛选参数同时兼容 `regionId/deviceType` 和 `region/device`。

### 4.3 设备状态汇总

`GET /api/device-status/summary`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `regionId` | `string` | `all` | 区域 ID |
| `deviceType` | `string` | `all` | 设备类型 ID |
| `region` | `string` | 无 | 兼容中文区域名 |
| `device` | `string` | 无 | 兼容中文设备名 |

返回结构：裸 JSON。

```json
{
  "summary": {
    "totalDevices": 505,
    "onlineDevices": 460,
    "offlineDevices": 45,
    "onlineRate": 91.09
  },
  "records": [
    {
      "region": "A区",
      "device": "摄像机",
      "online": 50,
      "offline": 5
    }
  ]
}
```

### 4.4 设备状态明细

`GET /api/device-status/records`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `regionId` | `string` | `all` | 区域 ID |
| `deviceType` | `string` | `all` | 设备类型 ID |
| `region` | `string` | 无 | 兼容中文区域名 |
| `device` | `string` | 无 | 兼容中文设备名 |
| `dataId` | `string` | 空 | Nacos 配置 ID |
| `group` | `string` | `DEFAULT_GROUP` | Nacos 分组 |
| `tenant` | `string` | 空 | Nacos 命名空间 |
| `field` | `string` | `deviceStatus.records` | 配置内字段路径 |

返回结构：裸 JSON。

```json
{
  "records": [
    {
      "region": "A区",
      "device": "摄像机",
      "online": 50,
      "offline": 5
    }
  ],
  "updatedAt": "2026-05-06T14:30:00+08:00"
}
```

字段规则：

| 字段 | 类型 | 说明 |
|---|---|---|
| `region` | `string` | 中文区域名 |
| `device` | `string` | 中文设备名 |
| `online` | `number` | 在线数量，非负整数 |
| `offline` | `number` | 离线数量，非负整数 |

## 5. 标准请求体

### 5.1 发布 Nacos 配置

`POST /api/nacos/config`

Header：

| 名称 | 必填 | 说明 |
|---|---:|---|
| `X-Publish-Key` | 是 | 发布密钥 |

Body：

```json
{
  "dataId": "device-status.json",
  "group": "DEFAULT_GROUP",
  "tenant": "",
  "type": "json",
  "content": "{\"deviceStatus\":{\"records\":[]}}"
}
```

### 5.2 门禁控制

`POST /api/access/doors/{doorId}/command`

```json
{
  "command": "open",
  "reason": "现场授权放行",
  "durationSeconds": 30,
  "operator": "admin"
}
```

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "命令已接收",
  "data": {
    "commandId": "cmd_202605060001",
    "targetId": "door_r01_001",
    "targetType": "door",
    "command": "open",
    "status": "accepted",
    "operator": "admin",
    "createdAt": "2026-05-06T14:30:00+08:00"
  }
}
```

### 5.3 车辆道闸控制

`POST /api/vehicle/lanes/{laneId}/command`

```json
{
  "command": "open",
  "reason": "车辆授权通行",
  "operator": "admin"
}
```

### 5.4 告警动作

`POST /api/alarms/{alarmId}/actions`

```json
{
  "action": "ack",
  "comment": "已确认，通知现场处理",
  "operator": "admin"
}
```

### 5.5 事件关闭

`PATCH /api/events/{eventId}/close`

```json
{
  "result": "resolved",
  "comment": "现场确认已恢复",
  "operator": "admin"
}
```

### 5.6 火车道模式切换

`POST /api/railway/mode`

```json
{
  "mode": "manual",
  "reason": "现场检修",
  "operator": "admin"
}
```

### 5.7 巡检任务创建

`POST /api/v1/inspection/create-task`

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

## 6. 接口清单

### 6.1 基础接口

| 方法 | 路径 | Query/Path | 返回 |
|---|---|---|---|
| `GET` | `/` | 无 | 根路径信息 |
| `GET` | `/health` | 无 | 健康检查 |
| `GET` | `/api` | 无 | API 根信息 |
| `GET` | `/api/info` | 无 | `ApiResponse<ApiInfo>` |
| `GET` | `/api/test` | 无 | 测试连接 |
| `GET` | `/api/auth/me` | 无 | `ApiResponse<CurrentUser>` |

### 6.2 Nacos 配置

| 方法 | 路径 | Query/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/nacos/config` | `dataId, group, tenant, field, pageNo, pageSize` | 单配置或配置列表 |
| `POST` | `/api/nacos/config` | `PublishConfigRequest` | 发布结果 |

### 6.3 大屏、区域、设备

| 方法 | 路径 | Query/Path | 返回 |
|---|---|---|---|
| `GET` | `/api/dashboard/overview` | 无 | `ApiResponse<DashboardOverview>` |
| `GET` | `/api/overview` | 无 | 旧概览兼容 |
| `GET` | `/api/areas` | `includeDisabled` | `ApiResponse<Area[]>` |
| `GET` | `/api/area/{area_id}` | `area_id` | `ApiResponse<AreaDetail>` |
| `GET` | `/api/areas/{areaId}/summary` | `areaId` | `ApiResponse<AreaSummary>` |
| `GET` | `/api/devices` | 无 | 旧设备列表兼容 |
| `GET` | `/api/devices/list` | `areaId, deviceType, onlineStatus, keyword, page, pageSize` | `ApiResponse<PageResult<Device>>` |
| `GET` | `/api/devices/{deviceId}` | `deviceId` | `ApiResponse<DeviceDetail>` |
| `GET` | `/api/device-status/options` | `regionId` | 裸 JSON：`DeviceStatusOptions` |
| `GET` | `/api/device-status/summary` | `regionId, deviceType` | 裸 JSON：`DeviceStatusSummary` |
| `GET` | `/api/device-status/records` | `regionId, deviceType, dataId, field` | 裸 JSON：`DeviceStatusRecords` |

### 6.4 门禁

| 方法 | 路径 | Query/Path/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/access/doors` | `areaId, status, onlineStatus, page, pageSize` | `ApiResponse<PageResult<Door>>` |
| `GET` | `/api/access/doors/{doorId}` | `doorId` | `ApiResponse<DoorDetail>` |
| `POST` | `/api/access/doors/{doorId}/command` | `DoorCommandRequest` | `ApiResponse<CommandResult>` |
| `GET` | `/api/access/pass-records` | `areaId, doorId, personName, cardNo, result, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<AccessPassRecord>>` |

### 6.5 车辆

| 方法 | 路径 | Query/Path/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/vehicle/lanes` | `areaId, onlineStatus, barrierStatus, page, pageSize` | `ApiResponse<PageResult<VehicleLane>>` |
| `POST` | `/api/vehicle/lanes/{laneId}/command` | `VehicleCommandRequest` | `ApiResponse<CommandResult>` |
| `GET` | `/api/vehicle/pass-records` | `areaId, laneId, plateNo, direction, result, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<VehiclePassRecord>>` |

### 6.6 火车道

| 方法 | 路径 | Query/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/railway/status` | 无 | `ApiResponse<RailwayStatus>` |
| `POST` | `/api/railway/mode` | `RailwayModeRequest` | `ApiResponse<CommandResult>` |
| `GET` | `/api/railway/linkage-records` | `status, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<RailwayLinkageRecord>>` |

### 6.7 告警、事件、报警设备

| 方法 | 路径 | Query/Path/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/alarms` | `areaId, severity, status, alarmType, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<Alarm>>` |
| `GET` | `/api/alarms/{alarmId}` | `alarmId` | `ApiResponse<AlarmDetail>` |
| `POST` | `/api/alarms/{alarmId}/actions` | `AlarmActionRequest` | `ApiResponse<ActionResult>` |
| `GET` | `/api/events` | `areaId, eventType, status, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<Event>>` |
| `GET` | `/api/events/{eventId}` | `eventId` | `ApiResponse<EventDetail>` |
| `PATCH` | `/api/events/{eventId}/close` | `EventCloseRequest` | `ApiResponse<ActionResult>` |
| `GET` | `/api/alarm-devices` | `areaId, onlineStatus` | `ApiResponse<AlarmDevice[]>` |
| `POST` | `/api/alarm-devices/{deviceId}/command` | `deviceId` | `ApiResponse<CommandResult>` |
| `GET` | `/api/alarm-devices/{deviceId}/records` | `deviceId, startTime, endTime` | `ApiResponse<AlarmDeviceRecord[]>` |
| `GET` | `/api/alerts` | 无 | 旧告警兼容 |

### 6.8 视频

| 方法 | 路径 | Query/Path/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/video/cameras` | `areaId, onlineStatus, cameraType` | `ApiResponse<Camera[]>` |
| `GET` | `/api/video/cameras/{cameraId}/stream-url` | `cameraId, protocol, expireSeconds` | `ApiResponse<StreamUrl>` |
| `GET` | `/api/video/recordings` | `cameraId, startTime, endTime` | `ApiResponse<VideoRecording[]>` |
| `GET` | `/api/video/evidence` | `alarmId, eventId, cameraId, page, pageSize` | `ApiResponse<PageResult<Evidence>>` |
| `GET` | `/api/video/evidence/{evidenceId}` | `evidenceId` | `ApiResponse<EvidenceDetail>` |
| `POST` | `/api/video/evidence/export` | 导出条件 | `ApiResponse<ExportTask>` |

### 6.9 AI

| 方法 | 路径 | Query/Path | 返回 |
|---|---|---|---|
| `GET` | `/api/ai/rules` | 无 | `ApiResponse<AiRule[]>` |
| `PATCH` | `/api/ai/rules/{ruleId}` | `ruleId, enabled, threshold` | `ApiResponse<AiRule>` |
| `GET` | `/api/ai/detections` | `ruleId, minConfidence, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<AiDetection>>` |

### 6.10 报表和审计

| 方法 | 路径 | Query/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/reports/alarm-statistics` | `startTime, endTime, groupBy` | `ApiResponse<AlarmStatistics>` |
| `GET` | `/api/reports/device-status` | `startTime, endTime` | `ApiResponse<DeviceStatusReport>` |
| `GET` | `/api/reports/pass-statistics` | `startTime, endTime` | `ApiResponse<PassStatistics>` |
| `GET` | `/api/reports/vehicle-statistics` | `startTime, endTime` | `ApiResponse<VehicleStatistics>` |
| `POST` | `/api/reports/export` | 导出条件 | `ApiResponse<ExportTask>` |
| `GET` | `/api/audit/logs` | `operator, action, targetType, targetId, startTime, endTime, page, pageSize` | `ApiResponse<PageResult<AuditLog>>` |

### 6.11 测量和巡检

| 方法 | 路径 | Query/Path/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/tree-menu` | 无 | `ApiResponse<TreeMenu>` |
| `GET` | `/api/latest-measurements` | `since` | `ApiResponse<LatestMeasurements>` |
| `GET` | `/api/point/{point_id}/latest-measurement` | `point_id` | `ApiResponse<Measurement>` |
| `GET` | `/api/point/{point_id}/history-measurements` | `point_id, days, start_date, end_date` | `ApiResponse<Measurement[]>` |
| `GET` | `/api/premade-point/{premade_point_id}/latest-image` | `premade_point_id` | `ApiResponse<ImageInfo>` |
| `GET` | `/api/v1/inspection/list` | `status, page, per_page, start_date, end_date` | `ApiResponse<PageResult<InspectionTask>>` |
| `GET` | `/api/v1/inspection/tasks` | `status, page, per_page, start_date, end_date` | `ApiResponse<PageResult<InspectionTask>>` |
| `POST` | `/api/v1/inspection/create-task` | `CreateTaskRequest` | `ApiResponse<InspectionTask>` |
| `POST` | `/api/v1/inspection/start-task/{task_id}` | `task_id` | `ApiResponse<ActionResult>` |
| `POST` | `/api/v1/inspection/cancel-task/{task_id}` | `task_id` | `ApiResponse<ActionResult>` |
| `GET` | `/api/v1/inspection/task/{task_id}` | `task_id` | `ApiResponse<InspectionTaskDetail>` |
| `DELETE` | `/api/v1/inspection/tasks/{task_id}` | `task_id` | `ApiResponse<ActionResult>` |

### 6.12 硬件状态机模拟器

该模块用于在真实硬件未接入前模拟各类传感器、门禁、道闸、摄像机、报警器状态。

| 方法 | 路径 | Query/Path/Body | 返回 |
|---|---|---|---|
| `GET` | `/api/simulator/summary` | 无 | `ApiResponse<SimulatorSummary>` |
| `GET` | `/api/simulator/devices` | `areaId, deviceType, onlineStatus` | `ApiResponse<PageLike<HardwareDevice>>` |
| `GET` | `/api/simulator/devices/{deviceId}` | `deviceId` | `ApiResponse<HardwareDevice>` |
| `POST` | `/api/simulator/tick` | `steps` | `ApiResponse<SimulatorTickResult>` |
| `POST` | `/api/simulator/devices/{deviceId}/command` | `HardwareCommandRequest` | `ApiResponse<HardwareCommandResult>` |

支持命令：

| 命令 | 说明 |
|---|---|
| `recover` | 恢复在线正常 |
| `offline` | 强制离线 |
| `fault` | 强制故障 |
| `maintenance` | 强制维护 |
| `set_alarm` | 强制告警 |
| `clear_alarm` | 清除告警 |
| `open` | 打开 |
| `close` | 关闭 |
| `lock` | 锁定 |
| `unlock` | 解锁 |
| `reset` | 复位 |

## 7. 主要数据模型

### 7.1 通用模型

```ts
interface ApiResponse<T> {
  code: number;
  success: boolean;
  message: string;
  data: T;
  traceId?: string;
}

interface PageResult<T> {
  items: T[];
  page: number;
  pageSize: number;
  total: number;
}

interface OptionItem {
  id: string;
  name: string;
}

interface CommandResult {
  commandId: string;
  targetId: string;
  targetType: string;
  command: string;
  status: "accepted" | "running" | "success" | "failed";
  operator: string;
  createdAt: string;
}
```

### 7.2 区域和设备

```ts
interface Area {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  sort: number;
}

interface AreaSummary {
  areaId: string;
  areaName: string;
  peopleCount: number;
  vehicleCount: number;
  onlineDeviceCount: number;
  offlineDeviceCount: number;
  activeAlarmCount: number;
  updatedAt: string;
}

interface Device {
  id: string;
  name: string;
  deviceType: string;
  deviceTypeName: string;
  areaId: string;
  areaName: string;
  onlineStatus: "online" | "offline" | "fault" | "unknown";
  lastHeartbeatAt?: string;
}
```

### 7.3 门禁

```ts
interface Door {
  id: string;
  name: string;
  areaId: string;
  areaName: string;
  doorStatus: "open" | "closed" | "locked" | "opening" | "closing" | "fault";
  onlineStatus: "online" | "offline" | "fault" | "unknown";
  interlockGroupId?: string | null;
  lastHeartbeatAt?: string;
  lastEventAt?: string;
}

interface AccessPassRecord {
  id: string;
  personId?: string;
  personName: string;
  doorId: string;
  doorName: string;
  areaName: string;
  method: string;
  result: "allowed" | "denied" | "manual" | "timeout" | "unknown";
  reason?: string;
  occurredAt: string;
}
```

### 7.4 车辆

```ts
interface VehicleLane {
  id: string;
  name: string;
  areaId: string;
  direction: "in" | "out" | "bidirectional";
  barrierStatus: "open" | "closed" | "opening" | "closing" | "fault";
  recognizerStatus: "online" | "offline" | "fault" | "unknown";
  onlineStatus: "online" | "offline" | "fault" | "unknown";
  lastPlateNo?: string;
  lastEventAt?: string;
}

interface VehiclePassRecord {
  id: string;
  laneId: string;
  laneName: string;
  areaName: string;
  plateNo: string;
  direction: "in" | "out";
  result: "allowed" | "denied" | "manual" | "timeout" | "unknown";
  reason?: string;
  occurredAt: string;
}
```

### 7.5 火车道

```ts
interface RailwayStatus {
  railStatus: "idle" | "approaching" | "passing" | "blocked";
  signalStatus: "none" | "green" | "yellow" | "red";
  approachEtaSeconds?: number | null;
  isIsolationActive: boolean;
  activeLinkageId?: string | null;
  doorClosedCount: number;
  doorOpenCount: number;
  alarmActiveCount: number;
  updatedAt: string;
}

interface RailwayLinkageRecord {
  id: string;
  status: "started" | "running" | "finished" | "failed";
  triggerType: string;
  startedAt: string;
  finishedAt?: string;
  result?: string;
}
```

### 7.6 告警和事件

```ts
interface Alarm {
  id: string;
  type: string;
  alarmType: string;
  severity: "low" | "medium" | "high" | "critical";
  status: "pending" | "processing" | "closed";
  areaId: string;
  areaName: string;
  deviceId?: string;
  deviceName?: string;
  title: string;
  content: string;
  occurredAt: string;
  updatedAt?: string;
}

interface Event {
  id: string;
  type: string;
  eventType: string;
  status: "pending" | "processing" | "closed";
  areaId: string;
  areaName: string;
  deviceId?: string;
  deviceName?: string;
  title: string;
  content: string;
  occurredAt: string;
  closedAt?: string;
}
```

### 7.7 视频和 AI

```ts
interface Camera {
  id: string;
  name: string;
  areaId: string;
  areaName: string;
  cameraType: "fixed" | "ptz" | "thermal";
  onlineStatus: "online" | "offline" | "fault" | "unknown";
  resolution?: string;
  position?: string;
}

interface StreamUrl {
  cameraId: string;
  protocol: "hls" | "flv" | "rtsp";
  url: string;
  expireAt: string;
}

interface AiRule {
  ruleId: string;
  name: string;
  enabled: boolean;
  targetAccuracy: number;
  actualAccuracy: number;
  threshold: number;
}

interface AiDetection {
  id: string;
  ruleId: string;
  ruleName: string;
  confidence: number;
  status: "new" | "confirmed" | "ignored";
  imageUrl?: string;
  occurredAt: string;
}
```

### 7.8 硬件状态机模拟器

```ts
interface HardwareDevice {
  id: string;
  name: string;
  areaId: string;
  areaName: string;
  deviceType: string;
  deviceTypeName: string;
  onlineStatus: "online" | "offline" | "fault" | "maintenance";
  workStatus: string;
  alarmStatus: "normal" | "warning" | "alarm";
  value?: number | null;
  unit?: string | null;
  battery?: number | null;
  signal?: number | null;
  sequence: number;
  lastHeartbeatAt: string;
  lastChangedAt: string;
  metadata: Record<string, unknown>;
}

interface HardwareCommandRequest {
  command: string;
  reason?: string;
  operator?: string;
  payload?: Record<string, unknown>;
}

interface SimulatorSummary {
  tick: number;
  totalDevices: number;
  onlineDevices: number;
  offlineDevices: number;
  faultDevices: number;
  alarmDevices: number;
  onlineRate: number;
  updatedAt: string;
}
```

## 8. 权限规则

### 8.1 权限码

| 权限码 | 覆盖接口 |
|---|---|
| `dashboard:read` | `/api/dashboard/overview` |
| `area:read` | `/api/areas*`、`/api/area/*` |
| `device:read` | `/api/devices*`、`/api/device-status/*` |
| `access:read` | `GET /api/access/*` |
| `access:command` | `POST /api/access/doors/{doorId}/command` |
| `vehicle:read` | `GET /api/vehicle/*` |
| `vehicle:command` | `POST /api/vehicle/lanes/{laneId}/command` |
| `railway:read` | `GET /api/railway/*` |
| `railway:command` | `POST /api/railway/mode` |
| `alarm:read` | `GET /api/alarms*`、`GET /api/alarm-devices*` |
| `alarm:action` | `POST /api/alarms/{alarmId}/actions`、`POST /api/alarm-devices/{deviceId}/command` |
| `event:read` | `GET /api/events*` |
| `event:close` | `PATCH /api/events/{eventId}/close` |
| `video:read` | `GET /api/video/*` |
| `video:export` | `POST /api/video/evidence/export` |
| `ai:read` | `GET /api/ai/*` |
| `ai:write` | `PATCH /api/ai/rules/{ruleId}` |
| `report:read` | `GET /api/reports/*` |
| `report:export` | `POST /api/reports/export` |
| `audit:read` | `GET /api/audit/logs` |
| `nacos:read` | `GET /api/nacos/config` |
| `nacos:write` | `POST /api/nacos/config` |

### 8.2 控制类接口要求

控制类接口必须记录：

| 字段 | 说明 |
|---|---|
| `operator` | 操作人 |
| `reason` | 操作原因 |
| `targetId` | 操作目标 |
| `command/action` | 具体动作 |
| `createdAt` | 操作时间 |
| `result` | 执行结果 |

无权限返回 `403`，目标不存在返回 `404`，状态冲突返回 `409`。

## 9. 前端统一解析

前端调用时按以下规则解析：

```ts
export function unwrapApiResponse(response: any) {
  if (response && typeof response === "object" && "success" in response && "data" in response) {
    if (!response.success) {
      throw new Error(response.message || "请求失败");
    }
    return response.data;
  }

  return response;
}
```

适配 `8083` 设备状态：

```ts
const options = await fetch("/api/device-status/options").then(r => r.json());

const regions = Array.isArray(options.regions)
  ? options.regions.map((item: any) => typeof item === "string" ? item : item.name)
  : [];

const devices = Array.isArray(options.devices)
  ? options.devices.map((item: any) => typeof item === "string" ? item : item.name)
  : [];
```

## 10. 最小验收接口

第一批必须可用：

| 方法 | 路径 | 验收点 |
|---|---|---|
| `GET` | `/api/health` 或 `/health` | 服务探活成功 |
| `GET` | `/api/info` | 返回项目名称和版本 |
| `GET` | `/api/dashboard/overview` | 8083 大屏概览可取数 |
| `GET` | `/api/device-status/options` | 区域/设备筛选项可取数 |
| `GET` | `/api/device-status/summary` | 在线率和汇总可取数 |
| `GET` | `/api/device-status/records` | 设备状态图表可取数 |
| `GET` | `/api/areas` | 区域基础数据可取数 |
| `GET` | `/api/devices/list` | 设备列表可分页 |
| `GET` | `/api/access/doors` | 门禁列表可分页 |
| `GET` | `/api/vehicle/lanes` | 车辆道闸列表可分页 |
| `GET` | `/api/railway/status` | 火车道状态可取数 |
| `GET` | `/api/alarms` | 告警列表可分页 |
| `GET` | `/api/events` | 事件列表可分页 |

对应 curl：

```bash
curl "http://101.43.49.78:8082/api/info"
curl "http://101.43.49.78:8082/api/dashboard/overview"
curl "http://101.43.49.78:8082/api/device-status/options"
curl "http://101.43.49.78:8082/api/device-status/summary"
curl "http://101.43.49.78:8082/api/device-status/records"
curl "http://101.43.49.78:8082/api/areas"
curl "http://101.43.49.78:8082/api/devices/list"
curl "http://101.43.49.78:8082/api/access/doors"
curl "http://101.43.49.78:8082/api/vehicle/lanes"
curl "http://101.43.49.78:8082/api/railway/status"
curl "http://101.43.49.78:8082/api/alarms"
curl "http://101.43.49.78:8082/api/events"
```
