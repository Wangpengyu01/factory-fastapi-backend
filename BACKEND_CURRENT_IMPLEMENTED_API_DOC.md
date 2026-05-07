# 后端开发现阶段 API 落地文档

整理日期：`2026-05-07`

本文档面向后端开发同学，说明当前阶段已经落地的 FastAPI 接口、数据结构、运行方式、模拟器能力，以及后续全量接口的实现边界。

## 1. 当前阶段结论

当前后端已经落地的是一套“可让 8083 前端先取数、可让硬件未接入时先模拟状态”的最小闭环。

已落地能力：

| 能力 | 状态 | 说明 |
|---|---|---|
| FastAPI 服务 | 已落地 | 入口：`backend/app/main.py` |
| Swagger | 已落地 | `GET /docs` |
| OpenAPI 导出 | 已落地 | `backend/openapi.json` |
| 健康检查 | 已落地 | `GET /api/health` |
| 8083 大屏概览 | 已落地 | `GET /api/dashboard/overview` |
| 设备状态筛选项 | 已落地 | `GET /api/device-status/options` |
| 设备状态汇总 | 已落地 | `GET /api/device-status/summary` |
| 设备状态明细 | 已落地 | `GET /api/device-status/records` |
| Nacos 配置读取 | 已落地 | `GET /api/nacos/config` |
| Nacos 配置发布 | 已落地 | `POST /api/nacos/config` |
| 硬件状态机模拟器 | 已落地 | `/api/simulator/*` |

当前已落地接口共 `12` 个操作。

## 2. 代码位置

| 文件 | 说明 |
|---|---|
| `backend/app/main.py` | 当前 FastAPI 主入口和路由实现 |
| `backend/app/hardware_state_machine.py` | 硬件状态机模拟器 |
| `backend/.env.example` | 环境变量示例 |
| `backend/requirements.txt` | Python 依赖 |
| `backend/scripts/generate_openapi.py` | OpenAPI 导出脚本 |
| `backend/openapi.json` | 当前本地后端 OpenAPI |
| `HARDWARE_STATE_MACHINE_SIMULATOR.md` | 硬件状态机模拟器设计说明 |
| `TEAM_API_CONTRACT_8082_8083.md` | 8082/8083 全量 API 契约 |

## 3. 本地启动

安装依赖：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

启动：

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

```text
http://localhost:8000/docs
http://localhost:8000/openapi.json
http://localhost:8000/api/health
```

## 4. 环境变量

`backend/.env.example`：

```env
PORT=8000
NACOS_BASE_URL=http://127.0.0.1:8848/nacos
NACOS_USERNAME=
NACOS_PASSWORD=
CORS_ALLOWED_ORIGINS=http://localhost:9000,http://localhost:8083
PUBLISH_API_KEY=change-this-to-a-strong-key
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
```

变量说明：

| 变量 | 说明 |
|---|---|
| `PORT` | 后端端口 |
| `NACOS_BASE_URL` | Nacos 地址 |
| `NACOS_USERNAME` | Nacos 用户名，未开启鉴权可留空 |
| `NACOS_PASSWORD` | Nacos 密码，未开启鉴权可留空 |
| `CORS_ALLOWED_ORIGINS` | 允许跨域来源 |
| `PUBLISH_API_KEY` | 发布 Nacos 配置时使用的后端密钥 |
| `USE_STATE_MACHINE_SIMULATOR` | 是否启用硬件状态机模拟器 |
| `SIMULATOR_AUTO_TICK` | 是否自动推进模拟状态 |
| `SIMULATOR_TICK_SECONDS` | 自动推进间隔，单位秒 |

## 5. 响应结构规则

### 5.1 标准业务响应

除 `device-status` 兼容接口外，业务接口统一使用：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

### 5.2 8083 兼容裸 JSON

以下接口为了兼容现有 `8083` 前端，返回裸 JSON：

