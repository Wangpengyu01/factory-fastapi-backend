# 技术协议功能对照与缺口 API 补充文档

更新时间：`2026-04-27`

## 1. 文档定位

本文用于把《中厚板卷厂成品库区域全封闭改造项目（电气部分）技术协议》中的业务功能，和当前线上接口 `http://101.43.49.78:8082/docs`、前端 `http://101.43.49.78:8083` 做对照。

本文分两部分：

- 第一部分：协议功能点与现有 API 覆盖情况对照表
- 第二部分：缺口 API 补充协议，供后端后续实现、前端联调使用

边界说明：

- “已存在”以 `http://101.43.49.78:8082/openapi.json` 在 `2026-04-27` 可见路由为准。
- 本文新增的缺口 API 是补充协议，不代表当前后端已经实现。
- 当前线上后端返回结构混用裸 JSON 与 `code/success/message/data` 包装；本文建议后续新接口统一使用包装结构。

## 2. 当前线上 API 概况

### 2.1 与本项目大屏直接相关的现有接口

| 方法 | 路径 | 当前作用 | 备注 |
|---|---|---|---|
| `GET` | `/api/overview` | 首页概览数据 | 裸 JSON，字段较少 |
| `GET` | `/api/dashboard/overview` | 大屏聚合概览 | 已有 `code/success/data` 包装 |
| `GET` | `/api/area/{area_id}` | 区域详情 | 需要确认实际字段是否满足协议 |
| `GET` | `/api/devices` | 设备总览 | 偏统计，不含设备明细控制 |
| `GET` | `/api/alarms` | 告警列表 | 当前无详情、处置、闭环接口 |
| `GET` | `/api/events` | 事件列表 | 当前无详情、证据、闭环接口 |
| `GET` | `/api/alerts` | 风险预警列表 | 当前无规则与处置接口 |
| `GET` | `/api/device-status/options` | 设备状态筛选项 | 返回区域与设备类型 |
| `GET` | `/api/device-status/summary` | 设备状态汇总 | 支持 `regionId`、`deviceType` |
| `GET` | `/api/device-status/records` | 设备状态记录 | 支持 `regionId`、`deviceType`、`dataId`、`field` |
| `GET` | `/api/nacos/config` | 读取 Nacos 配置 | 配置桥能力 |
| `POST` | `/api/nacos/config` | 发布 Nacos 配置 | 需要 `X-Publish-Key` |

### 2.2 线上存在但不是本协议核心的接口

| 方法 | 路径 | 判断 |
|---|---|---|
| `GET` | `/api/tree-menu` | 更像检测/巡检业务树，不是协议里的成品库封闭管控核心接口 |
| `GET` | `/api/point/{point_id}/latest-measurement` | 轨道/测点检测类接口 |
| `GET` | `/api/point/{point_id}/history-measurements` | 轨道/测点检测类接口 |
| `GET` | `/api/latest-measurements` | 轨道/测点检测类接口 |
| `GET` | `/api/premade-point/{premade_point_id}/latest-image` | 轨道/测点检测类接口 |
| `POST` | `/api/v1/inspection/create-task` | 巡检任务管理 |
| `POST` | `/api/v1/inspection/start-task/{task_id}` | 巡检任务管理 |
| `GET` | `/api/v1/inspection/tasks` | 巡检任务管理 |
| `GET` | `/api/v1/inspection/list` | 巡检任务管理 |
| `GET` | `/api/v1/inspection/task/{task_id}` | 巡检任务管理 |
| `POST` | `/api/v1/inspection/cancel-task/{task_id}` | 巡检任务管理 |
| `DELETE` | `/api/v1/inspection/tasks/{task_id}` | 巡检任务管理 |

### 2.3 需要优先修正的线上展示问题

| 问题 | 影响 | 建议 |
|---|---|---|
| `/api/info` 返回名称仍是“轨道健康检测系统API” | 与“成品库区域全封闭改造项目”不一致，验收或汇报时容易被质疑 | 改为“成品库区域全封闭管控系统 API”或类似项目名称 |
| 响应结构不统一 | 前端适配成本高，也不利于文档统一 | 新增接口统一 `code/success/message/data` |
| 告警、事件接口只有列表 | 不能支撑协议要求的“事件留痕、闭环管理、证据留存” | 补详情、处置、关闭、证据关联接口 |
| 门禁、道闸、火车道联动缺少控制类接口 | 只能展示，不能体现“准入受控、联动管控、应急模式” | 补门禁/道闸/火车联动控制接口 |

## 3. 协议功能点与 API 覆盖对照表

