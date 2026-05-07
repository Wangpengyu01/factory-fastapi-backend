---
id: complete-api-doc
title: 成品库区域全封闭管控系统 API 文档
slug: /complete-api-doc
---

# 成品库区域全封闭管控系统 API 文档

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-API-FULL-2.1` |
| 原始版本 | `v2-from-zero` |
| 文档集 | `DOC-2026.05.07` |
| 适用系统版本 | `API-TARGET-1.0` + `OPENAPI-8082-CURRENT-2026.05.07` |
| 当前状态 | 全量 API 汇总和目标契约 |
| 更新日期 | `2026-05-07` |

整理日期：`2026-05-01`

本文档从零重新整理当前项目涉及的所有 API，目标是让前端、后端、联调和汇报人员只看这一份就能知道：Nacos 在系统里做什么、接口怎么调、哪些已经有、哪些只是协议建议。

适用读者：
- 前端同学：重点看第 `3`、`4`、`6`、`7`、`9`、`10`、`14.5` 节。
- 后端同学：重点看第 `1`、`5`、`6`、`7`、`8`、`12`、`14` 节。
- 测试/联调同学：重点看第 `4`、`9`、`10`、`11`、`15` 节。
- 汇报/项目管理：重点看第 `0`、`1`、`4`、`10`、`11`、`13` 节。

## 0. 先看结论

当前项目里实际有两套 API 口径：

| 口径 | Base URL | 来源 | 当前状态 |
|---|---|---|---|
| 本仓库 FastAPI 配置桥 | `http://localhost:8000` | `backend/app/main.py`、`backend/openapi.json` | 本仓库已实现，共 `5` 个接口 |
| 线上业务后端 | `http://101.43.49.78:8082` | `http://101.43.49.78:8082/openapi.json` | 线上已实现，共 `45` 个 OpenAPI 操作 |
| 补充协议接口 | 待定，一般沿用 `http://101.43.49.78:8082` | `PROTOCOL_API_GAP_AND_SUPPLEMENT.md` | 方案/待补齐，不等于已实现 |

本仓库 `8000` 服务是一个 Nacos 配置网关，不是完整业务后端。它的职责是把 Nacos 配置中心包装成前端可直接调用的 HTTP API，并给 `8083` 设备状态控件提供联调数据。

线上 `8082` 服务才是成品库区域全封闭管控业务 API 的主要承载方，包含大屏概览、区域、设备、门禁、车辆、火车道、告警、事件、巡检等接口。

## 1. Nacos 在本项目里的角色

### 1.1 Nacos 是什么

在本项目里，Nacos 只承担“配置中心”的角色：

- 存放 JSON/YAML/text 配置。
- 让后端或前端通过统一 API 读取配置。
- 支持受控发布配置，避免前端直接访问 Nacos 原生接口。
- 可作为 mock 数据或页面参数的数据源，例如设备状态记录、刷新间隔、页面配置。

Nacos 不是业务数据库，不负责存人员通行记录、车辆记录、告警闭环、视频证据这些业务数据。

### 1.2 本仓库为什么要包一层 FastAPI

前端不应该直接调用 Nacos 原生接口，原因有三点：

1. Nacos 原生接口参数和鉴权不适合直接暴露给前端。
2. 发布配置需要密钥保护。
3. 前端需要的是稳定业务字段，例如 `records`、`regions`、`devices`，不是 Nacos 原始响应。

所以本仓库的 FastAPI 做了这层转换：

```text
前端 / 运维页面
  -> FastAPI: /api/nacos/config
    -> Nacos: /v1/cs/configs
```

### 1.3 你应该怎么用 Nacos

最常见用法有两种。

第一种：读配置。

```http
GET /api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP
```

如果只想读某个字段：

```http
GET /api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP&field=deviceStatus.records
```

第二种：发配置。

```http
POST /api/nacos/config
X-Publish-Key: <你的发布密钥>
Content-Type: application/json

{
  "dataId": "device-status.json",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "type": "json",
  "content": "{\"deviceStatus\":{\"refreshSeconds\":30,\"records\":[]}}"
}
```

### 1.4 推荐放进 Nacos 的内容

| 类型 | 是否适合放 Nacos | 示例 |
|---|---:|---|
| 页面配置 | 是 | 刷新间隔、默认区域、图表开关 |
| mock 数据 | 是 | 设备状态 `deviceStatus.records` |
| 联动策略参数 | 可以 | 火车道提前预警秒数、告警等级阈值 |
| 字典项 | 可以 | 设备类型、区域配置 |
| 人员通行记录 | 否 | 应存业务库 |
| 车辆进出记录 | 否 | 应存业务库 |
| 告警处置记录 | 否 | 应存业务库 |
| 视频证据文件 | 否 | 应存对象存储/视频平台，接口只保存 URL 和元数据 |

### 1.5 一个标准 Nacos 配置样例

`dataId=device-status.json`

```json
{
  "deviceStatus": {
    "refreshSeconds": 30,
    "records": [
      {
        "region": "A区",
        "device": "摄像机",
        "online": 86,
        "offline": 6
      }
    ]
  }
}
```

读取记录：

```http
GET /api/device-status/records?dataId=device-status.json&field=deviceStatus.records
```

## 2. 环境和入口

### 2.1 本仓库本地服务

| 项 | 地址 |
|---|---|
| 后端 API | `http://localhost:8000` |
| 前端演示页 | `http://localhost:9000` |
| Swagger | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI | `http://localhost:8000/openapi.json` |
| 健康检查 | `http://localhost:8000/api/health` |

启动：

```powershell
cd H:\zxcasdqwe
Copy-Item .\backend\.env.example .\backend\.env
docker compose up -d --build
```

关键环境变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `PORT` | `8000` | FastAPI 服务端口 |
| `NACOS_BASE_URL` | `http://127.0.0.1:8848/nacos` | Nacos 地址 |
| `NACOS_USERNAME` | 空 | Nacos 开启鉴权时填写 |
| `NACOS_PASSWORD` | 空 | Nacos 开启鉴权时填写 |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:9000,http://localhost:8083` | 允许跨域来源 |
| `PUBLISH_API_KEY` | `change-this-to-a-strong-key` | 发布配置密钥 |

### 2.2 线上业务服务

| 项 | 地址 |
|---|---|
| API Base URL | `http://101.43.49.78:8082` |
| Swagger | `http://101.43.49.78:8082/docs` |
| OpenAPI | `http://101.43.49.78:8082/openapi.json` |
| 业务健康检查 | `http://101.43.49.78:8082/health` |
| API 信息 | `http://101.43.49.78:8082/api/info` |

说明：线上 `8082` 没有 `/api/health`，健康检查是 `/health`。本仓库 `8000` 的健康检查才是 `/api/health`。

## 3. 通用约定

### 3.1 请求和响应格式

- 请求体：`application/json`
- 响应体：`application/json`
- Nacos 发布时，FastAPI 内部再转成 Nacos 原生表单请求。

### 3.2 响应包装

本仓库 `8000`：裸 JSON。

```json
{
  "status": "ok"
}
```

线上业务 `8082`：多数业务接口使用统一包装。

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

例外：线上 `8082` 的部分 `device-status` 接口是裸 JSON，例如 `/api/device-status/options`、`/api/device-status/summary`。

### 3.3 分页