| 方法 | 路径 | 返回 |
|---|---|---|
| `GET` | `/api/device-status/options` | `{ regions, devices }` |
| `GET` | `/api/device-status/summary` | `{ summary, records }` |
| `GET` | `/api/device-status/records` | `{ records, updatedAt }` |

## 6. 当前已落地接口总表

| 方法 | 路径 | 模块 | 说明 |
|---|---|---|---|
| `GET` | `/api/health` | system | 服务探活 |
| `GET` | `/api/dashboard/overview` | dashboard | 8083 大屏概览 |
| `GET` | `/api/device-status/options` | device-status | 设备状态筛选项 |
| `GET` | `/api/device-status/summary` | device-status | 设备状态汇总 |
| `GET` | `/api/device-status/records` | device-status | 设备状态明细 |
| `GET` | `/api/nacos/config` | nacos-config | 读取 Nacos 配置 |
| `POST` | `/api/nacos/config` | nacos-config | 发布 Nacos 配置 |
| `GET` | `/api/simulator/summary` | hardware-simulator | 模拟器汇总 |
| `GET` | `/api/simulator/devices` | hardware-simulator | 模拟硬件列表 |
| `GET` | `/api/simulator/devices/{device_id}` | hardware-simulator | 模拟硬件详情 |
| `POST` | `/api/simulator/tick` | hardware-simulator | 手动推进模拟状态 |
| `POST` | `/api/simulator/devices/{device_id}/command` | hardware-simulator | 对模拟硬件下发命令 |

## 7. System API

### 7.1 健康检查

`GET /api/health`

返回：

```json
{
  "status": "ok"
}
```

curl：

```bash
curl "http://localhost:8000/api/health"
```

## 8. Dashboard API

### 8.1 大屏概览

`GET /api/dashboard/overview`

用途：

- 给 `8083` 前端提供大屏核心指标。
- 当前开启状态机模拟器后，设备统计来自模拟器聚合。

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "获取大屏概览数据成功",
  "data": {
    "onlineAccess": 27,
    "areaTotal": 139,
    "vehiclesOnSite": 22,
    "railStatus": "idle",
    "deviceRecords": [
      {
        "region": "A区",
        "device": "人员智能门/联锁门",
        "online": 8,
        "offline": 0
      }
    ],
    "deviceRegions": ["全部", "A区", "F区"],
    "deviceTypes": ["全部", "人员智能门/联锁门", "摄像机"],
    "updatedAt": "2026-05-07T10:19:48+08:00"
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `onlineAccess` | `number` | 在线门禁数量 |
| `areaTotal` | `number` | 区域总人数或大屏统计值 |
| `vehiclesOnSite` | `number` | 场内车辆数 |
| `railStatus` | `string` | 火车道状态 |
| `deviceRecords` | `array` | 设备在线离线聚合 |
| `deviceRegions` | `array` | 区域筛选项 |
| `deviceTypes` | `array` | 设备筛选项 |
| `updatedAt` | `string` | 更新时间 |

curl：

```bash
curl "http://localhost:8000/api/dashboard/overview"
```

## 9. Device Status API

### 9.1 获取筛选项

`GET /api/device-status/options`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `region` | `string` | `全部` | 中文区域名兼容 |
| `regionId` | `string` | 无 | 区域 ID 兼容 |

返回：

```json
{
  "regions": ["全部", "A区", "F区", "L区", "作业区", "厂房", "成品库", "火车道", "道路"],
  "devices": ["全部", "人员智能门/联锁门", "摄像机", "温感器", "烟感器"]
}
```

curl：

```bash
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/options?region=A区"
```

### 9.2 获取汇总

`GET /api/device-status/summary`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `region` | `string` | `全部` | 中文区域名 |
| `regionId` | `string` | 无 | 区域 ID |
| `device` | `string` | `全部` | 中文设备名 |
| `deviceType` | `string` | 无 | 设备类型 ID |

返回：

```json
{
  "summary": {
    "totalDevices": 143,
    "onlineDevices": 143,
    "offlineDevices": 0,
    "onlineRate": 100.0
  },
  "records": [
    {
      "region": "A区",
      "device": "摄像机",
      "online": 8,
      "offline": 0
    }
  ]
}
```

curl：

```bash
curl "http://localhost:8000/api/device-status/summary"
curl "http://localhost:8000/api/device-status/summary?region=A区&device=摄像机"
```

### 9.3 获取明细

`GET /api/device-status/records`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `region` | `string` | `全部` | 中文区域名 |
| `regionId` | `string` | 无 | 区域 ID |
| `device` | `string` | `全部` | 中文设备名 |
| `deviceType` | `string` | 无 | 设备类型 ID |
| `dataId` | `string` | 空 | Nacos 配置 ID |
| `group` | `string` | `DEFAULT_GROUP` | Nacos 分组 |
| `tenant` | `string` | 空 | Nacos namespace |
| `field` | `string` | `deviceStatus.records` | 配置字段路径 |

返回：

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
  "updatedAt": "2026-05-07T10:19:48+08:00"
}
```

说明：

- `USE_STATE_MACHINE_SIMULATOR=true` 时，默认从状态机聚合数据。
- 传入 `dataId` 时，可以从 Nacos 配置读取。
- 返回结构保持 8083 前端兼容。

curl：

```bash
curl "http://localhost:8000/api/device-status/records"
curl "http://localhost:8000/api/device-status/records?region=A区&device=摄像机"
```

## 10. Nacos Config API

### 10.1 读取配置

`GET /api/nacos/config`

Query：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `dataId` | `string` | 空 | 配置 ID；为空时读取列表 |
| `group` | `string` | `DEFAULT_GROUP` | 分组 |
| `tenant` | `string` | 空 | namespace |
| `field` | `string` | 空 | JSON/YAML 点路径 |
| `pageNo` | `number` | `1` | 列表页码 |
| `pageSize` | `number` | `200` | 列表每页数量 |

读取单配置返回：

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
  "value": []
}
```