| 序号 | 协议功能点 | 协议要求摘要 | 现有 API | 覆盖状态 | 主要缺口 | 建议补充 API | 优先级 |
|---:|---|---|---|---|---|---|---|
| 1 | 大屏运行总览 | 展示在线门禁、区域人数、车辆在场、火车道状态、告警汇总 | `/api/overview`、`/api/dashboard/overview` | 部分覆盖 | 字段口径需固定；缺少更新时间、数据源状态、异常降级信息 | 增强 `/api/dashboard/overview` | P0 |
| 2 | 区域封闭管理 | A 区、F 区、L 区、成品库、火车道等区域封闭状态与风险概览 | `/api/area/{area_id}` | 部分覆盖 | 缺区域列表、区域下门禁/道闸/摄像头/告警联动汇总 | `GET /api/areas`、`GET /api/areas/{areaId}/summary` | P0 |
| 3 | 设备状态展示 | 门禁、道闸、摄像机、声光报警、烟感温感、NVR、AI 服务器、大屏在线离线 | `/api/device-status/options`、`/api/device-status/summary`、`/api/device-status/records` | 基本覆盖 | 缺设备明细、设备健康状态、最后心跳、故障原因 | `GET /api/devices/list`、`GET /api/devices/{deviceId}` | P0 |
| 4 | 人员准入与联锁门禁 | 授权准入、未授权拦截、门状态可视、事件留痕 | 无专用接口 | 未覆盖 | 缺门禁列表、门状态、远程控制、人员通行记录 | `/api/access/*` | P0 |
| 5 | 人脸识别终端与权限 | 人脸识别、黑白名单、通行记录存储 | 无专用接口 | 未覆盖 | 缺人员权限、识别记录、名单同步 | `/api/access/permissions`、`/api/access/pass-records` | P0 |
| 6 | 车辆进出与道闸 | 车辆识别、预约/许可、未授权禁止进入、应急放行 | 只有统计类字段 | 未覆盖 | 缺车牌识别记录、许可管理、道闸状态、道闸控制 | `/api/vehicle/*` | P0 |
| 7 | 火车道联动管控 | 提前 3-5 分钟接收火车信号，自动执行隔离和告警，火车离开后恢复 | 只有 `railStatus` 展示字段 | 严重不足 | 缺火车信号接入、联动状态、联动记录、应急/维护模式 | `/api/railway/*` | P0 |
| 8 | 声光报警与行车提醒 | 门禁/管控/火车联动事件触发声光报警和投射灯提醒 | 告警列表部分体现 | 未覆盖控制 | 缺报警器状态、触发/解除、联动记录 | `/api/alarm-devices/*` | P1 |
| 9 | 告警与事件闭环 | 实时预警、处置闭环、事件留痕、统计分析 | `/api/alarms`、`/api/events`、`/api/alerts` | 部分覆盖 | 缺详情、确认、处置、关闭、证据、操作日志 | 增强 `/api/alarms`、`/api/events` | P0 |
| 10 | 视频监控与 AI 分析 | 摄像机在线、视频 AI 识别、抓拍取证、告警推送、证据留存 | 只有设备统计和告警列表 | 未覆盖 | 缺摄像机列表、流地址、录像查询、证据查询、AI 规则 | `/api/video/*`、`/api/ai/*` | P1 |
| 11 | 录像与证据保存 | 视频保存不少于 90 天，报警证据后台保存不少于 180 天 | 无 | 未覆盖 | 缺录像检索、证据检索、导出、保存周期字段 | `/api/video/recordings`、`/api/video/evidence` | P1 |
| 12 | 报表与统计 | 设备状态、告警查询、统计报表、权限管理 | 只有概览类接口 | 部分覆盖 | 缺按时间、区域、设备类型维度统计和导出 | `/api/reports/*` | P1 |
| 13 | 权限与审计 | 平台权限管理、操作日志、应急操作留痕 | 无 | 未覆盖 | 缺用户、角色、审计日志、操作追踪 | `/api/auth/me`、`/api/audit/logs` | P1 |
| 14 | 软件与配置版本管理 | 配置文件、参数表、账号权限说明、系统备份可恢复 | `/api/nacos/config` | 部分覆盖 | 缺配置版本、回滚、备份记录 | `/api/config/versions`、`/api/config/backups` | P2 |
| 15 | 调试与验收 | 联调记录、测试报告、问题闭环清单 | 巡检任务接口可借用但不匹配 | 未覆盖 | 缺验收问题单和测试记录接口 | `/api/acceptance/*` | P2 |

## 4. 缺口 API 补充协议

### 4.1 通用约定

#### Base URL

```http
http://101.43.49.78:8082
```

#### 新增接口统一响应结构

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {},
  "traceId": "optional-trace-id"
}
```

#### 分页响应结构

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 0
}
```

#### 通用时间格式

- 时间字段统一使用 ISO-8601 字符串。
- 建议使用北京时间，例如：`2026-04-27T20:00:00+08:00`。

#### 通用状态枚举

| 字段 | 建议枚举 | 说明 |
|---|---|---|
| `onlineStatus` | `online`、`offline`、`fault`、`unknown` | 设备在线状态 |
| `doorStatus` | `open`、`closed`、`locked`、`fault`、`unknown` | 门禁/联锁门状态 |
| `barrierStatus` | `open`、`closed`、`opening`、`closing`、`fault`、`unknown` | 道闸状态 |
| `railStatus` | `idle`、`approaching`、`occupied`、`leaving`、`fault`、`maintenance` | 火车道状态 |
| `alarmStatus` | `new`、`acknowledged`、`processing`、`closed`、`ignored` | 告警状态 |
| `severity` | `low`、`medium`、`high`、`critical` | 告警等级 |
| `commandStatus` | `accepted`、`rejected`、`executing`、`done`、`failed` | 控制命令状态 |