常规分页：

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 0
}
```

巡检任务接口使用 `per_page` 作为每页数量参数。

### 3.4 时间

推荐 ISO-8601 字符串：

```text
2026-05-01T10:00:00+08:00
```

线上部分样例无时区：

```text
2026-05-01T10:00:00.123456
```

前端解析时需要兼容两种格式。

### 3.5 常用状态枚举

| 字段 | 枚举 | 说明 |
|---|---|---|
| `onlineStatus` | `online`、`offline`、`fault`、`unknown` | 设备在线状态 |
| `doorStatus` | `open`、`closed`、`locked`、`fault`、`unknown` | 门禁状态 |
| `barrierStatus` | `open`、`closed`、`opening`、`closing`、`fault`、`unknown` | 道闸状态 |
| `railStatus` | `idle`、`approaching`、`occupied`、`leaving`、`fault`、`maintenance` | 火车道状态 |
| `alarmStatus` | `new`、`acknowledged`、`processing`、`closed`、`ignored` | 告警状态 |
| `severity` | `low`、`medium`、`high`、`critical` | 告警等级 |
| `commandStatus` | `accepted`、`rejected`、`executing`、`done`、`failed` | 控制命令状态 |
| `direction` | `in`、`out`、`bidirectional` | 车道方向 |
| `result` | `allowed`、`denied` | 通行结果 |

### 3.6 全局状态码总结

下面状态码作为团队统一口径使用，不区分接口当前是否已经实现。前端、后端、测试和文档都按这张表理解。

| 状态码 | 名称 | 统一含义 | 常见场景 | 前端处理建议 |
|---:|---|---|---|---|
| `200` | OK | 请求成功 | 查询成功、控制命令已接收、配置读取成功 | 正常渲染数据 |
| `201` | Created | 创建成功 | 新增权限、新增车辆许可、新增验收问题 | 提示创建成功，刷新列表 |
| `202` | Accepted | 请求已接收但未完成 | 控制命令异步执行、报表导出任务创建 | 显示“处理中”，轮询任务状态 |
| `204` | No Content | 成功但无响应体 | 删除成功、无须返回内容的操作 | 不解析 JSON，直接按成功处理 |
| `400` | Bad Request | 业务参数非法 | 未知区域、未知设备、时间范围错误、非法状态流转 | 展示后端 `message/detail`，让用户修正输入 |
| `401` | Unauthorized | 未认证或密钥错误 | `X-Publish-Key` 错误、登录态失效 | 提示重新登录或检查发布密钥 |
| `403` | Forbidden | 已认证但无权限 | 无门禁控制权限、无告警关闭权限 | 提示无权限，不重复重试 |
| `404` | Not Found | 资源不存在 | 设备不存在、告警不存在、Nacos 字段不存在 | 提示资源不存在，必要时刷新列表 |
| `405` | Method Not Allowed | HTTP 方法错误 | 用 `GET` 调了只支持 `POST` 的接口 | 检查前端请求方法 |
| `409` | Conflict | 资源状态冲突 | 重复关闭告警、重复启动任务、设备正在执行命令 | 提示当前状态不允许操作 |
| `415` | Unsupported Media Type | 请求格式不支持 | 未传 `application/json` | 检查请求头 |
| `422` | Unprocessable Entity | 请求结构或字段校验失败 | 必填字段缺失、数字类型错误、JSON/YAML 解析失败 | 标记表单字段错误或提示配置格式错误 |
| `429` | Too Many Requests | 请求过于频繁 | 大屏轮询过快、接口限流 | 降低刷新频率，延迟重试 |
| `500` | Internal Server Error | 服务端未预期异常 | 代码异常、数据处理异常 | 提示系统异常，保留旧数据 |
| `502` | Bad Gateway | 下游服务异常 | Nacos 访问失败、视频平台异常、第三方服务异常 | 提示依赖异常，保留旧数据 |
| `503` | Service Unavailable | 服务不可用或未配置 | 未配置 `PUBLISH_API_KEY`、依赖服务未启动 | 提示服务暂不可用 |
| `504` | Gateway Timeout | 下游超时 | Nacos 超时、视频流地址获取超时 | 提示超时，可稍后重试 |

后端返回错误时推荐结构：

```json
{
  "code": 400,
  "success": false,
  "message": "未知区域：X区",
  "data": null,
  "traceId": "optional-trace-id"
}
```

FastAPI 默认错误结构也需要前端兼容：

```json
{
  "detail": "Unknown region: X区"
}
```

FastAPI 参数校验错误结构：

```json
{
  "detail": [
    {
      "loc": ["query", "pageSize"],
      "msg": "Input should be less than or equal to 1000",
      "type": "less_than_equal"
    }
  ]
}
```

### 3.7 全局 JSON 结构总结

本节只总结 JSON 结构规范，不区分已实现或待实现。后续新接口优先按这里统一。

#### 3.7.1 成功响应包装

业务后端推荐统一包装：

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
| `code` | `number` | 是 | 业务/HTTP 状态码，一般与 HTTP 状态码一致 |
| `success` | `boolean` | 是 | 是否成功 |
| `message` | `string` | 是 | 给前端展示或调试的说明 |
| `data` | `object \| array \| null` | 是 | 真正业务数据 |
| `traceId` | `string` | 否 | 链路追踪 ID，排查问题用 |

#### 3.7.2 裸 JSON 响应

本仓库 `8000` 当前保留裸 JSON，例如：

```json
{
  "status": "ok"
}
```

前端必须同时兼容“包装 JSON”和“裸 JSON”，不能假设所有响应都有 `success/data`。

#### 3.7.3 分页 JSON

分页列表统一放在 `data` 内：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "items": [],
    "page": 1,
    "pageSize": 20,
    "total": 0
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `items` | `array` | 当前页记录 |
| `page` | `number` | 当前页码，从 `1` 开始 |
| `pageSize` | `number` | 每页数量 |
| `total` | `number` | 总记录数 |

#### 3.7.4 下拉选项 JSON

简单字符串选项：

```json
{
  "regions": ["全部", "A区", "F区"],
  "devices": ["全部", "摄像机", "人员智能门/联锁门"]
}
```

推荐业务选项：

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

推荐字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 提交给接口的稳定值 |
| `name` | `string` | 页面显示名称 |
| `disabled` | `boolean` | 是否禁用，可选 |
| `sort` | `number` | 排序，可选 |

#### 3.7.5 设备状态 JSON

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
      "online": 86,
      "offline": 6
    }
  ],
  "updatedAt": "2026-05-01T10:00:00+08:00"
}
```

#### 3.7.6 命令响应 JSON

门禁、道闸、火车道模式切换、报警设备控制统一返回命令结构：

```json
{
  "code": 200,
  "success": true,
  "message": "命令已接收",
  "data": {
    "commandId": "cmd_202605010001",
    "targetId": "door_r01_001",
    "targetType": "door",
    "command": "open",
    "status": "accepted",
    "operator": "admin",
    "reason": "现场授权放行",
    "createdAt": "2026-05-01T10:00:00+08:00"
  }
}
```

命令状态枚举：`accepted`、`rejected`、`executing`、`done`、`failed`。

#### 3.7.7 Nacos 配置读取 JSON

单配置读取：

```json
{
  "mode": "single",
  "dataId": "device-status.json",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "field": "deviceStatus.records",
  "content": "{\"deviceStatus\":{\"records\":[]}}",
  "parsed": {
    "deviceStatus": {
      "records": []
    }
  },
  "value": [],
  "total": null,
  "items": null,
  "mergedParams": null
}
```

全量读取：

```json
{
  "mode": "all",
  "dataId": null,
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "field": null,
  "content": null,
  "parsed": null,
  "value": null,
  "total": 2,
  "items": [],
  "mergedParams": {}
}
```

#### 3.7.8 告警 JSON

```json
{
  "id": "alarm_001",
  "alarmType": "access",
  "title": "未授权通行",
  "severity": "high",
  "status": "new",
  "areaId": "r01",
  "areaName": "A区",
  "deviceId": "door_r01_001",
  "deviceName": "A区门禁1",
  "occurredAt": "2026-05-01T10:00:00+08:00",
  "closedAt": null
}
```

#### 3.7.9 事件 JSON

```json
{
  "id": "event_001",
  "eventType": "railway_linkage",
  "status": "processing",
  "areaId": "r05",
  "areaName": "火车道",
  "sourceType": "railway",
  "sourceId": "sig_202605010001",
  "description": "火车即将进入，触发联动隔离",
  "evidenceIds": [],
  "occurredAt": "2026-05-01T10:00:00+08:00"
}
```

#### 3.7.10 通行记录 JSON

人员通行：

```json
{
  "id": "pass_001",
  "personId": "p001",
  "personName": "张三",
  "doorId": "door_r01_001",
  "doorName": "A区门禁1",
  "areaName": "A区",
  "method": "face",
  "result": "allowed",
  "reason": "白名单授权",
  "snapshotUrl": "https://example.com/snapshot.jpg",
  "occurredAt": "2026-05-01T10:00:00+08:00"
}
```

车辆通行：

