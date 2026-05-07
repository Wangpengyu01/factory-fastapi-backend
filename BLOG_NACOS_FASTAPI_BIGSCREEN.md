# 大屏业务接口范围说明（方案稿）

## 1. 文档定位

这份文档描述的是“大屏业务接口”的范围和汇报口径，不是当前仓库 `backend/app/main.py` 已落地的路由清单。

截至 `2026-04-22`，当前仓库真正已经实现的只有下面 `5` 个接口：

1. `GET /api/health`
2. `GET /api/nacos/config`
3. `POST /api/nacos/config`
4. `GET /api/device-status/options`
5. `GET /api/device-status/records`

本文后面提到的树菜单、测点详情、预制点图片、消息轮询、任务管理、首页概览等，属于业务侧接口范围稿或待对齐接口，不在这个 FastAPI 仓库里直接落地。

## 2. 为什么会有这份文档

原因是当前项目里同时存在两类资料：

- 当前仓库的真实接口文档：围绕 `health`、`nacos-config`、`device-status`
- 外部大屏业务接口方案文档：围绕树、测点、螺栓、开距、任务、概览

如果开会时不把这两类资料拆开，很容易把“文档里有”误说成“这个仓库里已经有实现”。

## 3. 业务接口范围怎么讲

下面这组接口，是业务侧大屏交互里会涉及到的接口范围。  
如果对应业务后端已经存在，可以按这个清单去对齐；如果还没实现，就把它当成方案稿或待落地清单。

### 3.1 树与详情

- `GET /api/tree-menu`
- `GET /api/point/{point_id}/latest-measurement`
- `GET /api/point/{point_id}/history-measurements`
- `GET /api/premade-point/{premade_point_id}/latest-image`

### 3.2 消息轮询

- `GET /api/latest-measurements`

### 3.3 任务管理

- `GET /api/v1/inspection/list`
- `POST /api/v1/inspection/create-task`
- `POST /api/v1/inspection/start-task/{task_id}`
- `GET /api/v1/inspection/tasks`
- `GET /api/v1/inspection/task/{task_id}`
- `POST /api/v1/inspection/cancel-task/{task_id}`
- `DELETE /api/v1/inspection/tasks/{task_id}`

### 3.4 首页概览

建议单独整理为：

```http
GET /api/dashboard/overview
```

这一组字段和树、点位详情、任务管理不是一类职责，建议单独讲、单独接。

## 4. 最关键的 ID 规则

这部分是业务侧文档里最容易讲错的地方。

树节点 `id` 不一定等于后端业务提交 ID。

- 综合检测：传 `premade_point_id`
- 开距检测：传原始 `point_id`
- 螺栓检测：传原始 `point_id`

不要直接把下面这种树节点 ID 提交给后端：

- `opening_xxx`
- `screw_xxx`

树展示阶段可以继续使用节点 `id`；真正发业务请求时，要回到节点上的 `point_id` 或 `premade_point_id`。

## 5. 螺栓和开距为什么会出现在文档里

因为这份文档服务的是业务侧大屏方案，而业务模型本身就把检测类型拆成：

- 综合检测
- 开距检测
- 螺栓检测

所以才会有：

- `opening_point`
- `screw_point`
- `selected_points`
- `raw_data`
- `coordinates`

这些业务字段不是当前 Nacos FastAPI 配置桥自身需要的能力，而是业务大屏领域模型的一部分。

## 6. 汇报时怎么拆

最稳的汇报方式是拆成两部分。

### 6.1 第一部分：当前仓库已实现

只讲这 `5` 个接口：

- `GET /api/health`
- `GET /api/nacos/config`
- `POST /api/nacos/config`
- `GET /api/device-status/options`
- `GET /api/device-status/records`

### 6.2 第二部分：业务接口范围稿

再单独说：

- 树菜单
- 测点最新值
- 历史值
- 预制点最新图片
- 消息轮询
- 任务创建与管理
- 首页概览接口

并明确说明：

- 这一组是业务接口方案或外部系统接口口径
- 不等于当前仓库已经实现的 FastAPI 路由

## 7. 统一包装也要单独讲清楚

业务接口方案文档里通常约定：

- 先判断 `response.data.success`
- 真正业务数据在 `response.data.data`

但当前这个 FastAPI 仓库不是这套包装，而是直接返回裸 JSON 模型。

所以汇报时不要把两套响应结构混在一起讲。

## 8. 一句话结论

这份文档是“大屏业务接口范围稿”，核心作用是帮助汇报和划边界；真正当前仓库已落地的接口能力，请以 `API_DOC.md` 和 `backend/openapi.json` 为准。