## 5. P0 必补 API

P0 是支撑协议核心演示和联调的最低集合，建议优先落地。

### 5.1 区域接口

#### 5.1.1 获取区域列表

```http
GET /api/areas
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `includeDisabled` | `boolean` | 否 | 是否包含停用区域 |

响应：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "items": [
      {
        "id": "r01",
        "name": "A区",
        "type": "production_area",
        "enabled": true,
        "sort": 1
      }
    ]
  }
}
```

#### 5.1.2 获取区域综合状态

```http
GET /api/areas/{areaId}/summary
```

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `area` | `object` | 区域基础信息 |
| `peopleCount` | `number` | 当前区域人数 |
| `vehicleCount` | `number` | 当前区域车辆数 |
| `doorSummary` | `object` | 门禁在线、离线、开门、关门数量 |
| `cameraSummary` | `object` | 摄像机在线、离线数量 |
| `alarmSummary` | `object` | 当前告警汇总 |
| `riskLevel` | `string` | 区域风险等级 |
| `updatedAt` | `string` | 更新时间 |

### 5.2 门禁与人员准入接口

#### 5.2.1 获取门禁/联锁门列表

```http
GET /api/access/doors
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 ID |
| `status` | `string` | 否 | `open`、`closed`、`locked`、`fault` |
| `onlineStatus` | `string` | 否 | `online`、`offline`、`fault` |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

响应记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 门禁 ID |
| `name` | `string` | 门禁名称 |
| `areaId` | `string` | 所属区域 |
| `areaName` | `string` | 所属区域名称 |
| `doorStatus` | `string` | 门状态 |
| `onlineStatus` | `string` | 在线状态 |
| `interlockGroupId` | `string` | 联锁组 ID |
| `lastHeartbeatAt` | `string` | 最近心跳时间 |
| `lastEventAt` | `string` | 最近事件时间 |

#### 5.2.2 获取门禁详情

```http
GET /api/access/doors/{doorId}
```

详情应包含：

- 门禁基础信息
- 当前门状态
- 控制器状态
- 联锁组状态
- 最近通行记录
- 最近告警记录
- 最近控制命令记录

#### 5.2.3 下发门禁控制命令

```http
POST /api/access/doors/{doorId}/command
```

Body：

```json
{
  "command": "open",
  "reason": "现场授权放行",
  "durationSeconds": 30,
  "operator": "admin"
}
```

`command` 建议枚举：

| 命令 | 说明 |
|---|---|
| `open` | 开门 |
| `close` | 关门 |
| `lock` | 锁定 |
| `unlock` | 解锁 |
| `emergency_open` | 应急开门 |
| `reset` | 复位 |

响应：

```json
{
  "code": 200,
  "success": true,
  "message": "命令已接收",
  "data": {
    "commandId": "cmd_202604270001",
    "doorId": "door_a_001",
    "command": "open",
    "status": "accepted",
    "createdAt": "2026-04-27T20:00:00+08:00"
  }
}
```

#### 5.2.4 获取人员通行记录

```http
GET /api/access/pass-records
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 |
| `doorId` | `string` | 否 | 门禁 |
| `personName` | `string` | 否 | 人员姓名 |
| `cardNo` | `string` | 否 | 卡号 |
| `result` | `string` | 否 | `allowed`、`denied` |
| `startTime` | `string` | 否 | 开始时间 |
| `endTime` | `string` | 否 | 结束时间 |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

响应记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 记录 ID |
| `personId` | `string` | 人员 ID |
| `personName` | `string` | 人员姓名 |
| `doorId` | `string` | 门禁 ID |
| `doorName` | `string` | 门禁名称 |
| `areaName` | `string` | 区域 |
| `method` | `string` | `face`、`card`、`manual` |
| `result` | `string` | `allowed`、`denied` |
| `reason` | `string` | 放行或拒绝原因 |
| `snapshotUrl` | `string` | 抓拍图片 |
| `occurredAt` | `string` | 发生时间 |

#### 5.2.5 人员权限管理

```http
GET /api/access/permissions
POST /api/access/permissions
PATCH /api/access/permissions/{permissionId}
DELETE /api/access/permissions/{permissionId}
```

`POST /api/access/permissions` Body：

```json
{
  "personId": "p001",
  "personName": "张三",
  "cardNo": "10001",
  "faceImageUrl": "https://example.com/face.jpg",
  "areaIds": ["r01", "r02"],
  "doorIds": ["door_a_001"],
  "validFrom": "2026-04-27T00:00:00+08:00",
  "validTo": "2026-12-31T23:59:59+08:00",
  "enabled": true
}
```

### 5.3 车辆与道闸接口

#### 5.3.1 获取道闸/车道列表