```json
{
  "id": "vehicle_pass_001",
  "plateNo": "沪A12345",
  "laneId": "lane_r01_001",
  "laneName": "A区入口车道",
  "areaName": "A区",
  "direction": "in",
  "result": "allowed",
  "reason": "预约车辆",
  "snapshotUrl": "https://example.com/plate.jpg",
  "occurredAt": "2026-05-01T10:00:00+08:00"
}
```

#### 3.7.11 证据 JSON

```json
{
  "id": "evidence_001",
  "alarmId": "alarm_001",
  "eventId": "event_001",
  "cameraId": "cam_r01_001",
  "type": "image",
  "url": "https://example.com/evidence.jpg",
  "capturedAt": "2026-05-01T10:00:00+08:00",
  "retentionDays": 180
}
```

#### 3.7.12 JSON 字段命名总结

| 类型 | 规则 | 示例 |
|---|---|---|
| JSON 字段 | `camelCase` | `areaId`、`pageSize`、`updatedAt` |
| Python 内部变量 | `snake_case` | `area_id`、`page_size`、`updated_at` |
| 路径参数 | `camelCase` 优先 | `{areaId}`、`{deviceId}` |
| 数据 ID | 保持 Nacos 原始命名 | `dataId` |
| 时间字段 | 以 `At` 结尾 | `createdAt`、`updatedAt`、`occurredAt` |
| 数量字段 | 使用 `Count` 或明确名词 | `doorClosedCount`、`onlineDevices` |

#### 3.7.13 JSON 空值规则

| 场景 | 推荐值 |
|---|---|
| 无对象 | `null` |
| 无列表 | `[]` |
| 无字符串 | `""` 或 `null`，同一字段保持一致 |
| 无数字 | `0` 或 `null`，统计值优先 `0` |
| 无布尔值 | `false` 或 `null`，开关值优先 `false` |

#### 3.7.14 前端统一解析建议

```ts
function unwrapApiResponse(response: any) {
  if (response && typeof response === "object" && "success" in response && "data" in response) {
    if (!response.success) {
      throw new Error(response.message || "请求失败");
    }
    return response.data;
  }
  return response;
}
```

## 4. 全部接口总表

### 4.1 本仓库 8000 已实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/nacos/config` | 读取 Nacos 配置 |
| `POST` | `/api/nacos/config` | 发布 Nacos 配置 |
| `GET` | `/api/device-status/options` | 获取 8083 设备状态筛选项 |
| `GET` | `/api/device-status/records` | 获取 8083 设备状态记录 |

### 4.2 线上 8082 已实现接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/` | 根路径 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api` | API 根路径 |
| `GET` | `/api/info` | API 信息 |
| `GET` | `/api/test` | 连接测试 |
| `GET` | `/api/overview` | 首页旧版概览 |
| `GET` | `/api/dashboard/overview` | 大屏聚合概览 |
| `GET` | `/api/area/{area_id}` | 区域详情 |
| `GET` | `/api/areas` | 区域列表 |
| `GET` | `/api/areas/{areaId}/summary` | 区域综合状态 |
| `GET` | `/api/devices` | 设备总览 |
| `GET` | `/api/devices/list` | 设备明细列表 |
| `GET` | `/api/devices/{deviceId}` | 设备详情 |
| `GET` | `/api/device-status/options` | 设备状态筛选项 |
| `GET` | `/api/device-status/summary` | 设备状态汇总 |
| `GET` | `/api/device-status/records` | 设备状态记录 |
| `GET` | `/api/alarms` | 告警列表 |
| `GET` | `/api/alarms/{alarmId}` | 告警详情 |
| `POST` | `/api/alarms/{alarmId}/actions` | 告警动作 |
| `GET` | `/api/events` | 事件列表 |
| `GET` | `/api/events/{eventId}` | 事件详情 |
| `PATCH` | `/api/events/{eventId}/close` | 关闭事件 |
| `GET` | `/api/alerts` | 风险预警 |
| `GET` | `/api/access/doors` | 门禁列表 |
| `GET` | `/api/access/doors/{doorId}` | 门禁详情 |
| `POST` | `/api/access/doors/{doorId}/command` | 门禁控制 |
| `GET` | `/api/access/pass-records` | 人员通行记录 |
| `GET` | `/api/vehicle/lanes` | 车道/道闸列表 |
| `POST` | `/api/vehicle/lanes/{laneId}/command` | 道闸控制 |
| `GET` | `/api/vehicle/pass-records` | 车辆通行记录 |
| `GET` | `/api/railway/status` | 火车道状态 |
| `GET` | `/api/railway/linkage-records` | 火车道联动记录 |
| `POST` | `/api/railway/mode` | 设置火车道模式 |
| `GET` | `/api/nacos/config` | 读取 Nacos 配置 |
| `POST` | `/api/nacos/config` | 发布 Nacos 配置 |
| `GET` | `/api/tree-menu` | 业务树菜单 |
| `GET` | `/api/point/{point_id}/latest-measurement` | 测点最新测量 |
| `GET` | `/api/point/{point_id}/history-measurements` | 测点历史测量 |
| `GET` | `/api/premade-point/{premade_point_id}/latest-image` | 预制点最新图片 |
| `GET` | `/api/latest-measurements` | 最新测量轮询 |
| `POST` | `/api/v1/inspection/create-task` | 创建巡检任务 |
| `POST` | `/api/v1/inspection/start-task/{task_id}` | 启动巡检任务 |
| `GET` | `/api/v1/inspection/tasks` | 巡检任务列表 |
| `GET` | `/api/v1/inspection/list` | 巡检任务列表兼容路径 |
| `GET` | `/api/v1/inspection/task/{task_id}` | 巡检任务详情 |
| `POST` | `/api/v1/inspection/cancel-task/{task_id}` | 取消巡检任务 |
| `DELETE` | `/api/v1/inspection/tasks/{task_id}` | 删除巡检任务 |

