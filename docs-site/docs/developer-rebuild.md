---
id: developer-rebuild
title: 从零到一开发文档
slug: /developer-rebuild
---

# 从零到一开发文档

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-REBUILD-1.1` |
| 文档集 | `DOC-2026.05.07` |
| 适用系统版本 | `LEGACY-FE-8083` + `API-TARGET-1.0` |
| 当前状态 | 正式开发环境重建依据 |
| 更新日期 | `2026-05-07` |

整理日期：`2026-05-06`

本文档用于开发人员重新搭建正式开发环境。当前 `8083` 前端保留，后端、代理、接口契约、配置中心接入、数据接入和交付流程按本文档从零到一重建。

## 1. 当前结论

| 项目项 | 处理方式 |
|---|---|
| `http://101.43.49.78:8083` 前端 | 保留，作为现有大屏展示入口和前端适配目标 |
| `http://101.43.49.78:8082/docs` | 保留，作为当前接口参考和对照 Swagger |
| 新 FastAPI 后端 | 从零搭建，接口结构对齐 `8082/docs` 和 `8083` 前端调用 |
| Nacos | 作为配置中心使用，不作为业务数据库 |
| 本仓库旧静态演示页 | 可作为本地调试页，不替代 `8083` 前端 |
| 打包 JS 文件 | 可用于分析字段和接口，不作为源码二次开发基础 |

一句话目标：

```text
前端保留 8083，后端重新按 FastAPI 标准搭建，并保证 8083 页面通过 /api/... 能稳定拿到数据。
```

## 2. 开发人员需要拿到的文件

开发人员至少需要这三份文件：

| 文件 | 用途 |
|---|---|
| `DEVELOPER_PROJECT_REBUILD_SUMMARY.md` | 从零到一搭建开发环境、实现顺序、代码规范、交付要求 |
| `TEAM_API_CONTRACT_8082_8083.md` | 对齐 `8082/docs` 和 `8083` 前端的 API 契约、返回 JSON、枚举、权限 |
| `COMPLETE_API_DOC.md` | 全量 API 设计、状态码、JSON 结构、代码规范补充 |

开发时以本文档为执行顺序，以 `TEAM_API_CONTRACT_8082_8083.md` 为接口实现口径。

## 3. 最终架构

```text
浏览器
  -> http://101.43.49.78:8083
    -> 8083 前端页面
      -> /api/...
        -> Nginx / 网关代理
          -> FastAPI 后端
            -> Nacos 配置中心
            -> 业务数据库
            -> 视频平台 / 门禁系统 / 车辆系统 / AI 系统
```

本地开发架构：

```text
浏览器
  -> http://localhost:9000 或 8083 线上页面
    -> /api/...
      -> 本地 Nginx / devServer proxy
        -> http://localhost:8000 FastAPI
          -> 本地 Nacos 或测试 Nacos
          -> mock 数据 / 测试数据库
```

## 4. 各模块职责

| 模块 | 技术 | 职责 |
|---|---|---|
| 8083 前端 | 现有前端 | 保留页面、交互、图表和现有入口 |
| 代理层 | Nginx 或 devServer proxy | 把 `/api/...` 转发到 FastAPI |
| API 层 | FastAPI | 路由、参数校验、响应模型、业务聚合 |
| 硬件模拟层 | Python 状态机 | 在真实硬件接入前模拟门禁、道闸、传感器、报警器状态 |
| 配置层 | Nacos | 页面配置、字典、阈值、策略、开发 mock 配置 |
| 数据层 | 数据库或外部系统 | 人员、车辆、设备、告警、事件、巡检、视频证据 |
| 文档层 | OpenAPI + Markdown | 保证接口、字段、状态码可查可验收 |

## 5. 项目目录标准

正式项目建议使用以下结构：