```http
GET /api/vehicle/lanes
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 |
| `onlineStatus` | `string` | 否 | 在线状态 |
| `barrierStatus` | `string` | 否 | 道闸状态 |

响应记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 车道 ID |
| `name` | `string` | 车道名称 |
| `areaId` | `string` | 区域 ID |
| `direction` | `string` | `in`、`out`、`bidirectional` |
| `barrierStatus` | `string` | 道闸状态 |
| `recognizerStatus` | `string` | 车牌识别设备状态 |
| `onlineStatus` | `string` | 在线状态 |
| `lastPlateNo` | `string` | 最近识别车牌 |
| `lastEventAt` | `string` | 最近事件时间 |

#### 5.3.2 下发道闸控制命令

```http
POST /api/vehicle/lanes/{laneId}/command
```

Body：

```json
{
  "command": "open",
  "reason": "授权车辆放行",
  "operator": "admin"
}
```

`command` 建议枚举：

| 命令 | 说明 |
|---|---|
| `open` | 抬杆 |
| `close` | 落杆 |
| `lock_open` | 常开 |
| `lock_closed` | 常闭 |
| `reset` | 复位 |

#### 5.3.3 获取车辆通行记录

```http
GET /api/vehicle/pass-records
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 |
| `laneId` | `string` | 否 | 车道 |
| `plateNo` | `string` | 否 | 车牌号 |
| `direction` | `string` | 否 | `in`、`out` |
| `result` | `string` | 否 | `allowed`、`denied` |
| `startTime` | `string` | 否 | 开始时间 |
| `endTime` | `string` | 否 | 结束时间 |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

#### 5.3.4 车辆预约/许可管理

```http
GET /api/vehicle/permits
POST /api/vehicle/permits
PATCH /api/vehicle/permits/{permitId}
DELETE /api/vehicle/permits/{permitId}
```

`POST /api/vehicle/permits` Body：

```json
{
  "plateNo": "苏A12345",
  "driverName": "李四",
  "driverPhone": "13800000000",
  "areaIds": ["r04"],
  "validFrom": "2026-04-27T08:00:00+08:00",
  "validTo": "2026-04-27T18:00:00+08:00",
  "permitType": "appointment",
  "remark": "成品库装卸作业"
}
```

### 5.4 火车道联动接口

#### 5.4.1 获取火车道状态

```http
GET /api/railway/status
```

响应：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "railStatus": "idle",
    "signalStatus": "none",
    "approachEtaSeconds": null,
    "isIsolationActive": false,
    "activeLinkageId": null,
    "doorClosedCount": 6,
    "doorOpenCount": 0,
    "alarmActiveCount": 0,
    "updatedAt": "2026-04-27T20:00:00+08:00"
  }
}
```

#### 5.4.2 接收火车信号事件

```http
POST /api/railway/signals/events
```

用途：对接甲方火车信号来源。协议要求火车进出前 `3-5` 分钟触发联动策略，建议该接口作为信号入口。

Body：

```json
{
  "signalId": "sig_202604270001",
  "direction": "inbound",
  "eventType": "approaching",
  "etaSeconds": 240,
  "source": "train_signal_system",
  "occurredAt": "2026-04-27T20:00:00+08:00",
  "rawPayload": {}
}
```

`eventType` 建议枚举：

| 枚举 | 说明 |
|---|---|
| `approaching` | 火车即将进入 |
| `entered` | 火车已进入 |
| `leaving` | 火车驶离中 |
| `left` | 火车已离开 |
| `cancelled` | 预告取消 |
| `fault` | 信号故障 |

#### 5.4.3 获取火车道联动记录

```http
GET /api/railway/linkage-records
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `status` | `string` | 否 | `running`、`completed`、`failed`、`cancelled` |
| `startTime` | `string` | 否 | 开始时间 |
| `endTime` | `string` | 否 | 结束时间 |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 联动记录 ID |
| `signalId` | `string` | 火车信号 ID |
| `eventType` | `string` | 信号类型 |
| `status` | `string` | 联动状态 |
| `startedAt` | `string` | 开始时间 |
| `finishedAt` | `string` | 完成时间 |
| `closedDoorCount` | `number` | 联动关闭门/道闸数量 |
| `triggeredAlarmCount` | `number` | 联动报警数量 |
| `failedActions` | `array` | 失败动作 |

#### 5.4.4 设置火车道运行模式

```http
POST /api/railway/mode
```

Body：

```json
{
  "mode": "emergency",
  "reason": "现场应急疏散",
  "operator": "admin"
}
```

`mode` 建议枚举：

| 枚举 | 说明 |
|---|---|
| `normal` | 正常模式 |
| `emergency` | 应急模式 |
| `maintenance` | 维护模式 |
| `manual` | 手动模式 |

### 5.5 告警与事件闭环接口

#### 5.5.1 增强告警列表

```http
GET /api/alarms
```

建议在当前接口基础上补充 Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 |
| `deviceId` | `string` | 否 | 设备 |
| `type` | `string` | 否 | 告警类型 |
| `severity` | `string` | 否 | 告警等级 |
| `status` | `string` | 否 | 告警状态 |
| `startTime` | `string` | 否 | 开始时间 |
| `endTime` | `string` | 否 | 结束时间 |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

#### 5.5.2 获取告警详情

```http
GET /api/alarms/{alarmId}
```

详情应包含：

- 告警基础信息
- 关联区域、设备、摄像机
- 关联事件
- 关联证据图片/短视频
- 处置记录
- 操作日志

#### 5.5.3 告警确认/处置/关闭

```http
POST /api/alarms/{alarmId}/actions
```

Body：

```json
{
  "action": "close",
  "comment": "现场确认已恢复",
  "operator": "admin"
}
```