### 4.3 协议建议但未确认实现的接口

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/access/permissions` | 人员权限列表 |
| `POST` | `/api/access/permissions` | 新增人员权限 |
| `PATCH` | `/api/access/permissions/{permissionId}` | 修改人员权限 |
| `DELETE` | `/api/access/permissions/{permissionId}` | 删除人员权限 |
| `GET` | `/api/vehicle/permits` | 车辆许可列表 |
| `POST` | `/api/vehicle/permits` | 新增车辆许可 |
| `PATCH` | `/api/vehicle/permits/{permitId}` | 修改车辆许可 |
| `DELETE` | `/api/vehicle/permits/{permitId}` | 删除车辆许可 |
| `POST` | `/api/railway/signals/events` | 接收火车信号事件 |
| `GET` | `/api/alarm-devices` | 报警设备列表 |
| `POST` | `/api/alarm-devices/{deviceId}/command` | 报警设备控制 |
| `GET` | `/api/alarm-devices/{deviceId}/records` | 报警设备触发记录 |
| `GET` | `/api/video/cameras` | 摄像机列表 |
| `GET` | `/api/video/cameras/{cameraId}/stream-url` | 摄像机播放地址 |
| `GET` | `/api/video/recordings` | 录像查询 |
| `GET` | `/api/video/evidence` | 证据列表 |
| `GET` | `/api/video/evidence/{evidenceId}` | 证据详情 |
| `POST` | `/api/video/evidence/export` | 证据导出 |
| `GET` | `/api/ai/rules` | AI 规则 |
| `PATCH` | `/api/ai/rules/{ruleId}` | 修改 AI 规则 |
| `GET` | `/api/ai/detections` | AI 识别记录 |
| `GET` | `/api/reports/device-status` | 设备状态报表 |
| `GET` | `/api/reports/alarm-statistics` | 告警统计 |
| `GET` | `/api/reports/pass-statistics` | 通行统计 |
| `GET` | `/api/reports/vehicle-statistics` | 车辆统计 |
| `POST` | `/api/reports/export` | 报表导出 |
| `GET` | `/api/auth/me` | 当前用户 |
| `GET` | `/api/audit/logs` | 审计日志 |
| `GET` | `/api/config/versions` | 配置版本 |
| `POST` | `/api/config/versions/{versionId}/rollback` | 配置回滚 |
| `GET` | `/api/config/backups` | 配置备份 |
| `POST` | `/api/config/backups` | 创建备份 |
| `GET` | `/api/acceptance/issues` | 验收问题 |
| `POST` | `/api/acceptance/issues` | 新增验收问题 |
| `PATCH` | `/api/acceptance/issues/{issueId}` | 更新验收问题 |
| `GET` | `/api/acceptance/test-records` | 验收测试记录 |
| `POST` | `/api/acceptance/test-records` | 新增验收测试记录 |

## 5. 数据模型定义

### 5.1 本仓库 8000 模型

#### HealthResponse

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `status` | `string` | 是 | 当前固定为 `ok` |

#### ConfigItem

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `dataId` | `string` | 是 | 配置 ID |
| `group` | `string` | 是 | Nacos 分组 |
| `tenant` | `string \| null` | 否 | Nacos namespaceId |
| `content` | `string` | 是 | 配置原文 |
| `parsed` | `unknown \| null` | 否 | JSON/YAML 解析结果 |
| `value` | `unknown \| null` | 否 | 按 `field` 提取的值 |

#### ConfigReadResponse

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `mode` | `single \| all` | 是 | 单配置或全量列表模式 |
| `dataId` | `string \| null` | 否 | 配置 ID |
| `group` | `string \| null` | 否 | 分组 |
| `tenant` | `string \| null` | 否 | namespaceId |
| `field` | `string \| null` | 否 | 点路径字段 |
| `content` | `string \| null` | 否 | 单配置原文 |
| `parsed` | `unknown \| null` | 否 | 单配置解析结果 |
| `value` | `unknown \| null` | 否 | 字段提取值 |
| `total` | `number \| null` | 否 | 全量模式条数 |
| `items` | `ConfigItem[] \| null` | 否 | 全量模式配置列表 |
| `mergedParams` | `object \| null` | 否 | 合并后的配置对象 |

#### PublishConfigBody

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `dataId` | `string` | 是 | - | 配置 ID |
| `group` | `string` | 否 | `DEFAULT_GROUP` | 分组 |
| `tenant` | `string \| null` | 否 | `null` | namespaceId |
| `content` | `string` | 是 | - | 配置内容 |
| `type` | `string` | 否 | `text` | 配置类型，常用 `json`、`yaml`、`text` |

#### PublishConfigResponse

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `success` | `boolean` | 是 | 是否成功 |
| `message` | `string` | 是 | 结果说明 |

#### DeviceStatusRecord

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `region` | `string` | 是 | 区域 |
| `device` | `string` | 是 | 设备类型 |
| `online` | `integer` | 是 | 在线数量，非负 |
| `offline` | `integer` | 是 | 离线数量，非负 |

#### DeviceStatusOptionsResponse

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `regions` | `string[]` | 是 | 区域筛选项 |
| `devices` | `string[]` | 是 | 设备筛选项 |

#### DeviceStatusRecordsResponse

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `records` | `DeviceStatusRecord[]` | 是 | 设备状态记录 |
| `updatedAt` | `string` | 是 | 更新时间 |

### 5.2 线上 8082 请求模型

#### PublishConfigRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `dataId` | `string` | 是 | - | 配置 ID |
| `group` | `string` | 否 | `DEFAULT_GROUP` | 分组 |
| `tenant` | `string` | 否 | `""` | namespaceId |
| `type` | `string` | 否 | `text` | 配置类型 |
| `content` | `string` | 是 | - | 配置内容 |

#### CreateTaskRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `task_name` | `string` | 否 | - | 任务名称 |
| `detection_type` | `string` | 是 | - | 检测类型 |
| `selected_points` | `string[]` | 是 | - | 选择测点 |
| `screw_alarm_threshold` | `number` | 否 | `5.0` | 螺栓报警阈值 |
| `opening_alarm_threshold` | `number` | 否 | `135.0` | 开距报警阈值 |
| `auto_start` | `boolean` | 否 | `false` | 是否自动启动 |
| `schedule_config` | `object` | 否 | - | 调度配置 |
| `metadata` | `object` | 否 | - | 扩展信息 |

#### DoorCommandRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `command` | `string` | 是 | - | 门禁命令 |
| `reason` | `string` | 否 | `""` | 操作原因 |
| `durationSeconds` | `integer` | 否 | `30` | 持续秒数 |
| `operator` | `string` | 否 | `admin` | 操作人 |

建议命令：`open`、`close`、`lock`、`unlock`、`emergency_open`、`reset`。

#### VehicleCommandRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `command` | `string` | 是 | - | 道闸命令 |
| `reason` | `string` | 否 | `""` | 操作原因 |
| `operator` | `string` | 否 | `admin` | 操作人 |

建议命令：`open`、`close`、`lock_open`、`lock_closed`、`reset`。

#### RailwayModeRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `mode` | `string` | 是 | - | 火车道模式 |
| `reason` | `string` | 否 | `""` | 切换原因 |
| `operator` | `string` | 否 | `admin` | 操作人 |

建议模式：`normal`、`emergency`、`maintenance`、`manual`。

#### AlarmActionRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `action` | `string` | 是 | - | 处理动作 |
| `comment` | `string` | 否 | `""` | 备注 |
| `operator` | `string` | 否 | `admin` | 操作人 |

建议动作：`acknowledge`、`process`、`close`、`ignore`、`reopen`。

#### EventCloseRequest

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `result` | `string` | 否 | `""` | 处理结果 |
| `comment` | `string` | 否 | `""` | 备注 |
| `operator` | `string` | 否 | `admin` | 操作人 |

## 6. 本仓库 8000 详细接口

### 6.1 健康检查

```http
GET /api/health
```

用途：确认本仓库 FastAPI 服务是否在线。

响应：

```json
{
  "status": "ok"
}
```

### 6.2 读取 Nacos 配置

```http
GET /api/nacos/config
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `dataId` | `string` | 否 | `""` | 配置 ID；为空表示读取列表 |
| `group` | `string` | 否 | `DEFAULT_GROUP` | 分组 |
| `tenant` | `string` | 否 | `null` | namespaceId |
| `field` | `string` | 否 | `null` | 点路径字段，例如 `deviceStatus.records` |
| `pageNo` | `integer` | 否 | `1` | 列表页码 |
| `pageSize` | `integer` | 否 | `200` | 每页数量，最大 `1000` |

单配置读取：

```http
GET /api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP
```

字段读取：

```http
GET /api/nacos/config?dataId=device-status.json&field=deviceStatus.records
```

列表读取：

```http
GET /api/nacos/config?dataId=&group=DEFAULT_GROUP&pageNo=1&pageSize=200
```

错误：

| 状态码 | 说明 |
|---|---|
| `404` | 字段不存在 |
| `422` | 配置不能解析为 JSON/YAML，或字段读取不合法 |
| `502` | Nacos 返回异常 |

### 6.3 发布 Nacos 配置

```http
POST /api/nacos/config
```

Header：

| 参数 | 必填 | 说明 |
|---|---:|---|
| `X-Publish-Key` | 是 | 发布密钥，来自服务端 `PUBLISH_API_KEY` |

Body：`PublishConfigBody`

示例：

```json
{
  "dataId": "device-status.json",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "type": "json",
  "content": "{\"deviceStatus\":{\"refreshSeconds\":30,\"records\":[]}}"
}
```

响应：

```json
{
  "success": true,
  "message": "Config published to Nacos"
}
```

错误：

| 状态码 | 说明 |
|---|---|
| `401` | 发布密钥错误 |
| `503` | 服务端未配置发布密钥 |
| `502` | Nacos 发布失败 |

### 6.4 获取设备状态筛选项

```http
GET /api/device-status/options
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `region` | `string` | 否 | `全部` | 区域名称 |
| `regionId` | `string` | 否 | `null` | 区域别名，优先级高于 `region` |

响应：

```json
{
  "regions": ["全部", "A区", "F区", "L区", "成品库", "火车道", "道路", "厂房", "作业区"],
  "devices": ["全部", "人员智能门/联锁门", "摄像机"]
}
```

说明：当前只基于内置演示数据生成，不读取 Nacos。

### 6.5 获取设备状态记录

```http
GET /api/device-status/records
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `region` | `string` | 否 | `全部` | 区域名称 |
| `regionId` | `string` | 否 | `null` | 区域别名 |
| `device` | `string` | 否 | `全部` | 设备名称 |
| `deviceType` | `string` | 否 | `null` | 设备别名 |
| `dataId` | `string` | 否 | `""` | Nacos 配置 ID；为空使用演示数据 |
| `group` | `string` | 否 | `DEFAULT_GROUP` | Nacos 分组 |
| `tenant` | `string` | 否 | `null` | namespaceId |
| `field` | `string` | 否 | `deviceStatus.records` | 配置字段路径 |