读取列表返回：

```json
{
  "mode": "all",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "field": null,
  "total": 1,
  "items": [
    {
      "dataId": "device-status.json",
      "group": "DEFAULT_GROUP",
      "tenant": null,
      "content": "{}",
      "parsed": {},
      "value": null
    }
  ],
  "mergedParams": {}
}
```

curl：

```bash
curl "http://localhost:8000/api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP"
curl "http://localhost:8000/api/nacos/config?dataId=device-status.json&field=deviceStatus.records"
```

### 10.2 发布配置

`POST /api/nacos/config`

Header：

| 名称 | 必填 | 说明 |
|---|---:|---|
| `X-Publish-Key` | 是 | 必须等于环境变量 `PUBLISH_API_KEY` |

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

返回：

```json
{
  "success": true,
  "message": "Config published to Nacos"
}
```

curl：

```bash
curl -X POST "http://localhost:8000/api/nacos/config" \
  -H "Content-Type: application/json" \
  -H "X-Publish-Key: change-this-to-a-strong-key" \
  -d "{\"dataId\":\"device-status.json\",\"group\":\"DEFAULT_GROUP\",\"type\":\"json\",\"content\":\"{}\"}"
```

错误：

| 状态码 | 场景 |
|---:|---|
| `401` | `X-Publish-Key` 错误 |
| `503` | 服务端未配置 `PUBLISH_API_KEY` |
| `502` | Nacos 发布失败 |

## 11. Hardware Simulator API

硬件模拟器用于在真实硬件未接入前模拟设备状态。当前模拟的硬件包括：

| 类型 | 中文名 |
|---|---|
| `door` | 人员智能门/联锁门 |
| `vehicle` | 车辆识别与道闸 |
| `rail` | 火车道联动门 |
| `camera` | 摄像机 |
| `acoustic` | 声光报警 |
| `photoelectric` | 光电报警 |
| `smoke` | 烟感器 |
| `temperature` | 温感器 |
| `nvr` | NVR |
| `ai` | AI分析服务器 |

