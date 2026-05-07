# API 文档同步摘要

更新时间：`2026-04-24`

## 1. 这次同步做了什么

本次主要把 API 文档统一到“代码真实实现”和“业务方案文档”两条线：

- 当前仓库已实现接口，只按 `backend/app/main.py` 和 `backend/openapi.json` 讲
- 大屏业务接口范围稿，单独保留为方案文档，不再写成“当前仓库已实现”

## 2. 当前仓库真实已实现的接口

共 `5` 个：

1. `GET /api/health`
2. `GET /api/nacos/config`
3. `POST /api/nacos/config`
4. `GET /api/device-status/options`
5. `GET /api/device-status/records`

## 3. 已明确为方案稿的内容

下面这些内容保留在业务文档里，但不属于当前仓库已经落地的 FastAPI 路由：

- `GET /api/tree-menu`
- `GET /api/point/{point_id}/latest-measurement`
- `GET /api/point/{point_id}/history-measurements`
- `GET /api/premade-point/{premade_point_id}/latest-image`
- `GET /api/latest-measurements`
- `GET/POST/DELETE /api/v1/inspection/*`
- `GET /api/dashboard/overview`

## 4. 这次重点统一的口径

- 当前 FastAPI 返回裸 JSON，不使用 `success/message/data` 包装
- `backend/openapi.json` 已重新生成，并补齐 `device-status` 两个路由
- `README.md`、`API_DOC.md`、`DEVICE_STATUS_WIDGET_8083_DOC.md`、`FRONTEND_DEMO_GUIDE.md` 已按同一口径更新
- `BLOG_NACOS_FASTAPI_BIGSCREEN.md`、`DASHBOARD_OVERVIEW_API_DOC.md` 已改成“方案稿”表述
- `blog-site` 静态文档站已重新生成

## 5. 已同步的主要文件

- `README.md`
- `API_DOC.md`
- `DEVICE_STATUS_WIDGET_8083_DOC.md`
- `FRONTEND_DEMO_GUIDE.md`
- `BLOG_NACOS_FASTAPI_BIGSCREEN.md`
- `DASHBOARD_OVERVIEW_API_DOC.md`
- `build_blog_docs.py`
- `backend/openapi.json`
- `blog-site/`

## 6. 服务器侧建议

如果你后续要对外展示：

- 查当前已实现接口：优先看 `API_DOC.md`
- 查 8083 设备状态控件：优先看 `DEVICE_STATUS_WIDGET_8083_DOC.md`
- 做汇报或解释螺栓/开距/首页概览：看业务范围稿，但要明确这是方案文档

## 7. 一句话结论

这次同步的核心结果是：以后再看这套文档时，不会把“仓库里已经有实现的接口”和“业务侧还在规划或另有系统实现的接口”混在一起。
