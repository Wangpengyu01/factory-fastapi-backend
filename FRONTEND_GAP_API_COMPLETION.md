# 8083 前端缺口 API 补齐文档

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-FE-GAP-API-1.0` |
| 文档集 | `DOC-2026.05.09` |
| 适用系统 | 服务器上的 `8083` 大屏前端 + FastAPI 后端 |
| 当前状态 | 给前端补齐中间主画面、右侧面板、子系统入口和接口模式的 API 对接口径 |
| 更新日期 | `2026-05-09` |

## 1. 本轮要解决的问题

当前 8083 前端已经能打开，也能显示顶部指标和设备状态环图，但还存在这些缺口：

| 缺口 | 现状 | API 补齐方向 |
|---|---|---|
| 中间主画面空框 | 没有厂区区域态势、地图、视频或 3D 数据 | 用 `GET /api/dashboard/aggregate` 的 `centerScene`，必要时拆出 `GET /api/dashboard/center-scene` |
| 事件看板空框 | 没有事件计数、最新事件、严重等级 | 用 `eventBoard`，数据来源聚合 `/api/alarms`、`/api/alerts`、`/api/ai/detections` |
| 事件列表空框 | 没有统一事件流 | 用 `eventList`，聚合报警、门禁、车辆、铁路、AI 事件 |
| 风险预警空框 | 没有风险等级和预警说明 | 用 `riskWarnings`，聚合设备在线率、报警统计和铁路状态 |
| 底部四个子系统仍指向 `localhost:5173` | 服务器上点击不可用 | 用 `subsystems` 由后端或环境变量统一下发真实 URL |
| 默认数据源还是 mock | 首屏数字可能来自本地模拟 | 前端默认使用接口模式，首屏调 `/api/dashboard/aggregate` |
| 前端只用了少量接口 | 已有报警、区域、设备、视频、报表接口没进页面 | 按本文档的页面模块映射逐步接入 |

## 2. 首屏推荐只调一个接口

### `GET /api/dashboard/aggregate`

用途：8083 大屏首屏聚合接口。前端首次加载只调这一个接口，避免中间画面、右侧面板、设备状态分别到处拼接口。

响应字段：

| 字段 | 用途 | 前端模块 |
|---|---|---|
| `onlineAccess` | 在线门禁数量 | 顶部指标 |
| `areaTotal` | 区域总人数或区域态势总数 | 顶部指标 |
| `vehiclesOnSite` | 场内车辆数 | 顶部指标 |
| `railStatus` | 火车道状态 | 顶部指标 |
| `deviceStatus.summary` | 设备总数、在线数、离线数、在线率 | 左侧设备状态环图 |
| `deviceRecords` | 区域 + 设备类型 + 在线/离线记录 | 左侧设备状态筛选和图表 |
| `centerScene` | 中间主画面区域态势 | 中间厂区平面/地图/3D |
| `areas` | 区域汇总 | 中间区域卡片、悬浮提示 |
| `eventBoard` | 事件看板统计和最新事件 | 右侧事件看板 |
| `eventList` | 统一事件列表 | 右侧事件列表 |
| `riskWarnings` | 风险预警列表 | 右侧风险预警 |
| `hardware.items` | 设备快照明细 | 调试、详情弹窗、地图点位 |
| `subsystems` | 四个子系统入口 | 底部模块按钮 |

示例：

```json
{
  "code": 200,
  "success": true,
  "message": "获取大屏聚合数据成功",
  "data": {
    "onlineAccess": 24,
    "areaTotal": 134,
    "vehiclesOnSite": 24,
    "railStatus": "idle",
    "deviceStatus": {
      "summary": {
        "totalDevices": 143,
        "onlineDevices": 130,
        "offlineDevices": 13,
        "onlineRate": 90.91
      },
      "records": []
    },
    "centerScene": {
      "sceneType": "factory-area-overview",
      "mapMode": "2d",
      "nodes": [],
      "links": []
    },
    "eventBoard": {
      "total": 8,
      "unhandled": 8,
      "critical": 2,
      "warning": 6,
      "items": []
    },
    "eventList": [],
    "riskWarnings": [],
    "subsystems": []
  }
}
```

## 3. 中间主画面 API

### 3.1 推荐字段：`data.centerScene`

中间主画面先不要让前端直接拼区域、视频、设备、报警。后端应在聚合接口里返回可直接渲染的 `centerScene`。

字段建议：

| 字段 | 类型 | 说明 |
|---|---|---|
| `sceneType` | `string` | `factory-area-overview`、`video-wall`、`three-scene` |
| `mapMode` | `string` | `2d`、`video`、`3d` |
| `nodes[]` | `array` | 区域、设备、摄像头、风险点 |
| `links[]` | `array` | 区域之间或设备联动关系 |
| `updatedAt` | `string` | 更新时间 |

`nodes[]` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 区域或设备 ID |
| `name` | `string` | 显示名称 |
| `type` | `string` | `area`、`device`、`camera`、`risk` |
| `x` / `y` | `number` | 百分比坐标，前端可直接定位 |
| `status` | `string` | `normal`、`warning`、`critical` |
| `onlineRate` | `number` | 区域或设备在线率 |
| `eventCount` | `number` | 当前事件数 |

### 3.2 可复用现有 API

如果中间主画面后续要做点击详情，可以接这些现有 API：

| API | 用途 |
|---|---|
| `GET /api/areas` | 区域列表 |
| `GET /api/areas/{areaId}/summary` | 区域汇总 |
| `GET /api/devices` | 设备列表 |
| `GET /api/devices/{deviceId}` | 设备详情 |
| `GET /api/video/cameras` | 摄像头列表 |
| `GET /api/video/cameras/{cameraId}/stream-url` | 摄像头播放地址 |
| `GET /api/alarms` | 区域关联报警 |

### 3.3 如需单独拆接口

后续如果中间主画面刷新频率和其他面板不同，可以新增：

```text
GET /api/dashboard/center-scene
```

但首版建议仍从 `/api/dashboard/aggregate` 取，减少前端联调成本。

## 4. 右侧事件看板 API

### 4.1 推荐字段：`data.eventBoard`

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `total` | `number` | 当前事件总数 |
| `unhandled` | `number` | 未处理事件数 |
| `critical` | `number` | 严重事件数 |
| `warning` | `number` | 警告事件数 |
| `items[]` | `array` | 最新事件，建议 5 到 8 条 |

`items[]` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 事件 ID |
| `eventType` | `string` | `alarm`、`access`、`vehicle`、`railway`、`ai`、`device_status` |
| `level` | `string` | `info`、`warning`、`critical` |
| `title` | `string` | 标题 |
| `areaName` | `string` | 区域 |
| `deviceName` | `string` | 设备 |
| `status` | `string` | `active`、`processing`、`closed` |
| `occurredAt` | `string` | 发生时间 |

### 4.2 来源 API

| API | 接入内容 |
|---|---|
| `GET /api/alarms` | 报警事件主来源 |
| `GET /api/alerts` | 轻量预警事件 |
| `GET /api/ai/detections` | AI 检测事件 |
| `GET /api/railway/signals/events` | 铁路信号事件 |
| `GET /api/access/pass-records` | 门禁通行事件 |
| `GET /api/vehicle/pass-records` | 车辆通行事件 |

## 5. 右侧事件列表 API

### 推荐字段：`data.eventList`

事件列表不建议前端分别拉报警、车辆、门禁、AI 再自己排序。后端聚合成统一事件流。

查询建议：

```text
GET /api/events?areaId=&eventType=&level=&status=&pageNo=1&pageSize=20
```

如果暂时不新增 `/api/events` 列表接口，则先由 `/api/dashboard/aggregate` 返回 `eventList`。

列表字段与 `eventBoard.items[]` 保持一致，额外增加：

| 字段 | 类型 | 说明 |
|---|---|---|
| `description` | `string` | 事件描述 |
| `source` | `string` | `alarm`、`access`、`vehicle`、`railway`、`ai` |
| `actionRequired` | `boolean` | 是否需要处理 |
| `closedAt` | `string/null` | 关闭时间 |

详情复用：

```text
GET /api/events/{eventId}
POST /api/events/{eventId}/close
POST /api/alarms/{alarmId}/actions
```

## 6. 右侧风险预警 API

### 推荐字段：`data.riskWarnings`

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 风险 ID |
| `level` | `string` | `normal`、`warning`、`critical` |
| `title` | `string` | 风险标题 |
| `areaName` | `string` | 区域 |
| `metric` | `string` | 指标名，如 `onlineRate`、`railStatus` |
| `value` | `number/string` | 当前值 |
| `threshold` | `number/string` | 阈值 |
| `description` | `string` | 说明 |
| `updatedAt` | `string` | 更新时间 |

来源 API：

| API | 接入内容 |
|---|---|
| `GET /api/reports/device-status` | 设备在线率和离线统计 |
| `GET /api/reports/alarm-statistics` | 报警统计 |
| `GET /api/railway/status` | 铁路/火车道状态 |
| `GET /api/alarm-devices` | 报警设备状态 |
| `GET /api/device-status/summary` | 当前设备在线率 |

## 7. 底部四个子系统入口 API

当前四个子系统入口不能继续写死 `localhost:5173`。应由接口或部署环境统一配置。

### 7.1 已实现字段：`data.subsystems`

可直接放进 `/api/dashboard/aggregate`：

```json
{
  "subsystems": [
    {
      "id": "face",
      "name": "人脸识别",
      "key": "faceRecognition",
      "url": "https://face.example.com/",
      "enabled": true,
      "description": "人员进出、识别记录和门禁联动"
    },
    {
      "id": "vehicle",
      "name": "车辆管控",
      "key": "vehicleControl",
      "url": "https://vehicle.example.com/",
      "enabled": true,
      "description": "车辆识别、道闸、场内车辆状态"
    },
    {
      "id": "rail",
      "name": "行车管控",
      "key": "railControl",
      "url": "https://rail.example.com/",
      "enabled": true,
      "description": "铁路道口、行车状态和道闸安全联动"
    },
    {
      "id": "fire",
      "name": "火灾算法",
      "key": "fireAlgorithm",
      "url": "https://fire.example.com/",
      "enabled": true,
      "description": "烟感温感、视频算法和火灾预警"
    }
  ]
}
```

### 7.2 已实现独立接口

```text
GET /api/subsystems
```

用途：单独返回底部四个子系统入口。`url` 来自后端 `SUBSYSTEM_*` 环境变量；未配置时返回 `url: null`、`enabled: false`，前端应置灰，不要回退到 `localhost`。

字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | `face`、`vehicle`、`rail`、`fire` |
| `name` | `string` | 按钮显示名 |
| `key` | `string` | 前端稳定识别键 |
| `url` | `string/null` | 服务器可访问地址，禁止 localhost；未配置为 `null` |
| `enabled` | `boolean` | 是否允许点击 |
| `description` | `string` | 子系统说明 |

### 7.3 部署变量建议

后端环境变量：

```env
SUBSYSTEM_BASE_URL=
SUBSYSTEM_FACE_URL=
SUBSYSTEM_VEHICLE_URL=
SUBSYSTEM_RAIL_URL=
SUBSYSTEM_FIRE_URL=
```

如果前端不读 `/api/subsystems`，也至少改成构建变量：

```env
VITE_FACE_SYSTEM_URL=
VITE_VEHICLE_SYSTEM_URL=
VITE_RAIL_SYSTEM_URL=
VITE_FIRE_SYSTEM_URL=
```

验收要求：构建后的前端产物里不能再出现：

```text
localhost:5173
```

## 8. 默认接口模式

这不是后端 API 缺口，是前端默认状态问题。

前端需要改：

| 项 | 当前 | 应改为 |
|---|---|---|
| 默认数据源 | `mock` | `api` |
| 首屏接口 | 本地默认值 | `GET /api/dashboard/aggregate` |
| 失败处理 | 空框 | 显示接口错误或降级提示 |

验收：

1. 打开 `http://服务器IP:8083/`
2. 浏览器 Network 里能看到 `/api/dashboard/aggregate`
3. 页面不用按 F8 也能显示接口数据
4. 顶部指标、设备状态、中间主画面、右侧三个面板都来自接口

