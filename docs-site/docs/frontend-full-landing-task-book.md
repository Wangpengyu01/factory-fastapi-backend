---
id: frontend-full-landing-task-book
title: 前端全量落地任务书
slug: /frontend-full-landing-task-book
---

# 前端全量落地任务书

| 项 | 值 |
|---|---|
| 文档版本 | `DOC-FE-TASK-1.1` |
| 文档集 | `DOC-2026.05.07` |
| 适用系统版本 | `LEGACY-FE-8083` + `API-TARGET-1.0` |
| 前端技术版本 | `Vue + Vite`，本地调试端口 `8083` |
| 当前状态 | 前端全量改造和联调任务 |
| 更新日期 | `2026-05-07` |

版本日期：2026-05-07

本文档给前端开发人员执行使用。目标是在保留现有 `101.43.49.78:8083` 前端入口的前提下，把旧 demo 前端改造成可对接正式 FastAPI 后端、可持续维护、可联调、可交付的前端项目。

## 1. 项目边界

| 项 | 结论 |
|---|---|
| 前端框架 | 使用 `Vue + Vite`，本地调试端口固定为 `8083` |
| 前端入口 | 保留 `101.43.49.78:8083` |
| 后端入口 | 开发期直接对接 `101.43.49.78:8082`，页面请求统一走 `/api/...` |
| API 文档 | `https://wpengu.top/openapi/` |
| OpenAPI JSON | `https://wpengu.top/openapi.json` |
| Swagger 参考 | `http://101.43.49.78:8082/docs` |
| 旧 demo 数据 | 只能放在 `mock` 或 `fixtures` 目录，正式页面不得直接写死 demo 数据 |
| Nacos | 前端不直接读写 Nacos；只有管理员配置页可调用后端封装后的 `/api/nacos/config` |
| 硬件状态 | 前端统一读取后端状态机或正式硬件接口返回值，不在页面内自行随机生成状态 |

## 2. 最终交付目标

前端最终必须完成以下交付：

| 编号 | 交付物 | 验收口径 |
|---|---|---|
| FE-D01 | 环境配置 | 本地、测试、线上 API 地址可切换，默认请求路径为 `/api/...` |
| FE-D02 | 统一 API 封装 | 页面组件内不存在裸 `fetch`、裸 `axios`、硬编码后端地址 |
| FE-D03 | 类型与字段字典 | 所有状态、枚举、颜色、文案集中维护 |
| FE-D04 | 全量页面路由 | 仪表盘、设备、告警、事件、巡检、视频、门禁、车辆、铁路联动、AI、报表、审计、模拟器页面可访问 |
| FE-D05 | 权限规则 | 路由和按钮具备角色权限控制，未授权页面显示 `403` |
| FE-D06 | 异常处理 | HTTP 状态码和业务错误码统一处理 |
| FE-D07 | 空态与加载态 | 表格、详情、图表、视频、表单均有 loading、empty、error 状态 |
| FE-D08 | 联调完成 | 所有页面接真实 API 或后端模拟器 API，不依赖页面内假数据 |
| FE-D09 | 构建发布 | `npm run build` 成功，发布到现有 `8083` 前端入口 |

## 3. 开发环境要求

### 3.1 本地运行

前端项目使用 `Vue + Vite`。`package.json` 必须提供以下脚本：

```json
{
  "scripts": {
    "dev": "vite --host 0.0.0.0 --port 8083",
    "build": "vue-tsc --noEmit && vite build",
    "lint": "eslint .",
    "typecheck": "vue-tsc --noEmit",
    "preview": "vite preview --host 0.0.0.0 --port 8083"
  }
}
```

如果旧项目暂时没有 TypeScript，`typecheck` 可以先保留为空检查脚本，但新增代码按 `Vue 3 + TypeScript` 口径编写。

### 3.2 环境变量

前端必须提供 `.env.example`：

```env
VITE_API_BASE_URL=/api
VITE_API_TIMEOUT_MS=15000
VITE_OPENAPI_URL=https://wpengu.top/openapi.json
VITE_ENABLE_MOCK=false
VITE_ENABLE_SIMULATOR=true
```

所有前端环境变量统一使用 `VITE_` 前缀，页面代码只能通过 `import.meta.env` 读取。

