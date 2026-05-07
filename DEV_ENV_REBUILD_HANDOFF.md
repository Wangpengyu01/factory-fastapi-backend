# 开发环境重建交接说明

整理日期：`2026-05-06`

本文档用于交接给开发同学：当前工作不是教学演示，也不是继续维护以前同学做的 demo，而是重新搭建一套可以持续开发、联调、验收的开发环境。

## 1. 交接口径

可以直接把下面这段发给开发同学：

```text
之前对接的都是同学 demo，只能作为参考，不再作为后续开发基础。

这次任务是重新搭建正式开发环境：
1. 不继续依赖旧 demo 页面、旧 demo 接口、旧 mock 服务。
2. 新建一套干净的开发项目结构。
3. 后端使用 FastAPI，前端通过 /api/... 对接后端。
4. Nacos 只作为配置中心，不作为业务数据库。
5. 所有接口以 COMPLETE_API_DOC.md 为接口契约。
6. 先搭通开发环境，再逐步实现接口，不要一次性把所有协议接口硬塞进去。
```

## 2. 这次要解决的问题

以前的问题：

| 问题 | 影响 |
|---|---|
| 对接同学 demo | 接口字段、路径、返回结构不稳定 |
| mock 和真实接口混在一起 | 前端不知道哪些能长期依赖 |
| 没有统一开发环境 | 每个人本地启动方式不同 |
| 没有统一 API 契约 | 接口实现和文档容易不一致 |
| Nacos 角色不清楚 | 容易把配置中心当数据库使用 |

这次目标：

| 目标 | 标准 |
|---|---|
| 开发环境可复现 | 新同学拉代码后能按文档启动 |
| 前后端链路固定 | 浏览器通过 `/api/...` 请求后端 |
| 接口契约统一 | 以 `COMPLETE_API_DOC.md` 为准 |
| mock 有边界 | mock 只用于开发占位，不冒充真实业务 |
| Nacos 定位清楚 | 只存配置、字典、策略、演示数据 |

## 3. 要给开发同学的文件

必须给：

| 文件 | 用途 |
|---|---|
| `DEV_ENV_REBUILD_HANDOFF.md` | 本交接说明，告诉他这次不是继续 demo |
| `COMPLETE_API_DOC.md` | API 契约、状态码、JSON、代码规范 |

可选给：

| 文件 | 用途 |
|---|---|
| `backend/openapi.json` | 当前本仓库已有接口 OpenAPI，仅作参考 |
| `docker-compose.yml` | 当前容器编排参考 |
| `backend/.env.example` | 环境变量参考 |
| `frontend/nginx.conf` | `/api` 代理参考 |

不建议作为开发基础：

| 文件/内容 | 原因 |
|---|---|
| `_8083_bundle.js`、`_8083_cockpit.js` | 打包产物，不适合二次开发 |
| 同学 demo 接口 | 字段和稳定性不可控 |
| 旧 mock 页面 | 可以看效果，但不要继续堆业务 |

## 4. 新开发环境目标架构

```text
开发人员浏览器
  -> 前端开发服务或 Nginx
    -> /api/... 统一代理
      -> FastAPI 开发后端
        -> Nacos 配置中心
        -> 后续业务数据库/业务服务
```

开发阶段至少要有三层：

| 层 | 推荐技术 | 职责 |
|---|---|---|
| 前端 | Vue/React/静态页均可 | 页面、交互、请求 `/api/...` |
| API 后端 | FastAPI | 接口、模型、鉴权占位、业务聚合 |
| 配置中心 | Nacos | 配置、字典、策略、mock 配置数据 |

如果暂时没有真实数据库，可以先用后端内置 mock，但必须标注为 `mock`，后续替换为数据库或业务服务。

## 5. 新项目目录要求

让开发同学新建干净目录，不要在旧 demo 上继续改。

推荐结构：

```text
new-project/
  backend/
    app/
      main.py
      routers/
      schemas/
      services/
      config.py
    scripts/
      generate_openapi.py
    .env.example
    Dockerfile
    requirements.txt
  frontend/
    src/
    nginx.conf
    Dockerfile
  docs/
    COMPLETE_API_DOC.md
  docker-compose.yml
  README.md
```

