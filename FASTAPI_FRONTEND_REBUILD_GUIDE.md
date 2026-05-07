# FastAPI 到前后端联调从零搭建教学指南

整理日期：`2026-05-06`

这份文档用于带同学从零搭建一个最小可用项目：后端用 FastAPI，前端用静态 HTML/JS，最后用 Nginx 和 Docker Compose 完成前后端联调。

目标不是一次写完所有业务，而是让每个同学理解完整链路：

```text
浏览器页面
  -> fetch("/api/...")
    -> Nginx 反向代理
      -> FastAPI 后端
        -> mock 数据 / Nacos 配置中心 / 后续业务数据库
```

## 1. 课堂目标

完成后，同学应该能做到：

| 能力 | 要求 |
|---|---|
| 搭 FastAPI | 能创建 `main.py`、启动接口、打开 Swagger |
| 写接口模型 | 能用 Pydantic 定义请求体和响应体 |
| 调接口 | 能用浏览器、Swagger、curl 调接口 |
| 前端请求 | 能用 `fetch` 调后端 API |
| 解决跨域 | 理解 CORS 和 Nginx 代理的区别 |
| Docker 部署 | 能用 `docker compose up -d --build` 同时启动前后端 |
| 对接 Nacos | 理解 Nacos 是配置中心，不是业务数据库 |

## 2. 项目最终结构

从零搭建时，最终目录建议长这样：

```text
project-root/
  backend/
    app/
      main.py
    scripts/
      generate_openapi.py
    .env.example
    Dockerfile
    openapi.json
    requirements.txt
  frontend/
    index.html
    nginx.conf
    Dockerfile
  docker-compose.yml
  README.md
  COMPLETE_API_DOC.md
```

当前仓库 `H:\zxcasdqwe` 已经是这个结构，可以作为标准答案。

## 3. 准备环境

### 3.1 必装工具

| 工具 | 用途 | 验证命令 |
|---|---|---|
| Python 3.12 | 跑 FastAPI | `python --version` |
| Docker Desktop | 容器运行前后端 | `docker --version` |
| PowerShell | 执行命令 | Windows 默认有 |
| VS Code | 编辑代码 | 可选但推荐 |
| curl | 测接口 | `curl --version` |

### 3.2 新人先检查

```powershell
python --version
docker --version
docker compose version
```

如果 Docker 命令失败，先启动 Docker Desktop。

## 4. 第一步：创建后端项目

### 4.1 创建目录

```powershell
mkdir demo-fastapi
cd demo-fastapi
mkdir backend
mkdir backend\app
mkdir backend\scripts
```

### 4.2 创建依赖文件

创建 `backend/requirements.txt`：

```txt
fastapi==0.115.12
uvicorn[standard]==0.34.2
httpx==0.28.1
python-dotenv==1.1.0
```

说明：

| 依赖 | 作用 |
|---|---|
| `fastapi` | Web API 框架 |
| `uvicorn` | ASGI 服务启动器 |
| `httpx` | 后端访问 Nacos 或第三方服务 |
| `python-dotenv` | 读取 `.env` 环境变量 |

### 4.3 创建环境变量样例

创建 `backend/.env.example`：

```env
PORT=8000
NACOS_BASE_URL=http://127.0.0.1:8848/nacos
NACOS_USERNAME=
NACOS_PASSWORD=
CORS_ALLOWED_ORIGINS=http://localhost:9000,http://localhost:8083
PUBLISH_API_KEY=change-this-to-a-strong-key
```

教学重点：

- `.env.example` 可以提交。
- `.env` 是真实环境配置，不应该提交。
- 密钥不要写进代码。

## 5. 第二步：写第一个 FastAPI 服务

创建 `backend/app/main.py`：

```py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Demo API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


class HealthResponse(BaseModel):
    status: str


@app.get("/api/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
```

启动：

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

验证：

```powershell
curl http://localhost:8000/api/health
```

预期：

```json
{"status":"ok"}
```

打开 Swagger：

```text
http://localhost:8000/docs
```

## 6. 第三步：加 CORS

前端直接访问 `http://localhost:8000` 时会遇到跨域问题，所以先加 CORS。

在 `main.py` 中加入：

```py
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

raw_origins = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:9000,http://localhost:8083",
)
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

教学重点：

- 开发环境可以临时放宽。
- 正式环境不要长期使用 `*`。
- 如果用 Nginx 代理，同源请求就不需要浏览器跨域。

## 7. 第四步：写一个设备状态 API

先不要接数据库，也不要接 Nacos，先用 mock 数据跑通前后端。

```py
from datetime import datetime, timedelta, timezone
from pydantic import Field

SHANGHAI_TZ = timezone(timedelta(hours=8))
ALL_OPTION = "全部"


class DeviceStatusRecord(BaseModel):
    region: str = Field(..., min_length=1)
    device: str = Field(..., min_length=1)
    online: int = Field(..., ge=0)
    offline: int = Field(..., ge=0)


class DeviceStatusOptionsResponse(BaseModel):
    regions: list[str]
    devices: list[str]


