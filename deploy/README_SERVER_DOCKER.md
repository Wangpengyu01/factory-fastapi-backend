# 服务器 Docker 部署说明

这份说明用于把 Nacos、FastAPI 配置桥、Python 模拟设备、静态演示前端都跑在同一台服务器上。

## 1. 服务组成

| 服务 | 容器名 | 端口 | 说明 |
|---|---|---|---|
| Nacos | `factory-nacos` | `127.0.0.1:8848`、`127.0.0.1:9848` | 配置中心，只绑定服务器本机 |
| FastAPI | `nacos-api` | `8000` | Nacos 配置桥和 Python 模拟设备 |
| 前端 | `nacos-web` | `9000` | 静态演示前端，`/api/*` 代理到 FastAPI |

Nacos 在 Docker 网络内的地址是：

```text
http://nacos:8848/nacos
```

所以服务器 Docker 部署时，不要把后端的 `NACOS_BASE_URL` 写成 `127.0.0.1`。

## 2. 首次部署

在服务器上执行：

```bash
git clone https://github.com/Wangpengyu01/factory-fastapi-backend.git
cd factory-fastapi-backend

mkdir -p deploy
cp deploy/server.env.example deploy/server.env
```

编辑 `deploy/server.env`：

```bash
nano deploy/server.env
```

至少要改：

```env
CORS_ALLOWED_ORIGINS=http://服务器IP:9000,http://服务器IP:8000
PUBLISH_API_KEY=换成强密码
```

启动：

```bash
docker compose -f docker-compose.server.yml up --build -d
```

## 3. 访问地址

把 `服务器IP` 换成你的公网 IP 或域名：

```text
FastAPI Swagger:
http://服务器IP:8000/docs

模拟设备汇总:
http://服务器IP:8000/api/simulator/summary

设备状态聚合:
http://服务器IP:8000/api/device-status/records

静态演示前端:
http://服务器IP:9000
```

Nacos 默认只绑定到服务器本机，不直接开放公网。需要看 Nacos 控制台时，建议用 SSH 隧道：

```bash
ssh -L 8848:127.0.0.1:8848 root@服务器IP
```

然后在你自己电脑浏览器打开：

```text
http://127.0.0.1:8848/nacos
```

如果你明确要把 Nacos 控制台开放到公网，把 `docker-compose.server.yml` 里的：

```yaml
- "127.0.0.1:8848:8848"
```

改成：

```yaml
- "8848:8848"
```

同时必须配置安全组/防火墙，不建议公网裸露未鉴权 Nacos。

## 4. 常用运维命令

查看服务：

```bash
docker compose -f docker-compose.server.yml ps
```

查看后端日志：

```bash
docker compose -f docker-compose.server.yml logs -f nacos-api
```

查看 Nacos 日志：

```bash
docker compose -f docker-compose.server.yml logs -f nacos
```

重启：

```bash
docker compose -f docker-compose.server.yml restart
```

停止：

```bash
docker compose -f docker-compose.server.yml down
```

停止并清掉 Nacos 数据卷：

```bash
docker compose -f docker-compose.server.yml down -v
```

## 5. 验证接口

在服务器上执行：

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/simulator/summary
curl http://127.0.0.1:8000/api/device-status/records
curl http://127.0.0.1:8000/api/dashboard/aggregate
curl http://127.0.0.1:8000/api/subsystems
```

手动推进模拟器：

```bash
curl -X POST "http://127.0.0.1:8000/api/simulator/tick?steps=10"
```

手动推进并立刻写入 Nacos：

```bash
curl -X POST "http://127.0.0.1:8000/api/simulator/tick?steps=1&syncNacos=true"
```

手动把当前模拟器快照写入 Nacos：

```bash
curl -X POST "http://127.0.0.1:8000/api/simulator/nacos-sync" \
  -H "X-Publish-Key: 你的PUBLISH_API_KEY"
```

发布一条 Nacos 配置：

```bash
curl -X POST "http://127.0.0.1:8000/api/nacos/config" \
  -H "Content-Type: application/json" \
  -H "X-Publish-Key: 你的PUBLISH_API_KEY" \
  -d '{
    "dataId": "device-status.json",
    "group": "DEFAULT_GROUP",
    "type": "json",
    "content": "{\"deviceStatus\":{\"records\":[{\"region\":\"A区\",\"device\":\"摄像机\",\"online\":8,\"offline\":1}]}}"
  }'
```

读取配置：

```bash
curl "http://127.0.0.1:8000/api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP"
```

## 6. 防火墙建议

服务器安全组至少放行：

| 端口 | 用途 |
|---|---|
| `8000` | FastAPI 接口 |
| `9000` | 静态演示前端 |

默认不需要放行：

| 端口 | 用途 |
|---|---|
| `8848` | Nacos 控制台和 HTTP API |
| `9848` | Nacos gRPC |

因为服务器版 compose 默认把 Nacos 绑定在 `127.0.0.1`。