### 3.3 代理规则

开发环境必须把 `/api` 代理到后端：

```js
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "0.0.0.0",
    port: 8083,
    proxy: {
      "/api": {
        target: "http://101.43.49.78:8082",
        changeOrigin: true
      }
    }
  }
});
```

线上 `8083` 必须由 Nginx 或同等网关把 `/api` 转发到后端服务，不允许前端页面硬编码 `http://101.43.49.78:8082`。

## 4. 代码目录规范

旧项目已有目录时，在原目录基础上迁移；没有时按以下结构建立：

```text
src/
  main.ts
  App.vue
  api/
    http.ts
    endpoints.ts
    types.ts
    error.ts
    modules/
      dashboard.ts
      devices.ts
      alarms.ts
      events.ts
      inspection.ts
      video.ts
      access.ts
      vehicle.ts
      railway.ts
      ai.ts
      reports.ts
      audit.ts
      simulator.ts
      nacos.ts
  assets/
  components/
    common/
    data-table/
    status-tag/
    page-state/
  constants/
    enums.ts
    routes.ts
    permissions.ts
  layouts/
    DefaultLayout.vue
  pages/
    dashboard/
      DashboardView.vue
    devices/
      DeviceStatusView.vue
      DeviceListView.vue
      DeviceDetailView.vue
    alarms/
      AlarmListView.vue
      AlarmDetailView.vue
    simulator/
      SimulatorView.vue
  router/
    index.ts
  stores/
    auth.ts
    app.ts
  styles/
  utils/
  mock/
  tests/
```

Vue 文件规则：

| 规则 | 要求 |
|---|---|
| 组件写法 | 统一使用 `<script setup lang="ts">` |
| 页面命名 | 页面组件使用 `*View.vue` |
| 公共组件命名 | 公共组件使用业务含义命名，不使用 `Comp1`、`CommonBox` 这类名称 |
| 路由 | 使用 `vue-router`，路由配置集中在 `src/router/index.ts` |
| 全局状态 | 使用 `Pinia`，只放登录态、权限、全局配置和跨页面共享状态 |
| 页面状态 | 页面自己的筛选、分页、弹窗状态放在页面组件内 |

代码规则：

| 规则 | 要求 |
|---|---|
| API 调用 | 只能通过 `src/api/modules/*` 暴露函数 |
| 页面组件 | 只负责渲染、交互和调用模块函数 |
| 状态枚举 | 只能从 `src/constants/enums.ts` 引用 |
| 路由配置 | 只能从 `src/constants/routes.ts` 或路由文件维护 |
| 权限配置 | 只能从 `src/constants/permissions.ts` 维护 |
| 样式 | 公共样式集中在 `styles`，页面样式跟随页面目录 |
| mock 数据 | 只能在 `mock` 或 `fixtures`，不能写入业务组件 |
| 时间处理 | 统一使用 `YYYY-MM-DD HH:mm:ss` 展示 |
| 金额/数量 | 统一走格式化工具，不在页面散写 |

## 5. API 封装标准

### 5.1 统一返回结构

前端统一按以下结构解析后端响应：

```ts
export interface ApiResponse<T> {
  code: number | string;
  message: string;
  data: T;
  traceId?: string;
  timestamp?: string;
}
```

过渡期如果部分接口直接返回对象或数组，必须在 `http.ts` 做兼容转换，页面层仍然只拿 `data`。

### 5.2 统一请求函数

```ts
export async function request<T>(config: RequestConfig): Promise<T> {
  // 1. 拼接 baseURL
  // 2. 注入 token
  // 3. 处理超时
  // 4. 解析 ApiResponse<T>
  // 5. 统一抛出业务错误
  // 6. 返回 data
}
```

页面禁止直接处理 HTTP 状态码；页面只处理业务动作是否成功、失败后展示什么。

### 5.3 Token 规则

| 场景 | 处理 |
|---|---|
| 未登录 | 跳转 `/login` |
| token 存在 | 请求头带 `Authorization: Bearer <token>` |
| token 过期 | 清空会话，跳转 `/login` |
| 后端未启用登录 | 开发环境使用 `dev-token`，生产环境不得使用假 token |

### 5.4 OpenAPI 同步

