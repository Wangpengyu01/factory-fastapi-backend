# 只部署后端 Docker 说明

这份说明适用于：服务器上已经有 Nacos，或者你已经单独把 Nacos 跑起来了，现在只需要把本仓库后端跑起来。

本仓库后端包含：

- Nacos 配置桥：`/api/nacos/config`
- Python 模拟设备：`/api/simulator/*`
- 设备状态聚合：`/api/device-status/*`
- Dashboard 概览：`/api/dashboard/overview`

## 1. 准备配置

在服务器上执行：

```bash
git clone https://github.com/Wangpengyu01/factory-fastapi-backend.git
cd factory-fastapi-backend

cp deploy/backend.env.example deploy/backend.env
nano deploy/backend.env
```

按实际情况修改 `NACOS_BASE_URL`：

```env
# Nacos 容器和后端容器在同一个 Docker 网络里，服务名叫 nacos
NACOS_BASE_URL=http://nacos:8848/nacos

# Nacos 跑在服务器宿主机
NACOS_BASE_URL=http://host.docker.internal:8848/nacos

# Nacos 跑在另一台服务器
NACOS_BASE_URL=http://NACOS服务器IP:8848/nacos
```

同时改掉：

```env
CORS_ALLOWED_ORIGINS=http://你的服务器IP:8000,http://你的服务器IP:9000,http://你的服务器IP:8083
PUBLISH_API_KEY=换成强密码
```

## 2. 启动后端

```bash
docker compose -f docker-compose.backend.yml up --build -d
```

查看状态：

```bash
docker compose -f docker-compose.backend.yml ps
```

查看日志：

```bash
docker compose -f docker-compose.backend.yml logs -f backend
```

## 3. 如果 Nacos 也在 Docker 里

如果 Nacos 容器已经存在，并且你想让后端通过 `http://nacos:8848/nacos` 访问它，两个容器必须在同一个 Docker 网络。

创建网络：

```bash
docker network create factory-net
```

把已有 Nacos 容器加入这个网络：

```bash
docker network connect factory-net nacos
```

启动后端时也加入同一个网络：

```bash
docker compose -f docker-compose.backend.yml up --build -d
docker network connect factory-net factory-fastapi-backend
```

如果你的 Nacos 容器名不是 `nacos`，要么把 `deploy/backend.env` 里的 `NACOS_BASE_URL` 改成真实容器名，要么给容器添加网络别名。

## 4. 验证

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:8000/api/simulator/summary
curl http://127.0.0.1:8000/api/device-status/records
```

测试 Nacos 配置读取：

```bash
curl "http://127.0.0.1:8000/api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP"
```

如果模拟设备接口正常、Nacos 接口失败，优先检查 `NACOS_BASE_URL` 和 Docker 网络。

## 5. 对外端口

后端默认监听：

```text
http://服务器IP:8000
```

Swagger：

```text
http://服务器IP:8000/docs
```

服务器安全组需要放行 `8000`。