如果项目暂时简单，也可以先用单文件 `backend/app/main.py`，但后续要拆成：

| 目录 | 职责 |
|---|---|
| `routers/` | 路由层，只处理 HTTP 参数和响应 |
| `schemas/` | Pydantic 请求/响应模型 |
| `services/` | 业务逻辑、Nacos 调用、数据组装 |
| `config.py` | 环境变量读取 |

## 6. 开发环境端口约定

| 服务 | 端口 | 说明 |
|---|---:|---|
| FastAPI 后端 | `8000` | 本地开发 API |
| 前端页面 | `9000` 或前端框架默认端口 | 页面访问入口 |
| Nacos | `8848` | 配置中心 |
| 线上业务 API | `8082` | 只用于对照，不作为本地开发依赖 |
| 线上旧大屏 | `8083` | 只用于看效果，不作为开发基础 |

要求：

- 前端统一请求 `/api/...`。
- 本地 Nginx 或前端 devServer 把 `/api` 代理到 FastAPI。
- 不要让前端直接请求 Nacos。
- 不要让新开发环境依赖同学 demo 的临时地址。

## 7. 环境变量要求

后端 `.env.example` 至少包含：

```env
PORT=8000
NACOS_BASE_URL=http://127.0.0.1:8848/nacos
NACOS_USERNAME=
NACOS_PASSWORD=
CORS_ALLOWED_ORIGINS=http://localhost:9000,http://localhost:5173,http://localhost:8083
PUBLISH_API_KEY=change-this-to-a-strong-key
ENV_NAME=dev
USE_MOCK=true
```

说明：

| 变量 | 说明 |
|---|---|
| `NACOS_BASE_URL` | Nacos 地址 |
| `PUBLISH_API_KEY` | 配置发布密钥 |
| `ENV_NAME` | 当前环境，建议 `dev/test/prod` |
| `USE_MOCK` | 是否启用 mock 数据 |

真实 `.env` 不提交。

## 8. API 实现顺序

不要一上来实现所有接口。按下面阶段做。

### 阶段 1：开发环境打通

必须完成：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/health` | 后端探活 |
| `GET` | `/api/device-status/options` | 前端筛选项联调 |
| `GET` | `/api/device-status/records` | 前端设备状态联调 |

验收：

```powershell
curl http://localhost:8000/api/health
curl http://localhost:9000/api/health
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/records?region=全部&device=全部"
```

### 阶段 2：接 Nacos 配置

必须完成：

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/nacos/config` | 读取配置 |
| `POST` | `/api/nacos/config` | 发布配置，受密钥保护 |

要求：

- 读取失败返回 `502`。
- 发布密钥错误返回 `401`。
- 未配置发布密钥返回 `503`。
- 前端不能直接访问 Nacos。

### 阶段 3：按业务最小验收接口补齐

优先实现 `COMPLETE_API_DOC.md` 第 `11` 节最小可验收接口：

| 优先级 | 模块 | 代表接口 |
|---|---|---|
| P0 | 大屏总览 | `/api/dashboard/overview` |
| P0 | 区域 | `/api/areas`、`/api/areas/{areaId}/summary` |
| P0 | 设备 | `/api/devices/list`、`/api/device-status/summary` |
| P0 | 门禁 | `/api/access/doors`、`/api/access/pass-records` |
| P0 | 车辆 | `/api/vehicle/lanes`、`/api/vehicle/pass-records` |
| P0 | 火车道 | `/api/railway/status`、`/api/railway/linkage-records` |
| P0 | 告警事件 | `/api/alarms`、`/api/events` |

AI、视频、报表、审计等后置，不要第一阶段就做。

## 9. mock 使用规则

允许使用 mock，但必须有边界。

| 规则 | 要求 |
|---|---|
| mock 开关 | 使用 `USE_MOCK=true/false` 控制 |
| mock 位置 | 放在后端 `services` 或 `mock_data`，不要写进前端 |
| mock 字段 | 必须和正式 API 字段一致 |
| mock 标识 | 文档和代码注释中标明 |
| 替换目标 | 每个 mock 接口要说明未来数据来源 |