响应：

```json
{
  "records": [
    {
      "region": "A区",
      "device": "摄像机",
      "online": 86,
      "offline": 6
    }
  ],
  "updatedAt": "2026-05-01T10:00:00+08:00"
}
```

支持的 Nacos 配置结构：

```json
[
  { "region": "A区", "device": "摄像机", "online": 1, "offline": 0 }
]
```

```json
{
  "records": [
    { "region": "A区", "device": "摄像机", "online": 1, "offline": 0 }
  ]
}
```

```json
{
  "deviceStatus": {
    "records": [
      { "region": "A区", "device": "摄像机", "online": 1, "offline": 0 }
    ]
  }
}
```

错误：

| 状态码 | 说明 |
|---|---|
| `400` | 未知区域或未知设备 |
| `404` | 指定字段不存在 |
| `422` | 配置结构不合法 |

## 7. 线上 8082 详细接口

### 7.1 系统接口

#### 根路径

```http
GET /
GET /api
GET /api/test
```

用途：基础连通性检查。

#### 健康检查

```http
GET /health
```

用途：线上业务服务健康检查。

#### API 信息

```http
GET /api/info
```

响应示例：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "name": "成品库区域全封闭管控系统 API",
    "version": "v1",
    "description": "提供成品库区域全封闭管控、门禁管理、车辆管理、火车道联动等功能"
  }
}
```

### 7.2 大屏概览

#### 旧版概览

```http
GET /api/overview
```

说明：旧版概览，字段以线上返回为准。

#### 大屏聚合概览

```http
GET /api/dashboard/overview
```

用途：大屏首页首屏聚合接口。

核心响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `onlineAccess` | `number` | 在线门禁数 |
| `areaTotal` | `number` | 区域总数 |
| `vehiclesOnSite` | `number` | 当前在场车辆数 |
| `railStatus` | `string` | 火车道状态 |
| `deviceRecords` | `DeviceStatusRecord[]` | 设备状态记录 |

### 7.3 区域接口

#### 区域详情

```http
GET /api/area/{area_id}
```

Path：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `area_id` | `string` | 是 | 区域 ID |

#### 区域列表

```http
GET /api/areas
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `includeDisabled` | `boolean` | 否 | `false` | 是否包含停用区域 |

响应数据：

```json
{
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
```

#### 区域综合状态

```http
GET /api/areas/{areaId}/summary
```

Path：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `areaId` | `string` | 是 | 区域 ID |

建议关注字段：`peopleCount`、`vehicleCount`、`doorSummary`、`cameraSummary`、`alarmSummary`、`riskLevel`、`updatedAt`。

### 7.4 设备接口

#### 设备总览

```http
GET /api/devices
```

用途：设备统计类总览。

#### 设备明细列表

```http
GET /api/devices/list
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `deviceType` | `string` | 否 | - | 设备类型 |
| `onlineStatus` | `string` | 否 | - | 在线状态 |
| `keyword` | `string` | 否 | - | 关键词 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

#### 设备详情

```http
GET /api/devices/{deviceId}
```

Path：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `deviceId` | `string` | 是 | 设备 ID |

### 7.5 设备状态接口

#### 筛选项

```http
GET /api/device-status/options
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `regionId` | `string` | 否 | `all` | 区域 ID |

线上 `8082` 返回对象数组：

```json
{
  "regions": [
    { "id": "all", "name": "全部" },
    { "id": "r01", "name": "A区" }
  ],
  "devices": [
    { "id": "all", "name": "全部" },
    { "id": "door", "name": "人员智能门/联锁门" }
  ]
}
```

#### 汇总

```http
GET /api/device-status/summary
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `regionId` | `string` | 否 | `all` | 区域 ID |
| `deviceType` | `string` | 否 | `all` | 设备类型 |

响应字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `summary.totalDevices` | `number` | 设备总数 |
| `summary.onlineDevices` | `number` | 在线数 |
| `summary.offlineDevices` | `number` | 离线数 |
| `summary.onlineRate` | `number` | 在线率 |
| `records` | `DeviceStatusRecord[]` | 明细记录 |

#### 记录

```http
GET /api/device-status/records
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `regionId` | `string` | 否 | `all` | 区域 ID |
| `deviceType` | `string` | 否 | `all` | 设备类型 |
| `dataId` | `string` | 否 | `""` | Nacos 配置 ID |
| `field` | `string` | 否 | `deviceStatus.records` | 字段路径 |

### 7.6 Nacos 配置接口

#### 读取配置

```http
GET /api/nacos/config
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `dataId` | `string` | 否 | `""` | 配置 ID |
| `group` | `string` | 否 | `DEFAULT_GROUP` | 分组 |
| `tenant` | `string` | 否 | `""` | namespaceId |
| `field` | `string` | 否 | `""` | 字段路径 |
| `pageNo` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `200` | 每页数量 |

#### 发布配置

```http
POST /api/nacos/config
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `x_publish_key` | `string` | 否 | 线上 OpenAPI 中定义为 query 参数 |

Body：`PublishConfigRequest`

注意：线上 `8082` 的发布密钥是 `x_publish_key` query 参数，本仓库 `8000` 是 `X-Publish-Key` Header。

### 7.7 门禁与人员

#### 门禁列表

```http
GET /api/access/doors
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `status` | `string` | 否 | - | 门状态 |
| `onlineStatus` | `string` | 否 | - | 在线状态 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

返回记录字段：`id`、`name`、`areaId`、`areaName`、`doorStatus`、`onlineStatus`、`interlockGroupId`、`lastHeartbeatAt`、`lastEventAt`。

#### 门禁详情

```http
GET /api/access/doors/{doorId}
```

#### 门禁控制

```http
POST /api/access/doors/{doorId}/command
```

Path：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `doorId` | `string` | 是 | 门禁 ID |

Body：`DoorCommandRequest`

#### 人员通行记录

```http
GET /api/access/pass-records
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `doorId` | `string` | 否 | - | 门禁 |
| `personName` | `string` | 否 | - | 人员姓名 |
| `cardNo` | `string` | 否 | - | 卡号 |
| `result` | `string` | 否 | - | 通行结果 |
| `startTime` | `string` | 否 | - | 开始时间 |
| `endTime` | `string` | 否 | - | 结束时间 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

### 7.8 车辆与道闸

#### 车道/道闸列表

```http
GET /api/vehicle/lanes
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `onlineStatus` | `string` | 否 | - | 在线状态 |
| `barrierStatus` | `string` | 否 | - | 道闸状态 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

返回记录字段：`id`、`name`、`areaId`、`direction`、`barrierStatus`、`recognizerStatus`、`onlineStatus`、`lastPlateNo`、`lastEventAt`。

#### 道闸控制

```http
POST /api/vehicle/lanes/{laneId}/command
```

Body：`VehicleCommandRequest`

#### 车辆通行记录

```http
GET /api/vehicle/pass-records
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `laneId` | `string` | 否 | - | 车道 |
| `plateNo` | `string` | 否 | - | 车牌号 |
| `direction` | `string` | 否 | - | 方向 |
| `result` | `string` | 否 | - | 通行结果 |
| `startTime` | `string` | 否 | - | 开始时间 |
| `endTime` | `string` | 否 | - | 结束时间 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

### 7.9 火车道联动

#### 火车道状态

```http
GET /api/railway/status
```

核心字段：`railStatus`、`signalStatus`、`approachEtaSeconds`、`isIsolationActive`、`activeLinkageId`、`doorClosedCount`、`doorOpenCount`、`alarmActiveCount`、`updatedAt`。

#### 火车道联动记录