```text
project-root/
  backend/
    app/
      main.py
      config.py
      dependencies.py
      routers/
        health.py
        info.py
        dashboard.py
        device_status.py
        nacos_config.py
        areas.py
        devices.py
        access.py
        vehicle.py
        railway.py
        alarms.py
        events.py
        video.py
        ai.py
        reports.py
        audit.py
        inspection.py
      schemas/
        common.py
        dashboard.py
        device_status.py
        nacos_config.py
        areas.py
        devices.py
        access.py
        vehicle.py
        railway.py
        alarms.py
        events.py
        video.py
        ai.py
        reports.py
        audit.py
        inspection.py
      services/
        nacos_client.py
        mock_data.py
        hardware_state_machine.py
        dashboard_service.py
        device_status_service.py
        access_service.py
        vehicle_service.py
        railway_service.py
        alarm_service.py
      repositories/
        db.py
      utils/
        response.py
        time.py
    scripts/
      generate_openapi.py
    tests/
    .env.example
    requirements.txt
    Dockerfile
    openapi.json
  frontend-adapter/
    nginx.conf
    README.md
  docs/
    DEVELOPER_PROJECT_REBUILD_SUMMARY.md
    TEAM_API_CONTRACT_8082_8083.md
    COMPLETE_API_DOC.md
  docker-compose.yml
  README.md
```

说明：

- `8083` 前端保留时，不要求把线上前端源码迁入新项目。
- `frontend-adapter/` 只放代理配置和前端适配说明。
- 如果后续拿到 `8083` 前端源码，再单独建立 `frontend/` 并保持 `/api/...` 调用不变。

## 6. 端口规划

| 服务 | 端口 | 说明 |
|---|---:|---|
| 现有前端 | `8083` | 保留的线上大屏入口 |
| 现有参考 API | `8082` | 当前 Swagger 对照服务 |
| 新 FastAPI | `8000` | 本地和测试环境后端 API |
| 本地调试前端/代理 | `9000` | 本地 Nginx 或静态调试入口 |
| Nacos | `8848` | 配置中心 |
| 数据库 | 按实际 | PostgreSQL/MySQL/其他业务库 |

## 7. 从零搭建步骤

### 7.1 创建后端项目

```powershell
mkdir backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install fastapi uvicorn[standard] pydantic pydantic-settings httpx python-dotenv
pip freeze > requirements.txt
mkdir app
mkdir app\routers
mkdir app\schemas
mkdir app\services
mkdir app\utils
mkdir scripts
mkdir tests
```

`requirements.txt` 最小依赖：

```txt
fastapi
uvicorn[standard]
pydantic
pydantic-settings
httpx
python-dotenv
```

### 7.2 创建环境变量

`backend/.env.example`：

```env
PORT=8000
ENV_NAME=dev
USE_MOCK=true

NACOS_BASE_URL=http://127.0.0.1:8848/nacos
NACOS_USERNAME=
NACOS_PASSWORD=

CORS_ALLOWED_ORIGINS=http://localhost:9000,http://localhost:5173,http://localhost:8083,http://101.43.49.78:8083
PUBLISH_API_KEY=change-this-to-a-strong-key

DB_DSN=
VIDEO_PLATFORM_BASE_URL=
ACCESS_SYSTEM_BASE_URL=
VEHICLE_SYSTEM_BASE_URL=
AI_SYSTEM_BASE_URL=
```

规则：

- `.env.example` 提交仓库。
- `.env` 不提交仓库。
- 密码、密钥、数据库连接串只放环境变量。

### 7.3 创建 FastAPI 入口

`backend/app/main.py`：

```py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import health, info, dashboard, device_status, nacos_config

app = FastAPI(title="Factory Control API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(info.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(device_status.router, prefix="/api")
app.include_router(nacos_config.router, prefix="/api")
```

启动命令：

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

```text
http://localhost:8000/docs
http://localhost:8000/health
```

## 8. 第一阶段：先让 8083 能取数

第一阶段只做保留前端必须使用的接口。

| 优先级 | 方法 | 路径 | 说明 |
|---:|---|---|---|
| P0 | `GET` | `/health` | 服务探活 |
| P0 | `GET` | `/api/info` | API 信息 |
| P0 | `GET` | `/api/dashboard/overview` | 8083 大屏概览 |
| P0 | `GET` | `/api/device-status/options` | 设备筛选项 |
| P0 | `GET` | `/api/device-status/summary` | 设备在线率汇总 |
| P0 | `GET` | `/api/device-status/records` | 设备图表明细 |
| P0 | `GET` | `/api/simulator/summary` | 模拟器汇总 |
| P0 | `GET` | `/api/simulator/devices` | 模拟硬件列表 |
| P0 | `POST` | `/api/simulator/tick` | 手动推进模拟状态 |