class DeviceStatusRecordsResponse(BaseModel):
    records: list[DeviceStatusRecord]
    updated_at: str = Field(..., alias="updatedAt")

    model_config = {"populate_by_name": True}


DEMO_RECORDS = [
    {"region": "A区", "device": "摄像机", "online": 86, "offline": 6},
    {"region": "A区", "device": "人员智能门/联锁门", "online": 120, "offline": 12},
    {"region": "F区", "device": "车辆识别与道闸", "online": 42, "offline": 5},
]


def now_text() -> str:
    return datetime.now(SHANGHAI_TZ).replace(microsecond=0).isoformat()


@app.get("/api/device-status/options", response_model=DeviceStatusOptionsResponse)
async def get_device_status_options(region: str = ALL_OPTION) -> DeviceStatusOptionsResponse:
    records = [DeviceStatusRecord(**item) for item in DEMO_RECORDS]
    regions = [ALL_OPTION] + sorted({item.region for item in records})
    devices = [ALL_OPTION] + sorted(
        {item.device for item in records if region == ALL_OPTION or item.region == region}
    )
    return DeviceStatusOptionsResponse(regions=regions, devices=devices)


@app.get("/api/device-status/records", response_model=DeviceStatusRecordsResponse)
async def get_device_status_records(
    region: str = ALL_OPTION,
    device: str = ALL_OPTION,
) -> DeviceStatusRecordsResponse:
    records = [DeviceStatusRecord(**item) for item in DEMO_RECORDS]
    filtered = [
        item
        for item in records
        if (region == ALL_OPTION or item.region == region)
        and (device == ALL_OPTION or item.device == device)
    ]
    return DeviceStatusRecordsResponse(records=filtered, updatedAt=now_text())
```

验证：

```powershell
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/records?region=A区&device=摄像机"
```

## 8. 第五步：前端页面调用后端

创建目录：

```powershell
mkdir frontend
```

创建 `frontend/index.html`：

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>FastAPI 联调 Demo</title>
    <style>
      body {
        font-family: "Segoe UI", "Microsoft Yahei", sans-serif;
        margin: 24px;
      }
      pre {
        background: #f3f4f6;
        padding: 12px;
        border-radius: 8px;
      }
    </style>
  </head>
  <body>
    <h1>FastAPI 前后端联调</h1>
    <button id="load">加载设备状态</button>
    <pre id="output">等待请求...</pre>

    <script>
      async function requestJson(url) {
        const resp = await fetch(url);
        const data = await resp.json().catch(() => null);
        if (!resp.ok) {
          throw new Error(data?.detail || data?.message || `HTTP ${resp.status}`);
        }
        return data;
      }

      document.getElementById("load").addEventListener("click", async () => {
        const output = document.getElementById("output");
        output.textContent = "加载中...";
        try {
          const data = await requestJson("/api/device-status/records?region=全部&device=全部");
          output.textContent = JSON.stringify(data, null, 2);
        } catch (err) {
          output.textContent = `请求失败：${err.message}`;
        }
      });
    </script>
  </body>
</html>
```

教学重点：

- 前端使用 `/api/...` 相对路径。
- 后面用 Nginx 把 `/api` 转发到后端。
- 不在前端写死 `http://localhost:8000`，部署更省事。

## 9. 第六步：Nginx 代理前端到后端

创建 `frontend/nginx.conf`：

```nginx
server {
  listen 80;
  server_name _;

  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://nacos-api:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

讲解：

```text
浏览器访问 http://localhost:9000/api/device-status/records
  -> Nginx 收到 /api/device-status/records
  -> 转发给 http://nacos-api:8000/api/device-status/records
  -> FastAPI 返回 JSON
```

## 10. 第七步：写 Dockerfile

创建 `backend/Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir --index-url ${PIP_INDEX_URL} -r /app/requirements.txt

COPY app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

创建 `frontend/Dockerfile`：

```dockerfile
FROM nginx:1.27-alpine

COPY index.html /usr/share/nginx/html/index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

## 11. 第八步：Docker Compose 同时启动

创建 `docker-compose.yml`：

```yaml
services:
  nacos-api:
    build:
      context: ./backend
    container_name: nacos-api
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    restart: unless-stopped
    extra_hosts:
      - "host.docker.internal:host-gateway"

  nacos-web:
    build:
      context: ./frontend
    container_name: nacos-web
    depends_on:
      - nacos-api
    ports:
      - "9000:80"
    restart: unless-stopped
```

启动：

```powershell
Copy-Item .\backend\.env.example .\backend\.env
docker compose up -d --build
```

验证：

```powershell
curl http://localhost:8000/api/health
curl http://localhost:9000/api/health
```

打开页面：

```text
http://localhost:9000
```

## 12. 第九步：接入 Nacos 配置

先讲清楚：Nacos 是配置中心，不是业务数据库。

适合放 Nacos：

- 页面刷新间隔。
- 设备状态 mock 数据。
- 字典配置。
- 告警阈值。

不适合放 Nacos：

- 人员通行流水。
- 车辆进出流水。
- 告警处置记录。
- 视频文件。

### 12.1 加 Nacos 读取接口

示例核心逻辑：

```py
import httpx

