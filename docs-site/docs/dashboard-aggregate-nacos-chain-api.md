---
id: dashboard-aggregate-nacos-chain-api
title: 大屏聚合与 Nacos 链路补齐 API
slug: /dashboard-aggregate-nacos-chain-api
---

# 大屏聚合与 Nacos 链路补齐 API 文档

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-DASHBOARD-NACOS-1.0` |
| 文档集 | `DOC-2026.05.08` |
| 适用系统 | `LEGACY-FE-8083` + FastAPI 后端 + Nacos 2.5.1/3.x |
| 当前状态 | 本轮已补齐，可进入前端联调 |
| 更新日期 | `2026-05-08` |

## 1. 结论

本轮补齐两个关键缺口：

| 缺口 | 已落地方式 | 前端怎么用 |
|---|---|---|
| 大屏右侧事件、风险预警、中间区域数据缺少统一接口 | `GET /api/dashboard/aggregate`，并同步扩展 `GET /api/dashboard/overview` | 页面首屏只调一个聚合接口，不需要到处拼接口 |
| Python 模拟设备没有进入 Nacos 链路 | `POST /api/simulator/nacos-sync` + 后台自动同步 | FastAPI 默认可从 Nacos 读设备状态，再统一输出给大屏 |

完整链路：

```text
Python 状态机模拟设备
  -> 写入 Nacos 配置 factory.hardware.snapshot.json
  -> FastAPI 读取 Nacos
  -> /api/dashboard/aggregate 输出大屏数据
  -> 8083 前端渲染中心区域、事件、风险、设备状态
```

## 2. 当前已落地 API 基线

当前 FastAPI OpenAPI 共 `15` 个操作：

| 方法 | 路径 | 状态 | 用途 |
|---|---|---|---|
| `GET` | `/api/health` | 已落地 | 服务健康检查 |
| `GET` | `/api/nacos/config` | 已落地 | 读取 Nacos 配置 |
| `POST` | `/api/nacos/config` | 已落地 | 发布 Nacos 配置 |
| `GET` | `/api/device-status/options` | 已落地 | 8083 设备状态筛选项 |
| `GET` | `/api/device-status/records` | 已落地 | 8083 设备状态明细 |
| `GET` | `/api/device-status/summary` | 已落地 | 设备状态汇总 |
| `GET` | `/api/dashboard/overview` | 已扩展 | 兼容旧大屏概览，并返回聚合数据 |
| `GET` | `/api/dashboard/aggregate` | 新增 | 大屏完整聚合接口 |
| `GET` | `/api/subsystems` | 新增 | 底部四个子系统入口 |
| `GET` | `/api/simulator/summary` | 已扩展 | 模拟器汇总，包含 Nacos 同步状态 |
| `GET` | `/api/simulator/devices` | 已落地 | 模拟设备列表 |
| `GET` | `/api/simulator/devices/{device_id}` | 已落地 | 模拟设备详情 |
| `POST` | `/api/simulator/tick` | 已扩展 | 推进模拟器，可选同步 Nacos |
| `POST` | `/api/simulator/devices/{device_id}/command` | 已落地 | 模拟设备命令 |
| `POST` | `/api/simulator/nacos-sync` | 新增 | 手动写入 Nacos 快照 |

## 3. 大屏聚合接口

### 3.1 `GET /api/dashboard/aggregate`

用途：给 8083 大屏首屏使用，一次返回顶部指标、设备状态、中间区域态势、右侧事件、风险预警和硬件快照。

响应结构：

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
    "deviceRecords": [],
    "deviceRegions": ["全部", "A区"],
    "deviceTypes": ["全部", "摄像机"],
    "deviceStatus": {
      "summary": {
        "totalDevices": 143,
        "onlineDevices": 130,
        "offlineDevices": 13,
        "onlineRate": 90.91
      },
      "records": [],
      "regions": [],
      "devices": [],
      "updatedAt": "2026-05-08T20:00:00+08:00"
    },
    "centerScene": {
      "sceneType": "factory-area-overview",
      "mapMode": "2d",
      "nodes": [],
      "links": []
    },
    "areas": [],
    "eventBoard": {
      "total": 8,
      "unhandled": 8,
      "critical": 2,
      "warning": 6,
      "items": []
    },
    "eventList": [],
    "riskWarnings": [],
    "hardware": {
      "total": 143,
      "items": []
    },
    "subsystems": [
      {
        "id": "face",
        "name": "人脸识别",
        "key": "faceRecognition",
        "url": null,
        "enabled": false,
        "description": "人员进出、识别记录和门禁联动"
      }
    ],
    "dataSource": "nacos",
    "nacos": {
      "enabled": true,
      "dataId": "factory.hardware.snapshot.json",
      "group": "DEFAULT_GROUP",
      "field": "deviceStatus.records"
    },
    "updatedAt": "2026-05-08T20:00:00+08:00"
  }
}
```

### 3.2 `GET /api/dashboard/overview`

`overview` 继续保留给现有 8083 前端使用，返回字段与 `aggregate` 保持同源。前端如果暂时只认旧字段，仍可读取：