## 9. 页面模块与 API 映射

| 前端区域 | 首选 API | 详情/扩展 API |
|---|---|---|
| 顶部运行指标 | `GET /api/dashboard/aggregate` | `/api/dashboard/overview` |
| 左侧设备状态 | `GET /api/dashboard/aggregate` | `/api/device-status/summary`、`/api/device-status/records` |
| 中间主画面 | `GET /api/dashboard/aggregate` 的 `centerScene` | `/api/areas`、`/api/devices`、`/api/video/cameras` |
| 事件看板 | `GET /api/dashboard/aggregate` 的 `eventBoard` | `/api/alarms`、`/api/alerts`、`/api/ai/detections` |
| 事件列表 | `GET /api/dashboard/aggregate` 的 `eventList` | `/api/events/{eventId}`、`/api/alarms/{alarmId}/actions` |
| 风险预警 | `GET /api/dashboard/aggregate` 的 `riskWarnings` | `/api/reports/*`、`/api/railway/status` |
| 底部子系统 | `GET /api/dashboard/aggregate` 的 `subsystems` | `GET /api/subsystems` |
| 视频弹窗 | `GET /api/video/cameras` | `GET /api/video/cameras/{cameraId}/stream-url` |
| 报表页 | `GET /api/reports/*` | `GET /api/reports/export` |

