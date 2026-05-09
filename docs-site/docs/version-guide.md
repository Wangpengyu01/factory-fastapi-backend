---
id: version-guide
title: 版本说明
slug: /version-guide
---

# 版本说明

更新日期：`2026-05-08`

本文档用于统一团队对“当前版本、目标版本、保留版本、文档版本”的理解。后续所有接口、前端、后端、模拟器和交付文档都按本页的版本口径标注。

## 1. 版本总览

| 版本标识 | 类型 | 当前状态 | 说明 |
|---|---|---|---|
| `LEGACY-FE-8083` | 前端保留版本 | 保留使用 | 当前服务器上的 `8083` Vue + Vite 前端入口，作为页面适配和联调入口 |
| `API-CURRENT-0.2` | 当前已落地 API | 可运行 | 当前 FastAPI 已落地的最小闭环接口，包含设备状态、模拟器、Dashboard 聚合、Nacos 模拟器链路等基础能力 |
| `API-TARGET-1.0` | 全量目标 API | 待补齐 | 对齐 OpenAPI 的全量接口目标，共 `71` 个操作 |
| `SIM-0.1` | 硬件状态机模拟器 | 已落地 | Python 内存状态机，用于硬件未接入前的前后端联调 |
| `SIM-0.2` | 硬件接入落地目标 | 本轮落地 | 状态上报、事件上报、命令回执、离线判断、状态快照存储 |
| `OPENAPI-8082-CURRENT-2026.05.08` | OpenAPI 快照 | 当前参考 | 当前文档站发布的 `openapi.json` 快照 |
| `DOC-2026.05.08` | 文档版本 | 当前文档集 | 当前文档站所有开发文档的统一版本日期 |

## 2. 文档版本对应关系

| 文档 | 文档版本 | 对应系统版本 | 用途 |
|---|---|---|---|
| [文档入口](./intro) | `DOC-INDEX-1.1` | 全局 | 团队入口和版本导航 |
| [从零到一开发文档](./developer-rebuild) | `DOC-REBUILD-1.1` | `API-TARGET-1.0` | 重新搭建开发环境和项目结构 |
| [后端全量 API 落地任务书](./backend-full-landing-task-book) | `DOC-BE-TASK-1.1` | `API-TARGET-1.0` | 后端全量接口实现任务 |
| [前端全量落地任务书](./frontend-full-landing-task-book) | `DOC-FE-TASK-1.1` | `LEGACY-FE-8083` + `API-TARGET-1.0` | Vue + Vite 前端改造和联调任务 |
| [后端现阶段 API 落地文档](./backend-current-api) | `DOC-BE-CURRENT-1.2` | `API-CURRENT-0.2` | 当前已经可运行的后端接口说明 |
| [大屏聚合与 Nacos 链路补齐 API](./dashboard-aggregate-nacos-chain-api) | `DOC-DASHBOARD-NACOS-1.0` | `API-CURRENT-0.2` | 本轮补齐的大屏聚合接口和模拟器写 Nacos 链路 |
| [8083 前端缺口 API 补齐文档](./frontend-gap-api-completion) | `DOC-FE-GAP-API-1.0` | `LEGACY-FE-8083` + `API-CURRENT-0.2` | 中间主画面、右侧面板、子系统入口和接口模式的对接口径 |
| [硬件状态机与硬件接入落地文档](./hardware-state-machine-simulator) | `DOC-SIM-1.2` | `SIM-0.1` + `SIM-0.2` | 硬件状态抽象、模拟器接口、真实硬件接入任务 |
| [8082/8083 API 契约](./team-api-contract) | `DOC-CONTRACT-1.1` | `OPENAPI-8082-CURRENT-2026.05.07` | 前后端字段、状态码、返回结构契约 |
| [技术协议功能对照与缺口 API 补充文档](./protocol-api-gap-and-supplement) | `DOC-PROTOCOL-GAP-0.0.2` | `API-TARGET-1.0` | 技术协议功能点与现有 API 覆盖情况对照 |
| [完整 API 文档](./complete-api-doc) | `DOC-API-FULL-2.1` | `API-TARGET-1.0` | 全量 API 汇总和接口清单 |

## 3. 状态定义

| 状态 | 含义 | 开发处理 |
|---|---|---|
| 当前已落地 | 代码中已经有可运行接口或页面 | 可以直接联调，发现问题按缺陷修复 |
| 保留使用 | 旧入口继续使用，但内部实现可以逐步替换 | 不删除入口，按新契约适配 |
| 目标版本 | 当前任务要求最终完成的版本 | 按任务书拆分实现 |
| 快照版本 | 某一天固定下来的接口或文档状态 | 用于对照，不代表后续不能更新 |
| 废弃 | 不再作为正式开发依据 | 只能作为历史参考，不允许新增依赖 |

## 4. 更新规则

| 场景 | 必须更新 |
|---|---|
| 后端新增或修改接口 | 更新 OpenAPI、[后端现阶段 API 落地文档](./backend-current-api)、[8082/8083 API 契约](./team-api-contract) |
| 前端新增页面或调整路由 | 更新 [前端全量落地任务书](./frontend-full-landing-task-book) |
| 全量任务范围变化 | 更新 [后端全量 API 落地任务书](./backend-full-landing-task-book) 和 [完整 API 文档](./complete-api-doc) |
| 模拟器状态或命令变化 | 更新 [硬件状态机模拟器](./hardware-state-machine-simulator) |
| 版本口径变化 | 更新本文档和 [文档入口](./intro) |

## 5. 对外沟通口径

当前对团队统一说明：

| 问题 | 统一回答 |
|---|---|
| 前端是不是重做 | 入口保留 `8083`，框架按 Vue + Vite 继续调试和改造 |
| 后端是不是继续旧 demo | 不是，后端按 FastAPI 从零到一落地 |
| 当前能不能联调 | 可以，先用 `API-CURRENT-0.2` 和 `SIM-0.1` 联调，真实硬件按 `SIM-0.2` 接入 |
| 最终接口按什么做 | 按 `API-TARGET-1.0` 和 `OPENAPI-8082-CURRENT-2026.05.07` 补齐 |
| Nacos 做什么 | 只做配置中心，不做业务数据库 |