### 11.1 模拟器汇总

`GET /api/simulator/summary`

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "tick": 0,
    "totalDevices": 143,
    "onlineDevices": 143,
    "offlineDevices": 0,
    "faultDevices": 0,
    "alarmDevices": 0,
    "onlineRate": 100.0,
    "updatedAt": "2026-05-07T10:19:48+08:00"
  }
}
```

curl：

```bash
curl "http://localhost:8000/api/simulator/summary"
```

### 11.2 模拟硬件列表

`GET /api/simulator/devices`

Query：

| 参数 | 类型 | 说明 |
|---|---|---|
| `areaId` | `string` | 区域 ID，如 `r01` |
| `deviceType` | `string` | 设备类型，如 `smoke` |
| `onlineStatus` | `string` | 在线状态，如 `online` |

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "items": [
      {
        "id": "door_r01_001",
        "name": "A区人员智能门/联锁门1",
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
        "sequence": 0,
        "lastHeartbeatAt": "2026-05-07T10:19:48+08:00",
        "lastChangedAt": "2026-05-07T10:19:48+08:00",
        "metadata": {}
      }
    ],
    "total": 1,
    "tick": 0,
    "updatedAt": "2026-05-07T10:19:48+08:00"
  }
}
```

curl：

```bash
curl "http://localhost:8000/api/simulator/devices"
curl "http://localhost:8000/api/simulator/devices?areaId=r01&deviceType=smoke"
```

### 11.3 单个模拟硬件详情

`GET /api/simulator/devices/{device_id}`

curl：

```bash
curl "http://localhost:8000/api/simulator/devices/door_r01_001"
```

找不到返回 `404`。

### 11.4 手动推进模拟状态

`POST /api/simulator/tick`

Query：

| 参数 | 类型 | 默认 | 限制 | 说明 |
|---|---|---|---|---|
| `steps` | `number` | `1` | `1-100` | 推进步数 |

curl：

```bash
curl -X POST "http://localhost:8000/api/simulator/tick?steps=10"
```

### 11.5 模拟硬件命令

`POST /api/simulator/devices/{device_id}/command`

Body：

```json
{
  "command": "fault",
  "reason": "联调测试",
  "operator": "tester",
  "payload": {}
}
```

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

curl：

```bash
curl -X POST "http://localhost:8000/api/simulator/devices/door_r01_001/command" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"fault\",\"reason\":\"联调测试\",\"operator\":\"tester\",\"payload\":{}}"
```

## 12. 状态枚举

### 12.1 在线状态

| 值 | 说明 |
|---|---|
| `online` | 在线 |
| `offline` | 离线 |
| `fault` | 故障 |
| `maintenance` | 维护 |

### 12.2 工作状态

| 值 | 说明 |
|---|---|
| `normal` | 正常 |
| `open` | 开启 |
| `closed` | 关闭 |
| `locked` | 锁定 |
| `alarm` | 告警态 |
| `warning` | 预警态 |
| `fault` | 故障态 |
| `offline` | 离线态 |
| `maintenance` | 维护态 |

### 12.3 告警状态

| 值 | 说明 |
|---|---|
| `normal` | 无告警 |
| `warning` | 预警 |
| `alarm` | 告警 |

## 13. 当前后端和 8082 全量契约的关系

当前本地后端已经落地的是第一阶段闭环。`8082/docs` 里的接口更多，属于全量业务契约和后续实现范围。