`action` 建议枚举：

| 动作 | 说明 |
|---|---|
| `acknowledge` | 确认告警 |
| `assign` | 指派处理 |
| `process` | 标记处理中 |
| `close` | 关闭 |
| `ignore` | 忽略 |
| `reopen` | 重新打开 |

#### 5.5.4 事件详情与关闭

```http
GET /api/events/{eventId}
PATCH /api/events/{eventId}/close
```

`PATCH /api/events/{eventId}/close` Body：

```json
{
  "result": "已完成处置",
  "comment": "人员已撤离，门禁恢复正常",
  "operator": "admin"
}
```

### 5.6 设备明细接口

#### 5.6.1 获取设备明细列表

```http
GET /api/devices/list
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 |
| `deviceType` | `string` | 否 | 设备类型 |
| `onlineStatus` | `string` | 否 | 在线状态 |
| `keyword` | `string` | 否 | 设备名称或编码 |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

响应记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 设备 ID |
| `name` | `string` | 设备名称 |
| `deviceType` | `string` | 设备类型 |
| `areaId` | `string` | 区域 ID |
| `areaName` | `string` | 区域名称 |
| `onlineStatus` | `string` | 在线状态 |
| `healthStatus` | `string` | 健康状态 |
| `lastHeartbeatAt` | `string` | 最近心跳 |
| `lastFaultAt` | `string` | 最近故障 |
| `vendor` | `string` | 厂商 |
| `model` | `string` | 型号 |

#### 5.6.2 获取设备详情

```http
GET /api/devices/{deviceId}
```

详情应包含：

- 设备基础信息
- 实时状态
- 最近告警
- 最近事件
- 最近控制命令
- 配置参数
- 所属联动关系

## 6. P1 建议补充 API

P1 用于支撑更完整验收，包括视频 AI、证据留存、报表统计、审计。

### 6.1 声光报警设备接口

```http
GET /api/alarm-devices
POST /api/alarm-devices/{deviceId}/command
GET /api/alarm-devices/{deviceId}/records
```

`POST /api/alarm-devices/{deviceId}/command` Body：

```json
{
  "command": "start",
  "durationSeconds": 60,
  "reason": "火车道联动告警",
  "operator": "system"
}
```

`command` 建议枚举：`start`、`stop`、`test`、`reset`。

### 6.2 视频监控接口

#### 6.2.1 获取摄像机列表

```http
GET /api/video/cameras
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 否 | 区域 |
| `onlineStatus` | `string` | 否 | 在线状态 |
| `cameraType` | `string` | 否 | `fixed`、`ptz`、`panorama` |

#### 6.2.2 获取摄像机播放地址

```http
GET /api/video/cameras/{cameraId}/stream-url
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `protocol` | `string` | 否 | `flv`、`hls`、`webrtc`、`rtsp` |
| `expireSeconds` | `integer` | 否 | 播放地址有效期 |

响应：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "cameraId": "cam_a_001",
    "protocol": "hls",
    "url": "https://example.com/live/cam_a_001.m3u8",
    "expiresAt": "2026-04-27T20:10:00+08:00"
  }
}
```

#### 6.2.3 查询录像

```http
GET /api/video/recordings
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `cameraId` | `string` | 是 | 摄像机 ID |
| `startTime` | `string` | 是 | 开始时间 |
| `endTime` | `string` | 是 | 结束时间 |

协议要求：普通录像保存不少于 `90` 天。

#### 6.2.4 查询告警证据

```http
GET /api/video/evidence
GET /api/video/evidence/{evidenceId}
POST /api/video/evidence/export
```

证据记录字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 证据 ID |
| `alarmId` | `string` | 关联告警 |
| `eventId` | `string` | 关联事件 |
| `cameraId` | `string` | 摄像机 |
| `type` | `string` | `image`、`video` |
| `url` | `string` | 访问地址 |
| `capturedAt` | `string` | 抓拍时间 |
| `retentionDays` | `number` | 保存天数 |

协议要求：报警事件及相关证据保存不少于 `180` 天。

### 6.3 AI 识别接口

```http
GET /api/ai/rules
PATCH /api/ai/rules/{ruleId}
GET /api/ai/detections
```

AI 规则建议覆盖：

| 规则类型 | 说明 |
|---|---|
| `person_vehicle_track` | 行人/车辆识别与轨迹分析 |
| `intrusion` | 区域入侵 |
| `loitering` | 区域滞留 |
| `helmet` | 未戴安全帽 |
| `smoking` | 抽烟 |
| `illegal_parking` | 违章停车 |
| `wrong_way` | 逆行 |
| `fatigue` | 驾驶员疲劳 |
| `occlusion` | 摄像头遮挡 |

验收指标建议在规则中显式返回：

```json
{
  "ruleId": "helmet",
  "name": "未戴安全帽识别",
  "enabled": true,
  "targetAccuracy": 95,
  "actualAccuracy": 96.2,
  "threshold": 0.8
}
```

### 6.4 报表接口

```http
GET /api/reports/device-status
GET /api/reports/alarm-statistics
GET /api/reports/pass-statistics
GET /api/reports/vehicle-statistics
POST /api/reports/export
```

#### 6.4.1 告警统计

```http
GET /api/reports/alarm-statistics?startTime=2026-04-01T00:00:00+08:00&endTime=2026-04-27T23:59:59+08:00&groupBy=day
```

`groupBy` 建议枚举：`hour`、`day`、`week`、`month`、`area`、`type`、`severity`。

#### 6.4.2 报表导出

```http
POST /api/reports/export
```

Body：

```json
{
  "reportType": "alarm-statistics",
  "format": "xlsx",
  "filters": {
    "startTime": "2026-04-01T00:00:00+08:00",
    "endTime": "2026-04-27T23:59:59+08:00",
    "areaId": "r04"
  }
}
```

### 6.5 权限与审计接口

```http
GET /api/auth/me
GET /api/audit/logs
```

#### 6.5.1 当前登录用户

```http
GET /api/auth/me
```

响应：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "userId": "u001",
    "username": "admin",
    "displayName": "系统管理员",
    "roles": ["admin"],
    "permissions": [
      "door:control",
      "alarm:close",
      "railway:mode"
    ]
  }
}
```