禁止：

- 前端自己编一套和后端不同的字段。
- mock 接口返回结构和正式接口不一致。
- 把同学 demo 当成长期 mock 服务。

## 10. 前后端对接规则

前端只认 API 文档，不认口头字段。

请求规则：

```ts
fetch("/api/device-status/records?region=全部&device=全部")
```

不要这样写：

```ts
fetch("http://某同学电脑IP:xxxx/demo-api")
```

前端必须兼容两种返回：

包装 JSON：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {}
}
```

裸 JSON：

```json
{
  "records": [],
  "updatedAt": "2026-05-06T10:00:00+08:00"
}
```

统一解析：

```ts
function unwrapApiResponse(response: any) {
  if (response && typeof response === "object" && "success" in response && "data" in response) {
    if (!response.success) throw new Error(response.message || "请求失败");
    return response.data;
  }
  return response;
}
```

## 11. 后端开发规则

后端必须遵守：

| 规则 | 要求 |
|---|---|
| 框架 | FastAPI |
| 模型 | Pydantic |
| Python 命名 | `snake_case` |
| JSON 字段 | `camelCase` |
| 路径风格 | 小写中划线 |
| 错误 | 使用 `HTTPException` |
| OpenAPI | 新增接口后必须导出 |
| 文档 | 新增接口后必须同步 |

示例：

```py
class DeviceStatusRecordsResponse(BaseModel):
    records: list[DeviceStatusRecord]
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}
```

## 12. 交付物要求

开发同学完成开发环境后，必须交付：

| 交付物 | 标准 |
|---|---|
| 项目目录 | 新目录，不依赖旧 demo |
| 启动命令 | 写在 `README.md` |
| `.env.example` | 包含必要环境变量 |
| Swagger | `http://localhost:8000/docs` 能打开 |
| 前端页面 | 能通过 `/api` 请求后端 |
| Docker Compose | 一条命令能启动前后端 |
| curl 自测结果 | 至少包含 health、options、records |
| OpenAPI | 已导出 |
| API 文档同步 | 对照 `COMPLETE_API_DOC.md` |

## 13. 验收标准

开发环境通过标准：

```powershell
docker compose up -d --build
curl http://localhost:8000/api/health
curl http://localhost:9000/api/health
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/records?region=全部&device=全部"
```

必须满足：

| 检查项 | 通过标准 |
|---|---|
| 后端 | `localhost:8000/docs` 可访问 |
| 前端 | `localhost:9000` 可访问 |
| 代理 | `localhost:9000/api/health` 可访问 |
| 接口 | 返回 JSON 结构符合文档 |
| 配置 | `.env` 不提交，`.env.example` 完整 |
| Nacos | 明确只作为配置中心 |
| demo | 不依赖旧 demo 地址 |

## 14. 给开发同学的最终任务单

可以直接复制：

```text
任务：重新搭建正式开发环境，不继续维护旧 demo。

输入文件：
1. DEV_ENV_REBUILD_HANDOFF.md
2. COMPLETE_API_DOC.md

执行要求：
1. 新建干净项目目录。
2. 使用 FastAPI 搭建后端。
3. 使用前端页面或前端框架，通过 /api/... 请求后端。
4. 使用 Nginx 或前端代理把 /api 转到 FastAPI。
5. 使用 Docker Compose 一键启动前后端。
6. 先完成 /api/health、/api/device-status/options、/api/device-status/records。
7. 再接 /api/nacos/config。
8. 最后按 COMPLETE_API_DOC.md 第 11 节补业务最小验收接口。
9. 不允许依赖同学 demo 临时接口。
10. 每个接口必须能在 Swagger 看到，并提供 curl 自测结果。

交付：
- 新项目代码
- README 启动说明
- .env.example
- docker-compose.yml
- OpenAPI
- curl 自测结果
```

## 15. 一句话总结

这次不是教学，也不是继续接同学 demo；这次是重建正式开发环境。旧 demo 只能参考效果，不能作为接口依赖。后续开发以 `COMPLETE_API_DOC.md` 为 API 契约，以本文件为环境重建交接标准。