每次后端更新接口后，前端必须同步 `https://wpengu.top/openapi.json`：

```bash
npm run openapi:update
npm run typecheck
```

没有自动生成脚本时，至少要手动更新 `src/api/types.ts` 和 `src/api/modules/*` 的字段定义。

## 6. 状态码处理

### 6.1 HTTP 状态码

| HTTP 状态码 | 前端处理 |
|---|---|
| 200 | 正常解析响应 |
| 201 | 创建成功，按成功处理 |
| 204 | 无返回体，按成功处理 |
| 400 | 弹出错误信息，保留当前页面 |
| 401 | 清空登录态，跳转 `/login` |
| 403 | 跳转 `/403` 或显示无权限态 |
| 404 | 详情页显示不存在，列表页显示空态 |
| 409 | 弹出冲突提示，刷新当前数据 |
| 422 | 表单校验错误，字段级提示优先 |
| 429 | 弹出操作过快提示，禁用按钮 3 秒 |
| 500 | 显示系统异常，记录 traceId |
| 502 | 显示后端网关异常 |
| 503 | 显示服务暂不可用 |
| 504 | 显示请求超时，可重试 |

### 6.2 业务 code

| code | 含义 | 前端处理 |
|---|---|---|
| `0` | 成功 | 返回 `data` |
| `200` | 成功 | 返回 `data` |
| `400` | 参数错误 | 展示 `message` |
| `401` | 未登录 | 跳转 `/login` |
| `403` | 无权限 | 跳转 `/403` |
| `404` | 数据不存在 | 当前区域显示空态 |
| `409` | 状态冲突 | 刷新数据后提示 |
| `422` | 表单校验失败 | 展示字段错误 |
| `500` | 业务异常 | 展示 `message`，记录 `traceId` |

## 7. 字段枚举与 UI 字典

前端统一维护以下枚举，不允许页面内散写颜色和中文文案。

### 7.1 设备状态

| 值 | 中文 | 颜色 | 排序 |
|---|---|---|---|
| `online` | 在线 | green | 1 |
| `offline` | 离线 | gray | 5 |
| `warning` | 预警 | orange | 2 |
| `error` | 故障 | red | 3 |
| `maintenance` | 维护中 | blue | 4 |
| `unknown` | 未知 | gray | 6 |

### 7.2 告警等级

| 值 | 中文 | 颜色 | 默认动作 |
|---|---|---|---|
| `info` | 提示 | blue | 查看 |
| `warning` | 警告 | orange | 确认 |
| `critical` | 严重 | red | 处置 |

### 7.3 事件状态

| 值 | 中文 | 可操作 |
|---|---|---|
| `open` | 未关闭 | 可关闭 |
| `processing` | 处理中 | 可关闭 |
| `closed` | 已关闭 | 只读 |

### 7.4 巡检任务状态

| 值 | 中文 | 按钮 |
|---|---|---|
| `pending` | 待开始 | 开始、取消 |
| `running` | 执行中 | 取消 |
| `completed` | 已完成 | 查看 |
| `cancelled` | 已取消 | 查看 |
| `failed` | 失败 | 查看、重试 |

### 7.5 命令状态

| 值 | 中文 | 前端行为 |
|---|---|---|
| `pending` | 等待执行 | 按钮 loading |
| `running` | 执行中 | 禁止重复提交 |
| `success` | 成功 | 刷新详情 |
| `failed` | 失败 | 展示错误 |
| `timeout` | 超时 | 提供重试 |

## 8. 路由与菜单

### 8.1 路由表

| 路由 | 页面 | 权限 |
|---|---|---|
| `/login` | 登录页 | public |
| `/dashboard` | 综合仪表盘 | dashboard:view |
| `/devices/status` | 设备状态总览 | device:view |
| `/devices` | 设备列表 | device:view |
| `/devices/:deviceId` | 设备详情 | device:view |
| `/alarms` | 告警中心 | alarm:view |
| `/alarms/:alarmId` | 告警详情 | alarm:view |
| `/events` | 事件中心 | event:view |
| `/inspection/tasks` | 巡检任务 | inspection:view |
| `/video/cameras` | 视频监控 | video:view |
| `/video/evidence` | 视频证据 | video:view |
| `/access/doors` | 门禁管理 | access:view |
| `/vehicle/lanes` | 车辆通道 | vehicle:view |
| `/railway` | 铁路联动 | railway:view |
| `/ai/rules` | AI 规则 | ai:manage |
| `/reports` | 报表中心 | report:view |
| `/audit/logs` | 审计日志 | audit:view |
| `/simulator` | 硬件状态模拟器 | simulator:manage |
| `/settings/nacos` | Nacos 配置 | system:manage |
| `/403` | 无权限 | public |
| `/404` | 页面不存在 | public |