NACOS_BASE_URL = os.getenv("NACOS_BASE_URL", "http://127.0.0.1:8848/nacos").rstrip("/")


async def get_nacos_config(data_id: str, group: str = "DEFAULT_GROUP") -> str:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(
            f"{NACOS_BASE_URL}/v1/cs/configs",
            params={"dataId": data_id, "group": group},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Nacos read failed: {resp.text}")
    return resp.text
```

### 12.2 标准配置结构

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

## 13. 第十步：导出 OpenAPI

创建 `backend/scripts/generate_openapi.py`：

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

要求：

- 每次新增接口都重新导出。
- 文档必须和 OpenAPI 保持一致。

## 14. 课堂讲解顺序

建议你带同学时按这个节奏：

| 阶段 | 讲什么 | 结果 |
|---|---|---|
| 1 | FastAPI 是什么，Swagger 是什么 | 知道接口能自动生成文档 |
| 2 | 写 `/api/health` | 知道最小接口怎么跑 |
| 3 | 写 Pydantic 模型 | 知道请求/响应结构要固定 |
| 4 | 写设备状态 mock 接口 | 知道先 mock 跑通联调 |
| 5 | 前端用 `fetch` 请求 | 知道浏览器怎么拿 JSON |
| 6 | Nginx 代理 `/api` | 知道前后端同源联调 |
| 7 | Docker Compose | 知道怎么一键启动 |
| 8 | 接 Nacos | 知道配置中心怎么接入 |
| 9 | OpenAPI 和文档 | 知道代码变更要同步文档 |

## 15. 新同学必须记住的规则

### 15.1 API 规则

- 路径用小写和中划线：`/api/device-status/records`。
- JSON 字段用 `camelCase`：`dataId`、`pageSize`、`updatedAt`。
- Python 变量用 `snake_case`：`data_id`、`page_size`、`updated_at`。
- 列表接口返回 `items/page/pageSize/total`。
- 控制接口返回 `commandId/status/createdAt`。

### 15.2 状态码规则

| 状态码 | 意义 |
|---:|---|
| `200` | 成功 |
| `400` | 业务参数错 |
| `401` | 未登录或密钥错 |
| `403` | 无权限 |
| `404` | 资源不存在 |
| `409` | 状态冲突 |
| `422` | 字段校验失败 |
| `500` | 后端异常 |
| `502` | 下游服务异常 |
| `503` | 服务不可用或没配置 |

### 15.3 前端规则

- 所有请求都判断 `resp.ok`。
- 不要直接访问 Nacos。
- 请求失败保留旧数据。
- 大屏页面不能因为一个接口失败白屏。
- 自动刷新要清理定时器。

### 15.4 后端规则

- 新接口必须有 `response_model`。
- 新字段必须写类型。
- 错误用 `HTTPException`。
- 不要把密钥写进代码。
- 不要把 Nacos 当数据库。

## 16. 常见问题

### 16.1 为什么前端用 `/api/...`，不写 `localhost:8000`

因为正式部署时前端和后端通常不在同一个端口。前端写相对路径，交给 Nginx 代理，开发和部署都更稳定。

### 16.2 CORS 和 Nginx 代理有什么区别

CORS 是浏览器允许跨域请求的机制。Nginx 代理是让浏览器看起来访问同一个域名和端口。

教学时可以这么说：

```text
CORS 是允许跨域。
Nginx 代理是尽量不跨域。
```

### 16.3 为什么先 mock，再接 Nacos

因为前后端联调第一目标是跑通接口结构。结构跑通后，再把数据来源从 mock 换成 Nacos 或业务数据库。

### 16.4 Nacos 可以存业务数据吗

不可以。Nacos 只存配置。业务流水必须进业务数据库或对应业务系统。

## 17. 最终验收清单

同学完成后，至少能通过这些检查：

```powershell
curl http://localhost:8000/api/health
curl http://localhost:9000/api/health
curl "http://localhost:8000/api/device-status/options"
curl "http://localhost:8000/api/device-status/records?region=全部&device=全部"
```

浏览器打开：

```text
http://localhost:8000/docs
http://localhost:9000
```

检查结果：

| 检查项 | 通过标准 |
|---|---|
| FastAPI | Swagger 能打开 |
| 健康检查 | `/api/health` 返回 `{"status":"ok"}` |
| 设备状态 | 能返回 `records` |
| 前端页面 | 点击按钮能显示 JSON |
| Nginx 代理 | `localhost:9000/api/health` 能通 |
| Docker | 两个容器都正常运行 |

## 18. 你带同学时可以直接说的总结

“我们先不要一上来就做完整业务。第一步先把 FastAPI 跑起来，第二步用 Pydantic 固定接口结构，第三步让前端通过 `/api` 请求后端，第四步用 Nginx 和 Docker Compose 做成可部署形态。Nacos 只是配置中心，用来放配置和 mock 数据，不是数据库。所有接口变更都要同步 OpenAPI 和团队 API 文档。”