```text
data.onlineAccess
data.areaTotal
data.vehiclesOnSite
data.railStatus
data.deviceRecords
data.deviceRegions
data.deviceTypes
```

前端改造时建议直接改用 `aggregate`，语义更清晰。

## 4. Python 模拟器写 Nacos

### 4.1 自动同步

开启环境变量：

```env
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
SIMULATOR_NACOS_SYNC_ENABLED=true
SIMULATOR_NACOS_SYNC_INTERVAL_TICKS=1
SIMULATOR_NACOS_DATA_ID=factory.hardware.snapshot.json
SIMULATOR_NACOS_GROUP=DEFAULT_GROUP
```

效果：每次模拟器 tick 后，FastAPI 自动把当前硬件快照写入 Nacos。

### 4.2 手动同步

```bash
curl -X POST "http://127.0.0.1:8000/api/simulator/nacos-sync" \
  -H "X-Publish-Key: 你的PUBLISH_API_KEY"
```

### 4.3 推进并同步

```bash
curl -X POST "http://127.0.0.1:8000/api/simulator/tick?steps=1&syncNacos=true"
```

### 4.4 Nacos 写入内容

默认写入：

```text
dataId: factory.hardware.snapshot.json
group: DEFAULT_GROUP
type: json
```

核心结构：

```json
{
  "schemaVersion": "factory.hardware.snapshot.v1",
  "source": "python-simulator",
  "tick": 1,
  "updatedAt": "2026-05-08T20:00:00+08:00",
  "hardware": {
    "summary": {},
    "items": []
  },
  "deviceStatus": {
    "summary": {},
    "records": []
  }
}
```

## 5. FastAPI 从 Nacos 读设备状态

开启环境变量：

```env
DEVICE_STATUS_SOURCE=nacos
DEVICE_STATUS_NACOS_DATA_ID=factory.hardware.snapshot.json
DEVICE_STATUS_NACOS_GROUP=DEFAULT_GROUP
DEVICE_STATUS_NACOS_FIELD=deviceStatus.records
NACOS_READ_FALLBACK_TO_SIMULATOR=true
```

读取顺序：

1. 读取 Nacos `factory.hardware.snapshot.json`
2. 提取 `deviceStatus.records`
3. 聚合生成 `deviceStatus`、`areas`、`eventBoard`、`riskWarnings`、`centerScene`
4. 如果 Nacos 暂时不可用，并且 `NACOS_READ_FALLBACK_TO_SIMULATOR=true`，回退到本地模拟器，避免大屏接口 500

## 6. Nacos 版本配置

101 服务器当前 Nacos 是 `nacos/nacos-server:v2.5.1`，应使用：

```env
NACOS_API_VERSION=v1
NACOS_BASE_URL=http://host.docker.internal:8848/nacos
```

如果后端容器和 Nacos 容器在同一个 Docker 网络，并且 Nacos 服务名是 `nacos`：

```env
NACOS_BASE_URL=http://nacos:8848/nacos
```

如果使用本仓库 `docker-compose.server.yml` 拉起 Nacos 3.x，则使用：

```env
NACOS_API_VERSION=v3
NACOS_BASE_URL=http://nacos:8080
```

## 7. 前端需要改的点

| 模块 | 当前问题 | 对接方式 |
|---|---|---|
| 数据源 | 8083 默认还是本地 mock | 默认切到接口模式，调用 `/api/dashboard/aggregate` |
| 中间主画面 | 当前是空框 | 使用 `data.centerScene.nodes` 和 `data.centerScene.links` 渲染区域态势 |
| 事件看板 | 当前是空框 | 使用 `data.eventBoard.items` |
| 事件列表 | 当前是空框 | 使用 `data.eventList` |
| 风险预警 | 当前是空框 | 使用 `data.riskWarnings` |
| 设备状态 | 已有环图 | 使用 `data.deviceStatus.summary` 和 `data.deviceRecords` |
| 子系统入口 | 当前不应写 `localhost:5173` | 使用 `data.subsystems` 或 `GET /api/subsystems`，URL 从后端环境变量下发 |

子系统 URL 建议：

```env
SUBSYSTEM_BASE_URL=
SUBSYSTEM_FACE_URL=
SUBSYSTEM_VEHICLE_URL=
SUBSYSTEM_RAIL_URL=
SUBSYSTEM_FIRE_URL=
```

如果 `SUBSYSTEM_BASE_URL` 已配置但单个 `SUBSYSTEM_*_URL` 未配置，后端会按 `/face/`、`/vehicle/`、`/rail/`、`/fire/` 生成同域入口；如果都未配置，则对应入口 `enabled=false`，前端应置灰。

## 8. 验收命令

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/simulator/summary
curl http://127.0.0.1:8000/api/dashboard/aggregate
curl http://127.0.0.1:8000/api/device-status/records
```

写入 Nacos：

```bash
curl -X POST "http://127.0.0.1:8000/api/simulator/nacos-sync" \
  -H "X-Publish-Key: 你的PUBLISH_API_KEY"
```

读取 Nacos：

```bash
curl "http://127.0.0.1:8000/api/nacos/config?dataId=factory.hardware.snapshot.json&group=DEFAULT_GROUP"
```
