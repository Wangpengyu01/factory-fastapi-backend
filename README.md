# Factory FastAPI Backend

版本：`0.1.0`

本仓库用于管理成品库区域全封闭管控系统的 Python FastAPI 后端、硬件状态机模拟器、接口文档和前端对接资料。

## 当前口径

| 项 | 说明 |
|---|---|
| 前端入口 | 保留 `101.43.49.78:8083`，框架为 Vue + Vite |
| 后端 | FastAPI，从零到一重建 |
| API 调用 | 前端统一走 `/api/...` |
| Nacos | 只作为配置中心，不作为业务数据库 |
| 硬件状态 | 当前使用 Python 状态机模拟，可写入 Nacos 后由 FastAPI 统一读取 |
| 文档站 | `https://wpengu.top/` |
| OpenAPI | `https://wpengu.top/openapi/` |

## 目录

```text
backend/      FastAPI 后端代码
frontend/     旧静态演示前端
docs-site/    Docusaurus + Scalar 文档站源码
*.md          项目交付和接口文档
```

## 文档入口

- 运行 Nacos 配置桥和 Python 模拟设备：`RUN_NACOS_BRIDGE_AND_SIMULATOR.md`
- 只部署后端 Docker：`deploy/README_BACKEND_ONLY_DOCKER.md`
- 服务器 Docker 全量部署：`deploy/README_SERVER_DOCKER.md`
- 当前后端已落地接口：`BACKEND_CURRENT_IMPLEMENTED_API_DOC.md`
- 大屏聚合与 Nacos 链路补齐：`DASHBOARD_AGGREGATE_NACOS_CHAIN_API.md`
- 硬件状态机模拟器设计：`HARDWARE_STATE_MACHINE_SIMULATOR.md`

## Python 版本

推荐 Python `3.12`。

```powershell
python --version
```

## 后端启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：

- Swagger: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health: `http://localhost:8000/api/health`

## Nacos 配置桥和 Python 模拟设备

当前 Nacos 配置桥和 Python 硬件状态机模拟器都挂在同一个 FastAPI 服务里：

- Nacos 配置桥：`GET/POST /api/nacos/config`
- Python 模拟器：`GET/POST /api/simulator/*`
- 8083 设备状态聚合：`GET /api/device-status/*`
- 8083 大屏完整聚合：`GET /api/dashboard/aggregate`
- 8083 底部子系统入口：`GET /api/subsystems`

完整运行步骤见 [RUN_NACOS_BRIDGE_AND_SIMULATOR.md](RUN_NACOS_BRIDGE_AND_SIMULATOR.md)。

## 版本管理

当前版本号维护在：

- `VERSION`
- `backend/app/__init__.py`
- `backend/pyproject.toml`
- `CHANGELOG.md`

发版时四处版本号必须同步。

## 检查命令

```powershell
python -m py_compile backend/app/main.py backend/app/hardware_state_machine.py backend/scripts/generate_openapi.py
python backend/scripts/generate_openapi.py
```

## GitHub Actions

仓库包含 `.github/workflows/python-backend.yml`，推送到 `main` 或创建 PR 时会执行：

- 安装 Python 依赖
- 编译后端 Python 文件
- 重新生成 OpenAPI
