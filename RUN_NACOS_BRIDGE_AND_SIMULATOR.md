# Nacos 配置桥和 Python 模拟设备运行手册

这份手册只讲当前代码怎么跑起来。当前项目里：

- Nacos 配置桥在 `backend/app/main.py`，接口是 `/api/nacos/config`
- Python 模拟设备在 `backend/app/hardware_state_machine.py`，接口是 `/api/simulator/*`
- 两者都运行在同一个 FastAPI 服务里，不需要分别启动两个 Python 进程

## 1. 本地直接运行

在 PowerShell 里执行：

```powershell
cd H:\zxcasdqwe\backend

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

然后按你的环境修改 `backend\.env`：

```env
PORT=8000

# 本机直接运行 FastAPI，并且 Nacos 也跑在本机时用这个。
NACOS_BASE_URL=http://127.0.0.1:8848/nacos

# Nacos 2.x / 2.5.1 用 v1；Nacos 3.x 才用 v3。
NACOS_API_VERSION=v1

# Nacos 没开鉴权就留空；开了鉴权再填。
NACOS_USERNAME=
NACOS_PASSWORD=

# 发布配置接口的密钥，本地也建议改一下。
PUBLISH_API_KEY=dev-publish-key

# 启用 Python 内存状态机模拟设备。
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5

# 打开后形成链路：Python 模拟器 -> Nacos -> FastAPI -> 大屏。
SIMULATOR_NACOS_SYNC_ENABLED=true
SIMULATOR_NACOS_DATA_ID=factory.hardware.snapshot.json
SIMULATOR_NACOS_GROUP=DEFAULT_GROUP
DEVICE_STATUS_SOURCE=nacos
DEVICE_STATUS_NACOS_DATA_ID=factory.hardware.snapshot.json
DEVICE_STATUS_NACOS_FIELD=deviceStatus.records
NACOS_READ_FALLBACK_TO_SIMULATOR=true

# 底部四个子系统入口；不配置时接口返回 enabled=false，前端不要回退 localhost。
SUBSYSTEM_BASE_URL=
SUBSYSTEM_FACE_URL=
SUBSYSTEM_VEHICLE_URL=
SUBSYSTEM_RAIL_URL=
SUBSYSTEM_FIRE_URL=
```

启动 FastAPI：

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问地址：

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`
- 模拟器汇总: `http://localhost:8000/api/simulator/summary`
- 8083 设备状态: `http://localhost:8000/api/device-status/records`
- 大屏聚合: `http://localhost:8000/api/dashboard/aggregate`
- 底部子系统入口: `http://localhost:8000/api/subsystems`

## 2. Docker Compose 运行

先准备环境文件：

```powershell
cd H:\zxcasdqwe
Copy-Item backend\.env.example backend\.env
```

如果 Nacos 跑在宿主机，而 FastAPI 跑在 Docker 容器里，把 `backend\.env` 里的地址改成：

```env
NACOS_BASE_URL=http://host.docker.internal:8848/nacos
```

启动：

```powershell
docker compose up --build
```

访问地址：

- FastAPI: `http://localhost:8000/docs`
- 静态演示前端: `http://localhost:9000`

如果你没有启动 Nacos，模拟器和设备状态接口仍然可用；只有 `/api/nacos/config` 读写真实 Nacos 配置时会失败。

## 3. 快速检查命令

健康检查：

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

查看模拟器汇总：

```powershell
Invoke-RestMethod http://localhost:8000/api/simulator/summary
```

查看模拟设备列表：

```powershell
Invoke-RestMethod "http://localhost:8000/api/simulator/devices?areaId=r01&deviceType=smoke"
```

手动推进模拟器状态：

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/api/simulator/tick?steps=10"
```

手动推进并立刻写入 Nacos：

```powershell
Invoke-RestMethod -Method Post "http://localhost:8000/api/simulator/tick?steps=1&syncNacos=true"
```

手动把当前模拟器快照写入 Nacos：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/simulator/nacos-sync" `
  -Headers @{ "X-Publish-Key" = "dev-publish-key" }
```

查看大屏聚合数据：

```powershell
Invoke-RestMethod http://localhost:8000/api/dashboard/aggregate
Invoke-RestMethod http://localhost:8000/api/subsystems
```

给单个模拟设备下发命令：

```powershell
$body = @{
  command = "fault"
  reason = "联调测试"
  operator = "tester"
  payload = @{}
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/simulator/devices/smoke_r01_001/command" `
  -ContentType "application/json" `
  -Body $body
```

读取 Nacos 单个配置：

```powershell
Invoke-RestMethod "http://localhost:8000/api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP"
```

发布 Nacos 配置：

```powershell
$content = @{
  deviceStatus = @{
    records = @(
      @{
        region = "A区"
        device = "摄像机"
        online = 8
        offline = 1
      }
    )
  }
} | ConvertTo-Json -Depth 5 -Compress

$body = @{
  dataId = "device-status.json"
  group = "DEFAULT_GROUP"
  type = "json"
  content = $content
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/nacos/config" `
  -Headers @{ "X-Publish-Key" = "dev-publish-key" } `
  -ContentType "application/json" `
  -Body $body
```

## 4. 当前代码分工

| 文件 | 作用 |
|---|---|
| `backend/app/main.py` | FastAPI 入口，注册 Nacos、设备状态、Dashboard、模拟器接口 |
| `backend/app/hardware_state_machine.py` | Python 内存状态机，模拟门禁、道闸、摄像机、烟感、温感等硬件 |
| `backend/.env.example` | 本地和容器运行需要的环境变量模板 |
| `docker-compose.yml` | 同时启动 FastAPI 和旧静态演示前端 |
| `frontend/nginx.conf` | 把前端 `/api/*` 代理到 `nacos-api:8000` |

## 5. 常见问题

### `/api/simulator/*` 能用，`/api/nacos/config` 失败

这通常是 Nacos 没启动，或者 `NACOS_BASE_URL` 配错了。

- 本地直接运行 FastAPI：`NACOS_BASE_URL=http://127.0.0.1:8848/nacos`
- Docker 里运行 FastAPI，Nacos 在宿主机：`NACOS_BASE_URL=http://host.docker.internal:8848/nacos`
- Docker 同网络里另有 Nacos 服务：`NACOS_BASE_URL=http://nacos:8848/nacos`

### 设备状态为什么会自己变化

因为 `.env` 里默认：

```env
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
```

FastAPI 启动后会每 5 秒自动推进一次状态机。要关闭自动变化，把 `SIMULATOR_AUTO_TICK=false`。

### 前端怎么接

前端统一请求相对路径 `/api/...`。用 Docker Compose 跑 `nacos-web` 时，Nginx 会把 `/api/*` 转发到 FastAPI。

本地开发前端如果单独跑在 `8083`，后端已经默认允许：

```env
CORS_ALLOWED_ORIGINS=http://localhost:9000,http://localhost:8083
```