## 10. 后端补齐优先级

| 优先级 | API/字段 | 原因 |
|---|---|---|
| P0 | `/api/dashboard/aggregate.centerScene` | 解决中间主画面空框 |
| P0 | `/api/dashboard/aggregate.eventBoard/eventList/riskWarnings` | 解决右侧三个空面板 |
| P0 | `/api/dashboard/aggregate.subsystems` 或 `/api/subsystems` | 解决底部 localhost 跳转 |
| P1 | `/api/events` 列表接口 | 支撑事件列表分页和筛选 |
| P1 | `/api/dashboard/center-scene` | 中间主画面需要独立刷新时再拆 |
| P2 | `/api/reports/*` 接入右侧预警 | 做统计分析和趋势图 |

## 11. 前端验收清单

| 检查项 | 通过标准 |
|---|---|
| 默认接口模式 | 首屏自动请求 `/api/dashboard/aggregate` |
| 中间主画面 | 有区域态势/地图/视频/3D 的至少一种可视化，不再是空框 |
| 事件看板 | 显示事件总数、未处理数、严重/警告数、最新事件 |
| 事件列表 | 有统一事件流，支持空状态 |
| 风险预警 | 有风险等级、区域、指标和说明 |
| 子系统入口 | 不再出现 `localhost:5173`，未配置时显示禁用或维护状态 |
| 接口异常 | 后端不可用时显示错误状态，不白屏 |
| OpenAPI | 文档站能看到新增 API 文档 |