### 8.1 `/api/dashboard/overview`

返回标准包装：

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

### 8.2 `/api/device-status/options`

为兼容 `8082/docs` 和 `8083`，返回裸 JSON：

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

后端参数必须兼容两套写法：

| 参数 | 用途 |
|---|---|
| `regionId` | 标准区域 ID，例如 `r01` |
| `region` | 中文区域名兼容，例如 `A区` |
| `deviceType` | 标准设备类型 ID，例如 `camera` |
| `device` | 中文设备名兼容，例如 `摄像机` |

### 8.3 `/api/device-status/summary`

返回裸 JSON：

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

### 8.4 `/api/device-status/records`

返回裸 JSON：

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

验收命令：

```powershell
curl "http://localhost:8000/api/dashboard/overview"
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/summary"
curl "http://localhost:8000/api/device-status/records"
```

## 9. 第二阶段：接入 Nacos 配置中心

Nacos 在本项目中只做配置中心。

适合放 Nacos：

| 类型 | 示例 |
|---|---|
| 页面刷新配置 | `refreshSeconds=30` |
| 字典配置 | 区域、设备类型、状态枚举 |
| 阈值配置 | 告警阈值、AI 置信度阈值 |
| 策略配置 | 火车道联动策略、门禁控制策略 |
| 开发 mock 配置 | `deviceStatus.records` |

不适合放 Nacos：

| 类型 | 原因 |
|---|---|
| 人员通行流水 | 业务数据，应进数据库 |
| 车辆通行流水 | 业务数据，应进数据库 |
| 告警处置记录 | 闭环数据，应进数据库 |
| 视频和图片 | 应进视频平台或对象存储 |
| 用户密码 | 敏感信息，不写配置中心 |

必须实现：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/nacos/config` | 读取配置 |
| `POST` | `/api/nacos/config` | 发布配置 |

发布配置要求 `X-Publish-Key`。

## 10. 第三阶段：补齐业务模块

按以下顺序实现，不要一开始就铺满所有接口。

### 10.1 区域和设备

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/areas` | 区域列表 |
| `GET` | `/api/areas/{areaId}/summary` | 区域汇总 |
| `GET` | `/api/devices/list` | 设备分页列表 |
| `GET` | `/api/devices/{deviceId}` | 设备详情 |

### 10.2 门禁

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/access/doors` | 门禁分页列表 |
| `GET` | `/api/access/doors/{doorId}` | 门禁详情 |
| `POST` | `/api/access/doors/{doorId}/command` | 门禁控制 |
| `GET` | `/api/access/pass-records` | 人员通行记录 |

### 10.3 车辆

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/vehicle/lanes` | 车道分页列表 |
| `POST` | `/api/vehicle/lanes/{laneId}/command` | 道闸控制 |
| `GET` | `/api/vehicle/pass-records` | 车辆通行记录 |

### 10.4 火车道

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/railway/status` | 火车道状态 |
| `POST` | `/api/railway/mode` | 火车道模式切换 |
| `GET` | `/api/railway/linkage-records` | 联动记录 |

### 10.5 告警和事件

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/alarms` | 告警分页列表 |
| `GET` | `/api/alarms/{alarmId}` | 告警详情 |
| `POST` | `/api/alarms/{alarmId}/actions` | 告警处理动作 |
| `GET` | `/api/events` | 事件分页列表 |
| `GET` | `/api/events/{eventId}` | 事件详情 |
| `PATCH` | `/api/events/{eventId}/close` | 关闭事件 |

### 10.6 视频、AI、报表、审计、巡检

这些模块按验收优先级后续补齐：

