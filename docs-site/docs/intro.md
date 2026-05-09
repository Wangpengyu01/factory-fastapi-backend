---
id: intro
title: 文档入口
slug: /intro
---

# 文档入口

文档集版本：`DOC-2026.05.08`

本文档站用于同步正式开发环境、接口契约、前后端落地任务和硬件模拟器口径。

## 当前版本口径

| 版本 | 类型 | 状态 | 说明 |
|---|---|---|---|
| `LEGACY-FE-8083` | 前端保留版本 | 保留使用 | 服务器上的 `8083` Vue + Vite 前端入口 |
| `API-CURRENT-0.2` | 当前已落地 API | 可运行 | 当前 FastAPI 最小闭环接口，已补齐大屏聚合和 Nacos 模拟器链路 |
| `API-TARGET-1.0` | 全量目标 API | 待补齐 | 对齐 OpenAPI 的 `71` 个操作 |
| `SIM-0.1` | 硬件状态机模拟器 | 已落地 | Python 内存状态机模拟器 |
| `SIM-0.2` | 硬件接入落地目标 | 本轮落地 | 状态上报、事件上报、命令回执、离线判断 |
| `OPENAPI-8082-CURRENT-2026.05.08` | OpenAPI 快照 | 当前参考 | 文档站发布的 OpenAPI JSON |

## 当前环境

| 内容 | 结论 |
|---|---|
| `服务器IP:8083` | 保留为现有 Vue + Vite 前端入口 |
| `服务器IP:8082/docs` | 作为当前 API Swagger 参考 |
| 后端 | 使用 FastAPI 从零到一重建 |
| API 调用 | 前端统一走 `/api/...` |
| Nacos | 只作为配置中心，不作为业务数据库 |

## 快速入口

- [版本说明](./version-guide)
- [开发人员从零到一](./developer-rebuild)
- [后端全量 API 落地任务书](./backend-full-landing-task-book)
- [前端全量落地任务书](./frontend-full-landing-task-book)
- [后端现阶段 API 落地文档](./backend-current-api)
- [大屏聚合与 Nacos 链路补齐 API](./dashboard-aggregate-nacos-chain-api)
- [8083 前端缺口 API 补齐文档](./frontend-gap-api-completion)
- [硬件状态机与硬件接入落地文档](./hardware-state-machine-simulator)
- [8082/8083 API 契约](./team-api-contract)
- [技术协议功能对照与缺口 API 补充文档](./protocol-api-gap-and-supplement)
- [完整 API 文档](./complete-api-doc)
- [Scalar OpenAPI](/openapi)
- [OpenAPI JSON](https://wpengu.top/openapi.json)