```http
GET /api/railway/linkage-records
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `status` | `string` | 否 | - | 联动状态 |
| `startTime` | `string` | 否 | - | 开始时间 |
| `endTime` | `string` | 否 | - | 结束时间 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

#### 设置火车道模式

```http
POST /api/railway/mode
```

Body：`RailwayModeRequest`

### 7.10 告警、事件、预警

#### 告警列表

```http
GET /api/alarms
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `severity` | `string` | 否 | - | 等级 |
| `status` | `string` | 否 | - | 状态 |
| `alarmType` | `string` | 否 | - | 类型 |
| `startTime` | `string` | 否 | - | 开始时间 |
| `endTime` | `string` | 否 | - | 结束时间 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

#### 告警详情

```http
GET /api/alarms/{alarmId}
```

#### 告警动作

```http
POST /api/alarms/{alarmId}/actions
```

Body：`AlarmActionRequest`

#### 事件列表

```http
GET /api/events
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `areaId` | `string` | 否 | - | 区域 |
| `eventType` | `string` | 否 | - | 事件类型 |
| `status` | `string` | 否 | - | 状态 |
| `startTime` | `string` | 否 | - | 开始时间 |
| `endTime` | `string` | 否 | - | 结束时间 |
| `page` | `integer` | 否 | `1` | 页码 |
| `pageSize` | `integer` | 否 | `20` | 每页数量 |

#### 事件详情

```http
GET /api/events/{eventId}
```

#### 关闭事件

```http
PATCH /api/events/{eventId}/close
```

Body：`EventCloseRequest`

#### 风险预警

```http
GET /api/alerts
```

用途：获取风险预警列表。

### 7.11 树、测点、图片

#### 树菜单

```http
GET /api/tree-menu
```

关键 ID 规则：

- 综合检测提交 `premade_point_id`
- 开距检测提交原始 `point_id`
- 螺栓检测提交原始 `point_id`
- 不要把 `opening_xxx`、`screw_xxx` 这类树展示 ID 直接提交给后端业务接口。

#### 测点最新测量

```http
GET /api/point/{point_id}/latest-measurement
```

#### 测点历史测量

```http
GET /api/point/{point_id}/history-measurements
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `days` | `integer` | 否 | `25` | 最近天数 |
| `start_date` | `string` | 否 | - | 开始日期 |
| `end_date` | `string` | 否 | - | 结束日期 |

#### 预制点最新图片

```http
GET /api/premade-point/{premade_point_id}/latest-image
```

#### 最新测量轮询

```http
GET /api/latest-measurements
```

Query：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `since` | `string` | 否 | 增量起点 |

### 7.12 巡检任务

#### 创建任务

```http
POST /api/v1/inspection/create-task
```

Body：`CreateTaskRequest`

#### 启动任务

```http
POST /api/v1/inspection/start-task/{task_id}
```

#### 任务列表

```http
GET /api/v1/inspection/tasks
GET /api/v1/inspection/list
```

Query：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `status` | `string` | 否 | - | 任务状态 |
| `page` | `integer` | 否 | `1` | 页码 |
| `per_page` | `integer` | 否 | `20` | 每页数量 |
| `start_date` | `string` | 否 | - | 开始日期 |
| `end_date` | `string` | 否 | - | 结束日期 |

#### 任务详情

```http
GET /api/v1/inspection/task/{task_id}
```

#### 取消任务

```http
POST /api/v1/inspection/cancel-task/{task_id}
```

#### 删除任务

```http
DELETE /api/v1/inspection/tasks/{task_id}
```

## 8. 协议待补接口说明

这些接口是技术协议需要，但未在 `2026-05-01` 复核的线上 `8082` OpenAPI 中确认。后续实现时建议统一使用：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

### 8.1 人员权限

```http
GET /api/access/permissions
POST /api/access/permissions
PATCH /api/access/permissions/{permissionId}
DELETE /api/access/permissions/{permissionId}
```

创建 Body：

```json
{
  "personId": "p001",
  "personName": "张三",
  "cardNo": "10001",
  "faceImageUrl": "https://example.com/face.jpg",
  "areaIds": ["r01", "r02"],
  "doorIds": ["door_a_001"],
  "validFrom": "2026-05-01T00:00:00+08:00",
  "validTo": "2026-12-31T23:59:59+08:00",
  "enabled": true
}
```

### 8.2 车辆许可

```http
GET /api/vehicle/permits
POST /api/vehicle/permits
PATCH /api/vehicle/permits/{permitId}
DELETE /api/vehicle/permits/{permitId}
```

创建 Body：

```json
{
  "plateNo": "沪A12345",
  "driverName": "李四",
  "driverPhone": "13800000000",
  "areaIds": ["r04"],
  "validFrom": "2026-05-01T08:00:00+08:00",
  "validTo": "2026-05-01T18:00:00+08:00",
  "permitType": "appointment",
  "remark": "成品库装卸作业"
}
```

### 8.3 火车信号接入

```http
POST /api/railway/signals/events
```

Body：

```json
{
  "signalId": "sig_202605010001",
  "direction": "inbound",
  "eventType": "approaching",
  "etaSeconds": 240,
  "source": "train_signal_system",
  "occurredAt": "2026-05-01T10:00:00+08:00",
  "rawPayload": {}
}
```

### 8.4 报警设备

```http
GET /api/alarm-devices
POST /api/alarm-devices/{deviceId}/command
GET /api/alarm-devices/{deviceId}/records
```

控制 Body：

```json
{
  "command": "start",
  "durationSeconds": 60,
  "reason": "火车道联动告警",
  "operator": "system"
}
```

### 8.5 视频和证据

```http
GET /api/video/cameras
GET /api/video/cameras/{cameraId}/stream-url
GET /api/video/recordings
GET /api/video/evidence
GET /api/video/evidence/{evidenceId}
POST /api/video/evidence/export
```

证据字段建议：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 证据 ID |
| `alarmId` | `string` | 告警 ID |
| `eventId` | `string` | 事件 ID |
| `cameraId` | `string` | 摄像机 ID |
| `type` | `image \| video` | 证据类型 |
| `url` | `string` | 访问地址 |
| `capturedAt` | `string` | 抓拍时间 |
| `retentionDays` | `number` | 保存天数 |

协议口径：普通录像不少于 `90` 天，告警证据不少于 `180` 天。

### 8.6 AI 识别

```http
GET /api/ai/rules
PATCH /api/ai/rules/{ruleId}
GET /api/ai/detections
```

规则建议：`person_vehicle_track`、`intrusion`、`loitering`、`helmet`、`smoking`、`illegal_parking`、`wrong_way`、`fatigue`、`occlusion`。

### 8.7 报表

```http
GET /api/reports/device-status
GET /api/reports/alarm-statistics
GET /api/reports/pass-statistics
GET /api/reports/vehicle-statistics
POST /api/reports/export
```

导出 Body：

```json
{
  "reportType": "alarm-statistics",
  "format": "xlsx",
  "filters": {
    "startTime": "2026-05-01T00:00:00+08:00",
    "endTime": "2026-05-01T23:59:59+08:00",
    "areaId": "r04"
  }
}
```

### 8.8 权限与审计

```http
GET /api/auth/me
GET /api/audit/logs
```

审计 Query：`operator`、`action`、`targetType`、`targetId`、`startTime`、`endTime`、`page`、`pageSize`。

### 8.9 配置版本和备份

```http
GET /api/config/versions
POST /api/config/versions/{versionId}/rollback
GET /api/config/backups
POST /api/config/backups
```

### 8.10 验收问题闭环

```http
GET /api/acceptance/issues
POST /api/acceptance/issues
PATCH /api/acceptance/issues/{issueId}
GET /api/acceptance/test-records
POST /api/acceptance/test-records
```

## 9. 前端接入顺序

### 9.1 本仓库 8083 设备状态控件

页面初始化：

```http
GET /api/device-status/options
GET /api/device-status/records?region=全部&device=全部
```

切换区域：

```http
GET /api/device-status/options?region=A区
GET /api/device-status/records?region=A区&device=全部
```

切换设备：

```http
GET /api/device-status/records?region=A区&device=摄像机
```

前端聚合：