| 模块 | 接口范围 |
|---|---|
| 视频 | `/api/video/*` |
| AI | `/api/ai/*` |
| 报表 | `/api/reports/*` |
| 审计 | `/api/audit/logs` |
| 巡检 | `/api/v1/inspection/*`、`/api/tree-menu`、`/api/latest-measurements` |

## 11. API 统一规则

### 11.1 路径规则

| 场景 | 规则 | 示例 |
|---|---|---|
| 集合 | 复数名词 | `GET /api/areas` |
| 详情 | 路径参数 | `GET /api/devices/{deviceId}` |
| 控制 | `command` 子路径 | `POST /api/access/doors/{doorId}/command` |
| 动作 | `actions` 子路径 | `POST /api/alarms/{alarmId}/actions` |
| 关闭 | 明确动作路径 | `PATCH /api/events/{eventId}/close` |

### 11.2 命名规则

| 场景 | 规则 | 示例 |
|---|---|---|
| URL | 小写中划线 | `/api/device-status/records` |
| JSON 字段 | `camelCase` | `areaId`、`pageSize` |
| Python 变量 | `snake_case` | `area_id`、`page_size` |
| Pydantic 类 | `PascalCase` | `DeviceStatusRecord` |
| 时间字段 | `At` 结尾 | `createdAt`、`updatedAt` |

### 11.3 标准响应

除 `device-status` 三个兼容裸 JSON 接口外，业务接口统一返回：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {},
  "traceId": "optional-trace-id"
}
```

### 11.4 分页响应

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

## 12. 状态码规则

| 状态码 | 含义 | 使用场景 |
|---:|---|---|
| `200` | 成功 | 查询成功、命令处理成功 |
| `201` | 创建成功 | 新增任务 |
| `202` | 已接收 | 异步导出、异步控制 |
| `204` | 成功无内容 | 删除成功 |
| `400` | 业务参数错误 | 未知区域、非法命令 |
| `401` | 未认证 | 未登录、发布密钥错误 |
| `403` | 无权限 | 无控制权限 |
| `404` | 资源不存在 | 设备、告警、事件不存在 |
| `409` | 状态冲突 | 重复关闭、重复启动 |
| `422` | 字段校验失败 | 必填缺失、类型错误 |
| `429` | 请求过频 | 高频轮询、重复下发 |
| `500` | 服务端异常 | 未预期错误 |
| `502` | 下游异常 | Nacos、视频平台、业务系统异常 |
| `503` | 服务不可用 | 依赖未配置 |
| `504` | 下游超时 | 依赖请求超时 |

错误返回：

```json
{
  "code": 404,
  "success": false,
  "message": "设备不存在",
  "data": null,
  "traceId": "trace-202605060001"
}
```

## 13. 权限规则

最小权限码：

| 权限码 | 说明 |
|---|---|
| `dashboard:read` | 查看大屏 |
| `device:read` | 查看设备和设备状态 |
| `area:read` | 查看区域 |
| `access:read` | 查看门禁 |
| `access:command` | 控制门禁 |
| `vehicle:read` | 查看车辆 |
| `vehicle:command` | 控制道闸 |
| `railway:read` | 查看火车道 |
| `railway:command` | 切换火车道模式 |
| `alarm:read` | 查看告警 |
| `alarm:action` | 处理告警 |
| `event:read` | 查看事件 |
| `event:close` | 关闭事件 |
| `video:read` | 查看视频 |
| `video:export` | 导出视频证据 |
| `report:read` | 查看报表 |
| `report:export` | 导出报表 |
| `audit:read` | 查看审计 |
| `nacos:read` | 读取 Nacos 配置 |
| `nacos:write` | 发布 Nacos 配置 |

控制类接口必须记录：

| 字段 | 说明 |
|---|---|
| `operator` | 操作人 |
| `reason` | 操作原因 |
| `targetId` | 操作目标 |
| `command/action` | 动作 |
| `createdAt` | 操作时间 |
| `result` | 执行结果 |

## 14. mock 和真实数据切换

允许先 mock，但必须按正式字段 mock。

| 阶段 | 数据来源 |
|---|---|
| 本地开发早期 | `services/mock_data.py` |
| 前端联调 | mock 或 Nacos 配置 |
| 测试环境 | 测试数据库 / 测试业务系统 |
| 正式环境 | 正式数据库 / 正式业务系统 |

规则：

- `USE_MOCK=true` 时允许返回 mock。
- `USE_MOCK=false` 时必须走真实数据源或明确返回 `503`。
- mock 字段必须和正式接口一致。
- 前端不能自己维护另一套 mock 字段。

### 14.1 硬件状态机模拟器

所有硬件统一抽象成状态机。真实硬件未接入前，后端从状态机读取设备状态；真实硬件接入后，只替换状态来源，不改前端接口。

当前已落地：

| 文件 | 说明 |
|---|---|
| `backend/app/hardware_state_machine.py` | Python 状态机模拟器 |
| `HARDWARE_STATE_MACHINE_SIMULATOR.md` | 模拟器设计和使用文档 |

环境变量：

```env
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
```

模拟器接口：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/simulator/summary` | 查看模拟器汇总 |
| `GET` | `/api/simulator/devices` | 查看模拟硬件列表 |
| `GET` | `/api/simulator/devices/{deviceId}` | 查看单个模拟硬件 |
| `POST` | `/api/simulator/tick` | 手动推进状态 |
| `POST` | `/api/simulator/devices/{deviceId}/command` | 强制某个设备故障、恢复、告警、开关 |