#### 6.5.2 审计日志

```http
GET /api/audit/logs
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `operator` | `string` | 否 | 操作人 |
| `action` | `string` | 否 | 操作动作 |
| `targetType` | `string` | 否 | 目标类型 |
| `targetId` | `string` | 否 | 目标 ID |
| `startTime` | `string` | 否 | 开始时间 |
| `endTime` | `string` | 否 | 结束时间 |
| `page` | `integer` | 否 | 页码 |
| `pageSize` | `integer` | 否 | 每页数量 |

## 7. P2 运维与验收 API

P2 不影响大屏基础演示，但对最终交付和运维有帮助。

### 7.1 配置版本与备份

```http
GET /api/config/versions
POST /api/config/versions/{versionId}/rollback
GET /api/config/backups
POST /api/config/backups
```

用途：

- 保存平台配置、联动策略、AI 规则、账号权限说明
- 支持配置回滚
- 支持验收后的系统备份记录

### 7.2 验收问题闭环

```http
GET /api/acceptance/issues
POST /api/acceptance/issues
PATCH /api/acceptance/issues/{issueId}
GET /api/acceptance/test-records
POST /api/acceptance/test-records
```

用途：

- 记录调试问题
- 保存验收测试结果
- 形成问题闭环清单

## 8. 建议落地顺序

### 8.1 第一阶段：让 8083 大屏具备稳定演示口径

优先处理：

1. 修正 `/api/info` 项目名称。
2. 固化 `/api/dashboard/overview` 字段。
3. 补 `GET /api/areas` 和 `GET /api/areas/{areaId}/summary`。
4. 补 `GET /api/devices/list` 和 `GET /api/devices/{deviceId}`。
5. 增强 `/api/alarms`、`/api/events` 的筛选和详情。

### 8.2 第二阶段：补协议核心闭环

优先处理：

1. 门禁状态、门禁控制、人员通行记录。
2. 道闸状态、道闸控制、车辆通行记录、车辆许可。
3. 火车信号接入、火车道联动记录、火车道模式切换。
4. 告警确认、处置、关闭、证据关联。

### 8.3 第三阶段：补验收与运维能力

优先处理：

1. 摄像机列表、播放地址、录像查询。
2. AI 规则、AI 识别记录、算法指标。
3. 报表统计和导出。
4. 审计日志、配置版本、备份恢复。

## 9. 前端 8083 接入建议

前端建议按下面方式接入：

| 页面/模块 | 优先调用接口 | 说明 |
|---|---|---|
| 顶部总览卡片 | `/api/dashboard/overview` | 在线门禁、区域人数、车辆在场、火车道状态 |
| 区域态势 | `/api/areas`、`/api/areas/{areaId}/summary` | 区域列表和区域风险概览 |
| 设备状态图表 | `/api/device-status/summary`、`/api/device-status/records` | 现有接口可继续用 |
| 设备明细表 | `/api/devices/list` | 新增后替代仅统计的 `/api/devices` |
| 告警列表 | `/api/alarms` | 新增筛选、详情、处置 |
| 事件闭环 | `/api/events`、`/api/events/{eventId}` | 新增详情和关闭 |
| 门禁管控 | `/api/access/doors`、`/api/access/pass-records` | 协议核心 |
| 车辆管控 | `/api/vehicle/lanes`、`/api/vehicle/pass-records` | 协议核心 |
| 火车道联动 | `/api/railway/status`、`/api/railway/linkage-records` | 协议核心 |
| 视频证据 | `/api/video/evidence` | 验收闭环 |

### 9.1 《界面简介.docx》中的五个一级界面

`G:\photo\界面简介.docx` 将软件界面划分为五个一级界面，这个口径应作为后续前端页面拆分和 FastAPI 接口分组的主要依据。

| 一级界面 | 界面定位 | 核心展示内容 | 核心功能 | 提供方/状态 | 后端接口分组 |
|---|---|---|---|---|---|
| 系统总体界面 | 系统首页/总览驾驶舱，统一展示厂区全貌、运行状态和四个子界面入口 | 厂区总平图、A/F/L/成品库/火车道/道路/厂房/作业区、新增设备图层、运行总览卡片、事件/告警列表 | 总平图缩放、图层开关、区域高亮、区域/设备/时间查询统计、告警分发中心 | 需设计 | `/api/dashboard/overview`、`/api/areas`、`/api/device-status/*`、`/api/alarms`、`/api/events` |
| 人脸识别界面 | 面向封闭区域人员准入管理，解决谁能进、什么时候进、进了哪里、当前有多少人 | 门点状态、人脸抓拍、身份信息、白名单/黑名单、通行记录、区域人数、门禁权限 | 人脸识别、刷卡/双重认证、分区权限、异常开门告警、人员计数、事件追溯 | 上海贤松工业科技有限公司 | `/api/access/*`、`/api/video/evidence`、`/api/alarms` |
| 车辆管控界面（含火车道联动） | 面向车辆出入口与火车道交叉区域安全管控 | 车道/道闸状态、车牌识别、抓拍图片、车辆台账、预约/许可、火车道状态、联动倒计时、应急放行入口 | 车牌识别、授权放行、预约许可、误入告警、火车进出前 3-5 分钟预警、自动封控、应急模式和操作留痕 | 上海贤松工业科技有限公司 | `/api/vehicle/*`、`/api/railway/*`、`/api/alarms`、`/api/audit/logs` |
| 行车管控界面 | 面向厂内行车/吊运作业安全，解决盲区风险、驾驶员行为风险和精准停车 | 行车作业区域、驾驶员状态、盲区监控、危险区域告警、停车评分、事件回放与统计 | 疲劳/分心/打电话/低头识别、危险区域人员滞留/误入、盲区车辆主动预警、精准停车评分、异常事件留痕 | 需设计 | `/api/ai/detections`、`/api/video/cameras`、`/api/alarms`、`/api/reports/*` |
| 火灾等智能算法界面（含展示大屏） | 面向视频 AI 与消防/异常事件综合研判，形成算法告警中心和大屏展示中心 | 视频宫格/轮播、AI 告警、烟感温感、声光报警、区域告警地图、算法统计、65 寸大屏展示 | 人员/车辆轨迹、区域入侵/滞留、未戴安全帽、抽烟、违停、烟感温感接入、视频检索回放导出、告警闭环 | 目前已自研完成 | `/api/ai/*`、`/api/video/*`、`/api/alarm-devices/*`、`/api/device-status/*` |

### 9.2 给前端和 FastAPI 同学的对齐口径

可以直接按下面口径沟通：

前端侧：

- 先按《界面简介.docx》的五个一级界面拆页面：系统总体、人脸识别、车辆管控、行车管控、火灾及智能算法。
- 当前大屏首页只对应“系统总体界面”，定位是总览门户和态势入口。
- 截图底部四个按钮是四个子系统入口：`人脸识别`、`车辆管控`、`行车管控`、`火灾算法`；它们不是当前大屏面板里的普通筛选按钮。
- 底部按钮点击后建议跳转到对应子系统页面，或打开对应子系统嵌入页；当前大屏只保留摘要、告警提示和入口状态。
- 总体界面要保留厂区总平图/3D 地图挂载点，并支持设备图层、区域高亮、事件告警跳转到对应子系统。

FastAPI 侧：

- 接口分组跟五个界面走：`dashboard/areas/device-status` 给总体界面，`access` 给人脸识别，`vehicle + railway` 给车辆/火车道联动，`ai + video` 给行车和火灾算法，`alarms/events/audit` 给闭环和留痕。
- 先补第 10 节的最小可验收 API，保证前端能把五个界面跑起来。
- 控制类接口例如开门、抬杆、火车道模式切换，先做 mock 也要返回 `commandId` 和 `commandStatus`，方便前端做操作反馈和审计记录。
- `/api/info` 项目名称要从“轨道健康检测系统API”改为“成品库区域全封闭管控系统 API”。

### 9.3 8083 底部子系统入口与接口映射

根据当前 `8083` 前端截图，底部四个按钮应按“子系统入口”理解，不应按当前大屏内部模块理解：

| 底部按钮 | 子系统定位 | 子系统主要职责 | 与当前大屏关系 | 建议补充/优先接口 | 跳转/集成建议 |
|---|---|---|---|---|---|
| `人脸识别` | 人员准入与门禁识别子系统 | 人脸终端在线状态、人员识别记录、授权/未授权通行、黑白名单、门禁联锁事件 | 总览页只展示人员/门禁摘要和异常提示，完整功能进入子系统 | `GET /api/access/pass-records`、`GET /api/access/permissions`、`GET /api/access/doors`、`GET /api/video/evidence` | 跳转 `/face-recognition` 或嵌入人脸识别子系统 |
| `车辆管控` | 车辆进出与道闸子系统 | 车牌识别记录、车辆预约/许可、道闸状态、未授权拦截、车辆在场统计 | 总览页只展示车辆在场和关键告警，完整车辆管控进入子系统 | `GET /api/vehicle/lanes`、`POST /api/vehicle/lanes/{laneId}/command`、`GET /api/vehicle/pass-records`、`GET /api/vehicle/permits` | 跳转 `/vehicle-control` 或嵌入车辆管控子系统 |
| `行车管控` | 厂内行车/吊运安全子系统 | 驾驶员行为识别、盲区预警、危险区域告警、精准停车评分、事件回放 | 总览页只展示行车风险摘要，完整行车作业安全进入子系统 | `GET /api/ai/detections`、`GET /api/video/cameras`、`GET /api/reports/*`、`GET /api/alarms` | 跳转 `/driving-control` 或嵌入行车管控子系统 |
| `火灾算法` | 火灾及智能算法子系统 | 火灾/烟雾/抽烟/安全帽/入侵/违停等 AI 识别、烟感温感、证据留存 | 总览页只展示风险预警和消防状态摘要，完整算法管理进入子系统 | `GET /api/ai/rules`、`GET /api/ai/detections`、`GET /api/video/cameras`、`GET /api/video/evidence`、`GET /api/reports/alarm-statistics` | 跳转 `/fire-ai` 或嵌入火灾算法子系统 |

底部两侧的箭头按钮建议只作为“子系统入口翻页/轮播”使用，不建议绑定业务查询 API。如果后续入口超过四个，可以切换到第二组子系统入口。

| 入口组 | 建议按钮 | 说明 |
|---|---|---|
| 第一组 | `人脸识别`、`车辆管控`、`行车管控`、`火灾算法` | 当前截图已展示，对应四个子系统 |
| 第二组 | 预留 | 如果后续增加视频管理、设备运维、报表中心等独立系统，可放入第二组 |

### 9.4 子系统页面数据建议

#### 9.4.1 人脸识别

进入人脸识别子系统后，页面建议包含：

- 今日识别次数、授权通行数、未授权拦截数
- 人脸终端在线/离线数量
- 最近识别记录列表
- 关联门禁状态和抓拍证据

建议首屏请求：

```http
GET /api/access/pass-records?page=1&pageSize=10
GET /api/access/doors
GET /api/alarms?type=access&status=new
```

#### 9.4.2 车辆管控

进入车辆管控子系统后，页面建议包含：

- 当前在场车辆数
- 道闸在线/离线和开关状态
- 最近车辆进出记录
- 未授权车辆拦截记录
- 车辆预约/许可列表

建议首屏请求：

```http
GET /api/vehicle/lanes
GET /api/vehicle/pass-records?page=1&pageSize=10
GET /api/vehicle/permits
```

#### 9.4.3 行车管控

进入行车管控子系统后，页面建议包含：

- 火车道状态：空闲、预告、占用、驶离、故障、维护
- 火车信号倒计时或最近信号时间
- 当前联动隔离是否生效
- 火车道门/道闸/声光报警联动记录

建议首屏请求：

```http
GET /api/railway/status
GET /api/railway/linkage-records?page=1&pageSize=10
GET /api/alarms?type=railway
```

#### 9.4.4 火灾算法

进入火灾算法子系统后，页面建议包含：

- 火灾风险告警数
- 烟感温感设备在线/离线
- 抽烟、火焰/烟雾、区域入侵等 AI 识别记录
- 告警证据图片/短视频
- 算法准确率和启停状态

建议首屏请求：

```http
GET /api/alerts?type=fire
GET /api/ai/rules
GET /api/ai/detections?type=fire&page=1&pageSize=10
GET /api/video/evidence?type=fire
```

## 10. 最小可验收 API 清单

如果只按“能支撑协议演示和初步验收”划最小范围，建议至少补齐：

| 序号 | 方法 | 路径 | 原因 |
|---:|---|---|---|
| 1 | `GET` | `/api/areas` | 大屏区域筛选和区域态势基础 |
| 2 | `GET` | `/api/areas/{areaId}/summary` | 区域封闭状态汇总 |
| 3 | `GET` | `/api/devices/list` | 设备明细、状态、心跳 |
| 4 | `GET` | `/api/access/doors` | 门禁状态展示 |
| 5 | `POST` | `/api/access/doors/{doorId}/command` | 门禁控制与应急模式 |
| 6 | `GET` | `/api/access/pass-records` | 人员通行留痕 |
| 7 | `GET` | `/api/vehicle/lanes` | 道闸状态展示 |
| 8 | `POST` | `/api/vehicle/lanes/{laneId}/command` | 道闸控制 |
| 9 | `GET` | `/api/vehicle/pass-records` | 车辆通行留痕 |
| 10 | `GET` | `/api/railway/status` | 火车道当前联动状态 |
| 11 | `POST` | `/api/railway/signals/events` | 火车信号接入 |
| 12 | `GET` | `/api/railway/linkage-records` | 火车联动留痕 |
| 13 | `GET` | `/api/alarms/{alarmId}` | 告警详情 |
| 14 | `POST` | `/api/alarms/{alarmId}/actions` | 告警处置闭环 |
| 15 | `GET` | `/api/video/evidence` | 告警证据留存 |
| 16 | `GET` | `/api/audit/logs` | 应急/控制操作留痕 |

## 11. 一句话结论

当前 `8082 + 8083` 已经具备大屏展示和设备状态演示基础，但要完整匹配技术协议，还需要补齐门禁、车辆、火车道联动、告警闭环、视频证据、权限审计这些协议核心 API。建议先按第 10 节最小清单补齐，再扩展报表、AI 规则、配置版本和验收问题闭环。