```ts
const online = records.reduce((sum, item) => sum + item.online, 0);
const offline = records.reduce((sum, item) => sum + item.offline, 0);
const total = online + offline;
const onlineRate = total === 0 ? 0 : Number(((online / total) * 100).toFixed(1));
```

### 9.2 线上 8082 大屏首页

建议首屏：

```http
GET /api/dashboard/overview
GET /api/areas
GET /api/device-status/summary
GET /api/alarms?page=1&pageSize=10
GET /api/events?page=1&pageSize=10
```

### 9.3 子系统入口

| 页面入口 | 推荐接口 |
|---|---|
| 系统总体 | `/api/dashboard/overview`、`/api/areas`、`/api/device-status/*`、`/api/alarms`、`/api/events` |
| 人脸识别 | `/api/access/doors`、`/api/access/pass-records`、`/api/alarms?alarmType=access` |
| 车辆管控 | `/api/vehicle/lanes`、`/api/vehicle/pass-records`、`/api/railway/status` |
| 行车管控 | `/api/alarms`、`/api/events`，后续补 `/api/ai/*`、`/api/video/*` |
| 火灾算法 | `/api/alerts`，后续补 `/api/ai/*`、`/api/video/evidence` |

## 10. 主要差异和坑

| 问题 | 说明 | 处理方式 |
|---|---|---|
| 健康检查路径不同 | 本仓库是 `/api/health`，线上 8082 是 `/health` | 按服务区分 |
| Nacos 发布密钥位置不同 | 本仓库用 Header `X-Publish-Key`，线上 8082 OpenAPI 用 query `x_publish_key` | API client 分支处理 |
| 响应包装不统一 | 本仓库裸 JSON，8082 多数包装，部分裸 JSON | 不要写一个固定解析器套所有接口 |
| 设备筛选返回结构不同 | 本仓库 `string[]`，8082 `{id,name}[]` | 前端做适配层 |
| Nacos 不是业务库 | 不能把通行、告警、证据当配置写 | 业务数据走业务接口 |
| 待补接口不能说已实现 | AI、视频、审计、报表等还未在 8082 OpenAPI 确认 | 汇报时标注“协议建议/待实现” |

## 11. 最小可验收接口

如果只为演示和初验，最小集合建议是：

| 序号 | 方法 | 路径 | 说明 |
|---:|---|---|---|
| 1 | `GET` | `/api/dashboard/overview` | 大屏首页 |
| 2 | `GET` | `/api/areas` | 区域列表 |
| 3 | `GET` | `/api/areas/{areaId}/summary` | 区域状态 |
| 4 | `GET` | `/api/devices/list` | 设备明细 |
| 5 | `GET` | `/api/device-status/summary` | 设备汇总 |
| 6 | `GET` | `/api/access/doors` | 门禁列表 |
| 7 | `POST` | `/api/access/doors/{doorId}/command` | 门禁控制 |
| 8 | `GET` | `/api/access/pass-records` | 人员通行 |
| 9 | `GET` | `/api/vehicle/lanes` | 道闸列表 |
| 10 | `POST` | `/api/vehicle/lanes/{laneId}/command` | 道闸控制 |
| 11 | `GET` | `/api/vehicle/pass-records` | 车辆通行 |
| 12 | `GET` | `/api/railway/status` | 火车道状态 |
| 13 | `GET` | `/api/railway/linkage-records` | 火车道联动记录 |
| 14 | `GET` | `/api/alarms` | 告警列表 |
| 15 | `GET` | `/api/alarms/{alarmId}` | 告警详情 |
| 16 | `POST` | `/api/alarms/{alarmId}/actions` | 告警处置 |
| 17 | `GET` | `/api/events` | 事件列表 |
| 18 | `PATCH` | `/api/events/{eventId}/close` | 事件关闭 |

## 12. 文档维护

重新生成本仓库 OpenAPI：

```powershell
cd H:\zxcasdqwe\backend
python .\scripts\generate_openapi.py
```

复核线上 8082 OpenAPI：

```powershell
Invoke-WebRequest -Uri "http://101.43.49.78:8082/openapi.json" -OutFile ".\_fresh_8082_openapi.json"
```

生成文档站：

```powershell
cd H:\zxcasdqwe
python .\build_blog_docs.py
```

## 13. 一句话总结

Nacos 在这里是配置中心；本仓库 `8000` 是 Nacos 配置桥和 8083 设备状态联调服务；线上 `8082` 是业务 API 主体；AI、视频、报表、审计、验收闭环等接口目前应按协议待补能力管理。

## 14. 团队代码规范

本节是团队协作的统一规则。新同学先按这里写，老同学改接口也按这里检查，避免代码、接口、文档各说各话。

### 14.1 仓库目录职责

| 路径 | 职责 | 修改规则 |
|---|---|---|
| `backend/app/main.py` | 本仓库 FastAPI 实现 | 新增/修改接口必须同步 OpenAPI 和文档 |
| `backend/openapi.json` | 本仓库 OpenAPI 导出文件 | 不手改，使用脚本重新生成 |
| `backend/scripts/generate_openapi.py` | OpenAPI 生成脚本 | 只有生成逻辑变化时才改 |
| `backend/.env.example` | 后端环境变量样例 | 新增环境变量必须同步这里 |
| `frontend/index.html` | 本仓库演示前端 | 只做演示和联调，不承载复杂业务 |
| `frontend/nginx.conf` | 前端 Nginx 代理 | `/api/*` 代理到 `nacos-api:8000` |
| `docker-compose.yml` | 本地容器编排 | 服务名、端口、依赖变更必须写清楚 |
| `COMPLETE_API_DOC.md` | 团队 API 和规范总文档 | 接口变更必须同步 |
| `PROTOCOL_API_GAP_AND_SUPPLEMENT.md` | 协议缺口和建议 API | 只写方案，不直接代表已实现 |

### 14.2 Python/FastAPI 代码规范

后端当前技术栈：

- `Python 3.12`
- `FastAPI`
- `Pydantic`
- `httpx`
- `python-dotenv`

编码规则：

| 规则 | 要求 |
|---|---|
| 函数命名 | 使用 `snake_case`，例如 `get_device_status_records` |
| 变量命名 | 使用 `snake_case`，例如 `data_id`、`page_size` |
| Pydantic 模型 | 类名使用 `PascalCase`，例如 `DeviceStatusRecord` |
| API 出参字段 | 面向前端使用 `camelCase`，例如 `dataId`、`updatedAt` |
| Python 内部字段 | 使用 `snake_case`，通过 `Field(alias="camelCase")` 对外 |
| 类型标注 | 新代码必须写类型标注 |
| 默认值 | Query、Body 字段默认值必须显式写出 |
| 错误处理 | 业务错误用 `HTTPException`，不要直接返回字符串错误 |
| 注释 | 只给复杂逻辑加短注释，不写无意义注释 |

字段别名示例：

```py
class DeviceStatusRecordsResponse(BaseModel):
    records: list[DeviceStatusRecord]
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}
```

新增接口模板：

```py
@app.get(
    "/api/example/items",
    tags=["example"],
    summary="Get example items",
    response_model=ExampleItemsResponse,
)
async def get_example_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, alias="pageSize", ge=1, le=200),
) -> ExampleItemsResponse:
    return ExampleItemsResponse(items=[], page=page, pageSize=page_size, total=0)
```

禁止事项：

- 不要把密钥写死在代码里。
- 不要在接口里返回 Python 异常堆栈给前端。
- 不要新增没有 `response_model` 的本仓库接口，除非返回结构确实不可固定。
- 不要直接让前端访问 Nacos 原生接口。
- 不要把人员、车辆、告警、视频证据等业务流水数据写进 Nacos。

### 14.3 API 设计规范

路径规则：

| 类型 | 规则 | 示例 |
|---|---|---|
| 集合列表 | 复数名词 | `GET /api/areas` |
| 单个资源 | 路径参数 | `GET /api/devices/{deviceId}` |
| 资源动作 | 子路径动词 | `POST /api/alarms/{alarmId}/actions` |
| 控制命令 | 使用 `command` | `POST /api/access/doors/{doorId}/command` |
| 查询过滤 | 使用 Query | `GET /api/alarms?status=new&page=1&pageSize=20` |

命名规则：