状态机数据会聚合到：

| 接口 | 说明 |
|---|---|
| `/api/dashboard/overview` | 大屏概览 |
| `/api/device-status/options` | 设备筛选项 |
| `/api/device-status/summary` | 设备汇总 |
| `/api/device-status/records` | 设备图表明细 |

## 15. 8083 代理适配

`8083` 前端保留时，关键是 `/api/...` 代理到新 FastAPI。

线上 Nginx 目标配置：

```nginx
location /api/ {
  proxy_pass http://127.0.0.1:8000/api/;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}

location /health {
  proxy_pass http://127.0.0.1:8000/health;
}
```

本地调试 Nginx：

```nginx
server {
  listen 9000;

  location / {
    proxy_pass http://101.43.49.78:8083/;
  }

  location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
  }
}
```

如果使用 Vite 调试：

```ts
export default {
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true
      }
    }
  }
}
```

## 16. Docker Compose

最小 `docker-compose.yml`：

```yaml
services:
  api:
    build: ./backend
    container_name: factory-api
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    restart: unless-stopped

  web-adapter:
    image: nginx:1.29-alpine
    container_name: factory-web-adapter
    ports:
      - "9000:80"
    volumes:
      - ./frontend-adapter/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - api
    restart: unless-stopped
```

后端 `Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

启动：

```powershell
docker compose up -d --build
```

## 17. OpenAPI 和文档同步

每次新增或修改接口必须同步：

1. 后端代码。
2. `response_model`。
3. Swagger/OpenAPI。
4. `TEAM_API_CONTRACT_8082_8083.md`。
5. `COMPLETE_API_DOC.md`。
6. curl 自测结果。

导出 OpenAPI：

```py
import json
from pathlib import Path

from app.main import app

output = Path(__file__).resolve().parents[1] / "openapi.json"
output.write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(f"OpenAPI written to {output}")
```

运行：

```powershell
cd backend
python .\scripts\generate_openapi.py
```

## 18. 代码规范

### 18.1 后端

| 项 | 规范 |
|---|---|
| 框架 | FastAPI |
| 模型 | Pydantic |
| HTTP 客户端 | httpx |
| 配置 | pydantic-settings 或 python-dotenv |
| 路由 | 按业务模块拆到 `routers/` |
| Schema | 按业务模块拆到 `schemas/` |
| Service | 业务逻辑放 `services/` |
| 错误 | 使用统一错误响应 |
| 时间 | ISO 8601 |

要求：

- 新接口必须写 `response_model`。
- 请求体必须定义 Pydantic 模型。
- Query 参数必须写默认值和校验范围。
- 对外 JSON 使用 `camelCase`。
- 内部 Python 使用 `snake_case`。
- 密钥只从环境变量读取。
- 控制类接口必须记录操作日志。

### 18.2 前端适配

前端调用统一使用相对路径：

```ts
fetch("/api/device-status/records")
```

统一解析：

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

`device-status/options` 兼容 `{ id, name }`：

```ts
const regions = options.regions.map((item: any) =>
  typeof item === "string" ? item : item.name
);