### 8.2 菜单分组

| 一级菜单 | 子菜单 |
|---|---|
| 首页 | 综合仪表盘 |
| 设备监控 | 设备状态、设备列表、硬件模拟器 |
| 告警事件 | 告警中心、事件中心 |
| 巡检管理 | 巡检任务 |
| 视频管理 | 视频监控、视频证据 |
| 出入管理 | 门禁管理、车辆通道 |
| 联动控制 | 铁路联动、AI 规则 |
| 数据报表 | 报表中心 |
| 系统管理 | 审计日志、Nacos 配置 |

## 9. 页面落地矩阵

### 9.1 综合仪表盘

| 项 | 内容 |
|---|---|
| 路由 | `/dashboard` |
| API | `GET /api/dashboard/overview`、`GET /api/overview`、`GET /api/areas`、`GET /api/tree-menu` |
| 组件 | 总览指标、区域状态、设备状态分布、告警趋势、最新事件 |
| 交互 | 点击区域进入区域详情；点击告警进入告警详情；自动刷新可开关 |
| 验收 | 断网显示错误态；无数据显示空态；刷新不闪屏 |

### 9.2 设备状态总览

| 项 | 内容 |
|---|---|
| 路由 | `/devices/status` |
| API | `GET /api/device-status/summary`、`GET /api/device-status/records`、`GET /api/device-status/options` |
| 组件 | 状态统计、筛选区、设备状态表格、分页 |
| 筛选 | 区域、设备类型、状态、关键字、时间范围 |
| 操作 | 查看详情、刷新、导出当前筛选条件 |
| 验收 | 状态颜色与枚举一致；分页、筛选、刷新均调用真实 API |

### 9.3 设备列表与详情

| 项 | 内容 |
|---|---|
| 路由 | `/devices`、`/devices/:deviceId` |
| API | `GET /api/devices`、`GET /api/devices/list`、`GET /api/devices/{deviceId}` |
| 列表字段 | 设备编号、设备名称、类型、区域、状态、最后上报时间、操作 |
| 详情字段 | 基础信息、实时状态、最近测点、最近告警、操作记录 |
| 验收 | 设备不存在显示 404 空态；详情返回慢时展示骨架屏 |

### 9.4 硬件状态模拟器

| 项 | 内容 |
|---|---|
| 路由 | `/simulator` |
| API | `GET /api/simulator/summary`、`GET /api/simulator/devices`、`GET /api/simulator/devices/{device_id}`、`POST /api/simulator/tick`、`POST /api/simulator/devices/{device_id}/command` |
| 组件 | 模拟器总览、状态机列表、设备详情、命令面板 |
| 操作 | 手动 tick、发送命令、查看状态流转 |
| 验收 | 不在前端随机生成状态；状态变化只来自 API 返回 |

### 9.5 告警中心

| 项 | 内容 |
|---|---|
| 路由 | `/alarms`、`/alarms/:alarmId` |
| API | `GET /api/alarms`、`GET /api/alarms/{alarmId}`、`POST /api/alarms/{alarmId}/actions`、`GET /api/alerts` |
| 组件 | 告警统计、告警列表、告警详情、处置弹窗 |
| 操作 | 确认、处理、关闭、刷新 |
| 验收 | 处置成功后列表和详情同步刷新；重复提交被禁用 |

### 9.6 报警设备

| 项 | 内容 |
|---|---|
| 路由 | `/alarm-devices` |
| API | `GET /api/alarm-devices`、`POST /api/alarm-devices/{deviceId}/command`、`GET /api/alarm-devices/{deviceId}/records` |
| 组件 | 报警设备列表、命令按钮、历史记录 |
| 验收 | 命令执行中按钮 loading；执行结束刷新记录 |