- 路径使用小写和中划线：`device-status`、`pass-records`。
- Query 和 JSON 字段给前端使用 `camelCase`：`pageSize`、`regionId`。
- Python 内部变量使用 `snake_case`：`page_size`、`region_id`。
- ID 字段统一叫 `xxxId`，例如 `areaId`、`deviceId`、`alarmId`。

响应规则：

| 服务 | 响应规则 |
|---|---|
| 本仓库 `8000` | 维持当前裸 JSON，不强行改包装 |
| 线上 `8082` 新业务接口 | 推荐统一 `code/success/message/data` |
| 列表接口 | 推荐 `items/page/pageSize/total` |
| 控制接口 | 必须返回 `commandId`、`status`、`createdAt` |

统一包装建议：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {},
  "traceId": "optional-trace-id"
}
```

分页建议：

```json
{
  "items": [],
  "page": 1,
  "pageSize": 20,
  "total": 0
}
```

错误码约定：

| 状态码 | 用法 |
|---|---|
| `200` | 成功 |
| `400` | 业务参数非法，例如未知区域、未知设备 |
| `401` | 未认证或发布密钥错误 |
| `403` | 无权限 |
| `404` | 资源或字段不存在 |
| `409` | 状态冲突，例如重复操作 |
| `422` | 请求结构错误或字段校验失败 |
| `500` | 服务端未预期异常 |
| `502` | 下游服务异常，例如 Nacos 调用失败 |
| `503` | 服务未配置或依赖不可用 |

### 14.4 Nacos 配置规范

Nacos 命名：

| 项 | 规则 | 示例 |
|---|---|---|
| `dataId` | 小写中划线，带后缀 | `device-status.json` |
| `group` | 默认使用 `DEFAULT_GROUP` | `DEFAULT_GROUP` |
| `tenant` | 没有 namespace 时传空或不传 | `null` |
| 配置类型 | JSON 优先 | `json` |

配置内容规则：

- JSON 必须可解析。
- 业务字段使用 `camelCase`。
- 配置里要能看出模块名，例如 `deviceStatus`。
- 数字不要写成字符串，例如 `"online": "1"` 不推荐。
- 不要在配置里放账号密码、Token、私钥。

设备状态配置标准：

```json
{
  "deviceStatus": {
    "refreshSeconds": 30,
    "records": [
      {
        "region": "A区",
        "device": "摄像机",
        "online": 86,
        "offline": 6
      }
    ]
  }
}
```

发布配置前检查：

1. `dataId` 是否正确。
2. `group` 是否正确。
3. JSON/YAML 是否能解析。
4. 是否带了 `X-Publish-Key`。
5. 是否误把生产敏感信息写入配置。

### 14.5 前端代码规范

当前演示前端是原生 HTML/CSS/JS，后续正式前端如果使用 Vue/React，也应保留这些接口规则。

请求规则：

- 页面内调用本仓库服务时优先使用相对路径 `/api/...`。
- 不要在浏览器里写死 Nacos 原生地址。
- 所有 `fetch` 必须判断 `resp.ok`。
- 解析响应时要区分裸 JSON 和包装 JSON。
- 请求失败时保留上一次成功数据，不要直接清空大屏。

推荐封装：

```ts
async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, options);
  const data = await resp.json().catch(() => null);
  if (!resp.ok) {
    throw new Error(data?.detail || data?.message || `HTTP ${resp.status}`);
  }
  return data as T;
}
```

解析规则：

```ts
function unwrapResponse<T>(response: any): T {
  if (response && typeof response === "object" && "success" in response && "data" in response) {
    if (!response.success) throw new Error(response.message || "请求失败");
    return response.data as T;
  }
  return response as T;
}
```

UI 联调规则：

- 加载中要有状态。
- 失败要有轻提示。
- 自动刷新要在页面卸载时清理定时器。
- 大屏类页面不要因为某个接口失败整体白屏。
- 时间、数量、百分比都在前端做空值兜底。

### 14.6 安全规范

| 类型 | 规则 |
|---|---|
| 发布密钥 | 只放 `.env`，不提交真实值 |
| Nacos 账号 | 只放服务端环境变量 |
| 前端代码 | 不写密钥、不写 Nacos 账号 |
| 日志 | 不打印完整密钥、Token、密码 |
| 控制接口 | 必须记录操作人、原因、时间 |
| 跨域 | 只允许必要来源，不长期使用 `*` |

本仓库 `.env.example` 只放示例：

```env
PUBLISH_API_KEY=change-this-to-a-strong-key
```

真实环境必须改成强密钥。

### 14.7 Git 和提交规范

当前目录不是 git 仓库，但团队正式协作时建议按下面规则。

分支命名：

| 类型 | 示例 |
|---|---|
| 功能 | `feature/device-status-summary` |
| 修复 | `fix/nacos-publish-key` |
| 文档 | `docs/api-team-guide` |
| 重构 | `refactor/config-client` |

提交信息：

```text
docs: update team API and code guide
feat: add device status summary endpoint
fix: handle missing Nacos config field
```

提交前必须检查：

1. 代码能启动。
2. OpenAPI 已重新生成。
3. API 文档已同步。
4. `.env`、密钥、临时文件没有提交。
5. 新增接口有示例请求和响应。

### 14.8 测试和联调规范

后端自测最小清单：

```powershell
curl http://localhost:8000/api/health
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/records?region=全部&device=全部"
curl "http://localhost:8000/api/nacos/config?dataId=&group=DEFAULT_GROUP"
```

线上接口复核：

```powershell
curl http://101.43.49.78:8082/health
curl http://101.43.49.78:8082/api/info
curl http://101.43.49.78:8082/api/dashboard/overview
```

联调记录必须写清：

- 调用时间。
- 环境地址。
- 请求路径和参数。
- 响应状态码。
- 失败时的错误体。
- 前端页面表现。
- 责任人和下一步。

### 14.9 文档维护规范

任何接口变化都必须同步三处：

1. 源码：`backend/app/main.py` 或线上业务后端对应代码。
2. OpenAPI：`backend/openapi.json` 或线上 `/openapi.json`。
3. 文档：`COMPLETE_API_DOC.md`。

本仓库 OpenAPI 生成：

```powershell
cd H:\zxcasdqwe\backend
python .\scripts\generate_openapi.py
```

文档中接口状态必须写清楚：

| 状态 | 说明 |
|---|---|
| 已实现 | OpenAPI 中能看到，接口能访问 |
| 联调中 | 路径已定，字段可能调整 |
| 协议建议 | 文档方案，还没确认代码 |
| 废弃 | 不建议继续接入 |

### 14.10 Code Review 检查清单

评审接口改动时按这张表过：

| 检查项 | 要求 |
|---|---|
| 路径命名 | 是否符合 REST 和模块分组 |
| 参数命名 | Query/JSON 是否 `camelCase` |
| Python 命名 | 内部是否 `snake_case` |
| 响应模型 | 是否有明确结构 |
| 错误处理 | 是否返回合适状态码 |
| 安全 | 是否泄露密钥或敏感信息 |
| Nacos | 是否把 Nacos 当配置中心而不是业务库 |
| 前端兼容 | 是否破坏已有字段 |
| 文档 | 是否同步本文件 |
| OpenAPI | 是否已重新生成或复核 |

## 15. 顺序

第一天先按这个顺序看：

1. 看第 `0` 节，知道当前有 `8000` 和 `8082` 两套口径。
2. 看第 `1` 节，理解 Nacos 只是配置中心。
3. 本地启动服务：`docker compose up -d --build`。
4. 打开 `http://localhost:8000/docs`，看本仓库 5 个接口。
5. 打开 `http://101.43.49.78:8082/docs`，看线上业务接口。
6. 用 curl 调一次 `/api/health`、`/api/device-status/options`、`/api/device-status/records`。
7. 看第 `14` 节，按团队代码规范改第一处小需求。

最容易混淆的三件事：

| 问题 | 正确理解 |
|---|---|
| Nacos 是不是数据库 | 不是，它是配置中心 |
| 本仓库是不是完整业务后端 | 不是，本仓库只是配置桥和联调接口 |
| 文档里所有接口是不是都已实现 | 不是，要看“已实现/协议建议”状态 |