| 模块 | 当前本地后端 | 全量契约 |
|---|---|---|
| system | 已落地 `/api/health` | 已覆盖 |
| dashboard | 已落地 `/api/dashboard/overview` | 已覆盖 |
| device-status | 已落地 options/summary/records | 已覆盖 |
| nacos-config | 已落地 read/publish | 已覆盖 |
| hardware-simulator | 已落地 `/api/simulator/*` | 新增已同步 |
| areas | 待实现 | `GET /api/areas`、`GET /api/areas/{areaId}/summary` |
| devices | 待实现 | `GET /api/devices/list`、`GET /api/devices/{deviceId}` |
| access | 待实现 | 门禁列表、详情、控制、通行记录 |
| vehicle | 待实现 | 车道列表、道闸控制、车辆通行记录 |
| railway | 待实现 | 火车道状态、模式、联动记录 |
| alarms | 待实现 | 告警列表、详情、动作 |
| events | 待实现 | 事件列表、详情、关闭 |
| video | 待实现 | 摄像机、流地址、录像、证据 |
| ai | 待实现 | AI 规则、检测记录 |
| reports | 待实现 | 告警、通行、车辆、设备报表 |
| audit | 待实现 | 审计日志 |
| inspection | 待实现 | 巡检任务和测量数据 |

后续实现时，以 `TEAM_API_CONTRACT_8082_8083.md` 的路径、参数、返回结构为准。

## 14. 后端实现规范

### 14.1 基础规则

| 项 | 规则 |
|---|---|
| 框架 | FastAPI |
| 模型 | Pydantic |
| 路由 | 后续按模块拆到 `routers/` |
| Schema | 后续按模块拆到 `schemas/` |
| Service | 业务逻辑放 `services/` |
| 对外 JSON | `camelCase` |
| Python 内部变量 | `snake_case` |
| 时间 | ISO 8601 |
| 错误 | 使用 HTTP 状态码和统一错误结构 |

### 14.2 新接口要求

新接口必须满足：

1. 写 `response_model`。
2. 请求体定义 Pydantic 模型。
3. Query 参数写默认值和校验范围。
4. 返回结构对齐文档。
5. Swagger 能看到。
6. 更新 `backend/openapi.json`。
7. 更新 Markdown 文档。
8. 提供 curl 自测结果。

### 14.3 数据来源规则

| 数据 | 当前阶段 | 后续真实来源 |
|---|---|---|
| 设备状态 | Python 状态机模拟器 | 硬件适配器 / 状态表 / Redis |
| 设备筛选项 | 状态机聚合 | 设备台账 |
| Nacos 配置 | Nacos | Nacos |
| 业务流水 | mock 或待实现 | 业务数据库 |
| 视频证据 | 待实现 | 视频平台 / 对象存储 |

Nacos 不存业务流水，只存配置、字典、阈值、策略。

## 15. 自测清单

后端同学本地启动后先跑这些：

```bash
curl "http://localhost:8000/api/health"
curl "http://localhost:8000/api/dashboard/overview"
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/summary"
curl "http://localhost:8000/api/device-status/records"
curl "http://localhost:8000/api/simulator/summary"
curl "http://localhost:8000/api/simulator/devices"
curl -X POST "http://localhost:8000/api/simulator/tick?steps=5"
```

强制某个设备故障：

```bash
curl -X POST "http://localhost:8000/api/simulator/devices/door_r01_001/command" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"fault\",\"reason\":\"联调测试\",\"operator\":\"tester\",\"payload\":{}}"
```

恢复：

```bash
curl -X POST "http://localhost:8000/api/simulator/devices/door_r01_001/command" \
  -H "Content-Type: application/json" \
  -d "{\"command\":\"recover\",\"reason\":\"恢复测试\",\"operator\":\"tester\",\"payload\":{}}"
```

导出 OpenAPI：

```powershell
cd backend
python .\scripts\generate_openapi.py
```

## 16. 线上文档入口

| 内容 | 地址 |
|---|---|
| 文档站首页 | `https://wpengu.top/` |
| 本文档 | `https://wpengu.top/docs/backend-current-api/` |
| 硬件状态机模拟器 | `https://wpengu.top/docs/hardware-state-machine-simulator/` |
| API 契约 | `https://wpengu.top/docs/team-api-contract/` |
| Scalar OpenAPI | `https://wpengu.top/openapi/` |
| OpenAPI JSON | `https://wpengu.top/openapi.json` |