### 9.7 事件中心

| 项 | 内容 |
|---|---|
| 路由 | `/events` |
| API | `GET /api/events`、`GET /api/events/{eventId}`、`PATCH /api/events/{eventId}/close` |
| 组件 | 事件列表、事件详情、关闭确认 |
| 验收 | 已关闭事件按钮置灰；关闭失败保留原状态 |

### 9.8 巡检任务

| 项 | 内容 |
|---|---|
| 路由 | `/inspection/tasks` |
| API | `GET /api/v1/inspection/tasks`、`GET /api/v1/inspection/list`、`GET /api/v1/inspection/task/{task_id}`、`POST /api/v1/inspection/create-task`、`POST /api/v1/inspection/start-task/{task_id}`、`POST /api/v1/inspection/cancel-task/{task_id}`、`DELETE /api/v1/inspection/tasks/{task_id}` |
| 组件 | 任务列表、创建任务表单、任务详情、状态操作 |
| 表单 | 任务名称、巡检区域、巡检点位、计划时间、负责人 |
| 验收 | 表单校验失败不发请求；创建成功返回列表并刷新 |

### 9.9 视频监控与证据

| 项 | 内容 |
|---|---|
| 路由 | `/video/cameras`、`/video/evidence` |
| API | `GET /api/video/cameras`、`GET /api/video/cameras/{cameraId}/stream-url`、`GET /api/video/recordings`、`GET /api/video/evidence`、`GET /api/video/evidence/{evidenceId}`、`POST /api/video/evidence/export` |
| 组件 | 摄像头列表、播放器、录像列表、证据列表、导出按钮 |
| 验收 | 拉流失败显示错误态；导出中按钮不可重复点击 |

### 9.10 门禁管理

| 项 | 内容 |
|---|---|
| 路由 | `/access/doors` |
| API | `GET /api/access/doors`、`GET /api/access/doors/{doorId}`、`POST /api/access/doors/{doorId}/command`、`GET /api/access/pass-records` |
| 组件 | 门禁列表、门禁详情、开关门命令、通行记录 |
| 验收 | 命令成功后刷新门禁状态；记录列表支持分页 |

### 9.11 车辆通道

| 项 | 内容 |
|---|---|
| 路由 | `/vehicle/lanes` |
| API | `GET /api/vehicle/lanes`、`POST /api/vehicle/lanes/{laneId}/command`、`GET /api/vehicle/pass-records` |
| 组件 | 车道列表、车道控制、车辆通行记录 |
| 验收 | 车道命令执行期间禁止二次点击 |

### 9.12 铁路联动

| 项 | 内容 |
|---|---|
| 路由 | `/railway` |
| API | `GET /api/railway/status`、`POST /api/railway/mode`、`GET /api/railway/linkage-records` |
| 组件 | 联动状态、模式切换、联动记录 |
| 验收 | 模式切换必须二次确认；失败后回滚 UI 状态 |

### 9.13 AI 规则与检测

| 项 | 内容 |
|---|---|
| 路由 | `/ai/rules` |
| API | `GET /api/ai/rules`、`PATCH /api/ai/rules/{ruleId}`、`GET /api/ai/detections` |
| 组件 | 规则列表、启停开关、检测记录 |
| 验收 | 开关失败时恢复原值；规则变更记录到操作日志页面 |

### 9.14 区域与测点

| 项 | 内容 |
|---|---|
| 路由 | `/areas`、`/areas/:areaId`、`/points/:pointId` |
| API | `GET /api/areas`、`GET /api/area/{area_id}`、`GET /api/areas/{areaId}/summary`、`GET /api/latest-measurements`、`GET /api/point/{point_id}/latest-measurement`、`GET /api/point/{point_id}/history-measurements`、`GET /api/premade-point/{premade_point_id}/latest-image` |
| 组件 | 区域树、区域详情、测点卡片、历史曲线、最新图片 |
| 验收 | 曲线空数据不报错；图片加载失败显示占位 |

### 9.15 报表中心

| 项 | 内容 |
|---|---|
| 路由 | `/reports` |
| API | `GET /api/reports/alarm-statistics`、`GET /api/reports/device-status`、`GET /api/reports/pass-statistics`、`GET /api/reports/vehicle-statistics`、`POST /api/reports/export` |
| 组件 | 报表筛选、统计图、报表表格、导出任务 |
| 验收 | 导出携带当前筛选条件；导出失败显示原因 |