const devices = options.devices.map((item: any) =>
  typeof item === "string" ? item : item.name
);
```

## 19. 验收顺序

### 19.1 后端基础验收

```powershell
curl "http://localhost:8000/health"
curl "http://localhost:8000/api/info"
curl "http://localhost:8000/api/dashboard/overview"
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/summary"
curl "http://localhost:8000/api/device-status/records"
```

通过标准：

| 检查项 | 标准 |
|---|---|
| Swagger | `http://localhost:8000/docs` 可访问 |
| 健康检查 | 返回成功 |
| 大屏概览 | 返回 `onlineAccess/areaTotal/vehiclesOnSite/railStatus` |
| 设备筛选 | 返回 `regions/devices` |
| 设备记录 | 返回 `records/updatedAt` |
| 错误处理 | 非法参数返回对应状态码 |

### 19.2 8083 联调验收

```powershell
curl "http://101.43.49.78:8083/api/dashboard/overview"
curl "http://101.43.49.78:8083/api/device-status/options"
curl "http://101.43.49.78:8083/api/device-status/summary"
curl "http://101.43.49.78:8083/api/device-status/records"
```

通过标准：

| 检查项 | 标准 |
|---|---|
| 8083 页面 | 页面能打开 |
| `/api` 代理 | 8083 下 `/api/...` 能访问新后端 |
| 大屏指标 | 核心指标显示正常 |
| 设备图表 | 在线、离线、在线率正常 |
| 筛选 | 区域和设备切换正常 |
| 异常 | 后端失败时前端不白屏 |

## 20. 交付物

开发人员交付：

| 交付物 | 标准 |
|---|---|
| 后端代码 | FastAPI 可启动 |
| `.env.example` | 环境变量完整 |
| `requirements.txt` | 依赖完整 |
| `Dockerfile` | 可构建 |
| `docker-compose.yml` | 可一键启动 |
| Nginx 配置 | 能把 `/api` 转到 FastAPI |
| Swagger | `/docs` 可访问 |
| OpenAPI | 已导出 |
| curl 自测结果 | 覆盖第一阶段接口 |
| 文档同步 | `TEAM_API_CONTRACT_8082_8083.md` 和 `COMPLETE_API_DOC.md` 已更新 |

## 21. 开发任务单

```text
任务：保留 8083 前端，从零搭建正式 FastAPI 后端和开发环境。

输入文件：
1. DEVELOPER_PROJECT_REBUILD_SUMMARY.md
2. TEAM_API_CONTRACT_8082_8083.md
3. COMPLETE_API_DOC.md

必须保留：
1. http://101.43.49.78:8083 作为现有前端入口。
2. 前端通过 /api/... 调后端的方式。
3. 8082/docs 作为当前接口参考。

第一阶段：
1. 创建 FastAPI 项目。
2. 配置 .env.example。
3. 实现 /health。
4. 实现 /api/info。
5. 实现 /api/dashboard/overview。
6. 实现 /api/device-status/options。
7. 实现 /api/device-status/summary。
8. 实现 /api/device-status/records。
9. 配置 Nginx 或代理，让 8083 的 /api 指向新后端。
10. 提供 curl 自测结果。

第二阶段：
1. 实现 /api/nacos/config 读取。
2. 实现 /api/nacos/config 发布。
3. 接入 Nacos 配置。
4. 保证 Nacos 不存业务流水。

第三阶段：
1. 补区域、设备、门禁、车辆、火车道、告警、事件模块。
2. 每个接口必须有 response_model。
3. 每个接口必须能在 Swagger 看到。
4. 每次改接口必须同步 OpenAPI 和 Markdown 文档。

禁止：
1. 不允许把同学 demo 地址写入正式代码。
2. 不允许前端另起一套 mock 字段。
3. 不允许接口返回结构和文档不一致。
4. 不允许把业务流水写进 Nacos。
```