### 9.16 审计日志

| 项 | 内容 |
|---|---|
| 路由 | `/audit/logs` |
| API | `GET /api/audit/logs` |
| 组件 | 操作日志表、筛选、详情抽屉 |
| 验收 | 关键操作能在日志中查询到 |

### 9.17 系统配置

| 项 | 内容 |
|---|---|
| 路由 | `/settings/nacos` |
| API | `GET /api/nacos/config`、`POST /api/nacos/config` |
| 组件 | 配置查看、配置编辑、保存确认 |
| 验收 | 只有 `system:manage` 权限可访问；保存失败不覆盖本地表单 |

## 10. 表格规范

所有列表页必须具备：

| 功能 | 要求 |
|---|---|
| loading | 首次加载和刷新时展示 |
| empty | 接口成功但无数据时展示 |
| error | 接口失败时展示重试按钮 |
| pagination | 后端分页优先；无分页接口时前端只做展示分页 |
| filter | 筛选条件变化后重置到第一页 |
| refresh | 刷新保留当前筛选条件 |
| columns | 操作列固定在右侧 |
| row key | 使用后端唯一 id，不使用数组下标 |

## 11. 表单规范

| 项 | 要求 |
|---|---|
| 必填校验 | 前端先校验，后端再校验 |
| 提交态 | 提交期间按钮 loading 并禁用 |
| 成功 | 显示成功提示，刷新关联数据 |
| 失败 | 展示后端 `message` |
| 取消 | 有未保存改动时二次确认 |
| 时间字段 | 提交 ISO 字符串或后端约定格式，展示统一格式 |

## 12. 权限规则

### 12.1 角色

| 角色 | 说明 |
|---|---|
| `admin` | 全部权限 |
| `operator` | 查看和操作设备、告警、巡检 |
| `viewer` | 只读查看 |
| `auditor` | 查看审计和报表 |

### 12.2 权限点

| 权限 | 控制范围 |
|---|---|
| `dashboard:view` | 仪表盘 |
| `device:view` | 设备查看 |
| `device:command` | 设备命令 |
| `alarm:view` | 告警查看 |
| `alarm:handle` | 告警处置 |
| `event:view` | 事件查看 |
| `event:close` | 事件关闭 |
| `inspection:view` | 巡检查看 |
| `inspection:manage` | 巡检创建、开始、取消、删除 |
| `video:view` | 视频查看 |
| `video:export` | 视频证据导出 |
| `access:view` | 门禁查看 |
| `access:command` | 门禁控制 |
| `vehicle:view` | 车辆通道查看 |
| `vehicle:command` | 车道控制 |
| `railway:view` | 铁路联动查看 |
| `railway:manage` | 模式切换 |
| `ai:manage` | AI 规则管理 |
| `report:view` | 报表查看 |
| `report:export` | 报表导出 |
| `audit:view` | 审计日志 |
| `simulator:manage` | 模拟器操作 |
| `system:manage` | 系统配置 |

按钮权限必须在组件层控制，接口权限失败时仍按 `403` 处理。

## 13. 前后端联调流程

每个页面按以下流程联调：

1. 从 `https://wpengu.top/openapi.json` 确认接口路径、参数、返回字段。
2. 在 `src/api/modules/*` 新增或更新接口函数。
3. 在页面接入 loading、empty、error 三态。
4. 使用真实后端接口调通列表。
5. 调通详情。
6. 调通新增、修改、命令、关闭、导出等写操作。
7. 验证 400、401、403、404、422、500 的展示。
8. 记录字段缺失、接口缺失、枚举不一致问题。
9. 修复后执行 `lint`、`typecheck`、`build`。

## 14. 任务拆分

### 14.1 基础工程

| 任务编号 | 任务 | 输出 |
|---|---|---|
| FE-001 | 整理前端启动脚本 | `dev`、`build`、`lint`、`typecheck` 可执行 |
| FE-002 | 建立环境变量 | `.env.example`、开发环境配置 |
| FE-003 | 建立代理 | `/api` 转发后端 |
| FE-004 | 建立 API client | `src/api/http.ts` |
| FE-005 | 建立错误处理 | `src/api/error.ts` |
| FE-006 | 建立枚举字典 | `src/constants/enums.ts` |
| FE-007 | 建立权限配置 | `src/constants/permissions.ts` |
| FE-008 | 建立路由配置 | `src/constants/routes.ts` |

### 14.2 页面模块

| 任务编号 | 任务 | 路由 |
|---|---|---|
| FE-101 | 综合仪表盘 | `/dashboard` |
| FE-102 | 设备状态总览 | `/devices/status` |
| FE-103 | 设备列表与详情 | `/devices`、`/devices/:deviceId` |
| FE-104 | 硬件状态模拟器 | `/simulator` |
| FE-105 | 告警中心 | `/alarms` |
| FE-106 | 报警设备 | `/alarm-devices` |
| FE-107 | 事件中心 | `/events` |
| FE-108 | 巡检任务 | `/inspection/tasks` |
| FE-109 | 视频监控 | `/video/cameras` |
| FE-110 | 视频证据 | `/video/evidence` |
| FE-111 | 门禁管理 | `/access/doors` |
| FE-112 | 车辆通道 | `/vehicle/lanes` |
| FE-113 | 铁路联动 | `/railway` |
| FE-114 | AI 规则 | `/ai/rules` |
| FE-115 | 区域与测点 | `/areas`、`/points/:pointId` |
| FE-116 | 报表中心 | `/reports` |
| FE-117 | 审计日志 | `/audit/logs` |
| FE-118 | Nacos 配置 | `/settings/nacos` |

### 14.3 联调与发布

| 任务编号 | 任务 | 输出 |
|---|---|---|
| FE-201 | 全量接口冒烟 | 每个模块至少一次成功请求 |
| FE-202 | 异常状态冒烟 | 401、403、404、422、500 展示正确 |
| FE-203 | 权限冒烟 | 不同角色菜单和按钮正确 |
| FE-204 | 构建检查 | `npm run build` 通过 |
| FE-205 | 发布 8083 | 线上入口访问正常 |
| FE-206 | 回归记录 | 输出联调问题表和已修复表 |

## 15. 验收清单

前端提交前必须逐项确认：

| 检查项 | 必须结果 |
|---|---|
| 页面内无硬编码后端地址 | 通过 |
| 页面内无直接 mock 业务数据 | 通过 |
| 所有请求走 API 模块 | 通过 |
| 所有状态值走枚举字典 | 通过 |
| 列表具备 loading、empty、error | 通过 |
| 详情具备不存在状态 | 通过 |
| 表单具备提交 loading | 通过 |
| 命令按钮防重复提交 | 通过 |
| 401 可跳登录 | 通过 |
| 403 可显示无权限 | 通过 |
| OpenAPI 字段已同步 | 通过 |
| `lint` 通过 | 通过 |
| `typecheck` 通过 | 通过 |
| `build` 通过 | 通过 |
| 8083 线上可访问 | 通过 |

## 16. 交付文件

前端开发完成后必须提交以下内容：

| 文件或目录 | 内容 |
|---|---|
| `.env.example` | 环境变量说明 |
| `src/api/` | 全量 API 封装 |
| `src/constants/` | 枚举、权限、路由 |
| `src/pages/` | 全量页面 |
| `src/components/` | 公共组件 |
| `src/mock/` | 仅开发使用的 mock |
| `README.md` | 启动、构建、发布说明 |
| `CHANGELOG.md` | 本轮前端变更记录 |
| `联调问题表` | 接口缺失、字段缺失、枚举不一致记录 |

## 17. 与后端文档的对应关系

| 前端工作 | 对应文档 |
|---|---|
| API 字段和路径 | [完整 API 文档](./complete-api-doc) |
| 当前已落地接口 | [后端现阶段 API 落地文档](./backend-current-api) |
| 后端开发任务 | [后端全量 API 落地任务书](./backend-full-landing-task-book) |
| 8082/8083 对接契约 | [8082/8083 API 契约](./team-api-contract) |
| 硬件模拟器 | [硬件状态机模拟器](./hardware-state-machine-simulator) |
| 在线交互式接口 | [Scalar OpenAPI](/openapi) |
