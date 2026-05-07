# 项目 API 总说明

本文档面向两类使用者：

- 后端：作为 `FastAPI` 路由、`Pydantic` 模型、`OpenAPI` 导出的对照说明
- 前端：作为接口联调和数据结构接入说明

当前项目已实现并可直接使用的接口共 5 个：

1. `GET /api/health`
2. `GET /api/nacos/config`
3. `POST /api/nacos/config`
4. `GET /api/device-status/options`
5. `GET /api/device-status/records`

## 0. 文档边界

截至 `2026-04-22`，本文档只描述 `backend/app/main.py` 中已经实现的 FastAPI 路由。

- `BLOG_NACOS_FASTAPI_BIGSCREEN.md`：大屏业务接口范围稿，不代表当前仓库已实现
- `DASHBOARD_OVERVIEW_API_DOC.md`：首页概览接口方案稿，不在当前 FastAPI 路由内
- 当前 FastAPI 实现返回的是裸 JSON 模型，不使用统一的 `success/message/data` 包装

## 1. 项目结构与职责

### 1.1 backend

- 技术栈：`FastAPI + Pydantic + httpx`
- 作用：作为 Nacos 配置桥，并提供 `8083` 设备状态控件的联调接口
- Swagger 地址：`/docs`
- ReDoc 地址：`/redoc`
- OpenAPI 文件：`backend/openapi.json`

### 1.2 frontend

- 技术栈：静态页面 + `Nginx` 反向代理
- 作用：演示前端如何直接调用本项目 API
- 代理规则：前端请求 `/api/*` 时，由 `Nginx` 转发到后端 FastAPI

## 2. 通用约定

### 2.1 Base URL

- 本地开发后端：`http://localhost:8000`
- 前端页面内调用：直接使用相对路径 `/api/...`

### 2.2 数据格式

- 请求体：`application/json`
- 响应体：`application/json`
- 当前实现直接返回裸 JSON；错误详情通常位于 `detail`
- 时间字段：ISO-8601 字符串，当前实现使用 `+08:00`
- 字段命名：接口出参统一使用前端友好的 `camelCase`

### 2.3 错误码约定

- `200`：请求成功
- `400`：业务参数非法，例如未知 `region` 或 `device`
- `401`：发布配置时 `X-Publish-Key` 错误
- `404`：指定配置或字段不存在
- `422`：请求格式错误，或配置内容结构不符合约定
- `502`：后端访问 Nacos 失败或 Nacos 返回异常
- `503`：服务端未配置发布密钥

前端建议：

- 请求失败时保留上一次成功数据
- 对用户展示轻量错误提示，不要让页面直接白屏

## 3. FastAPI 模型映射

后端核心模型位于 `backend/app/main.py`：

- `HealthResponse`
- `ConfigItem`
- `ConfigReadResponse`
- `PublishConfigBody`
- `PublishConfigResponse`
- `DeviceStatusRecord`
- `DeviceStatusOptionsResponse`
- `DeviceStatusRecordsResponse`

前端如果使用 TypeScript，建议与这些响应结构保持一一对应。

## 4. 接口清单

### 4.1 健康检查

- 方法：`GET`
- 路径：`/api/health`
- 用途：探活、部署校验、负载均衡健康检查

响应示例：

```json
{
  "status": "ok"
}
```

前端用途：

- 页面初始化前做一次服务可用性检查
- 演示环境中用于确认接口服务已经在线

---

### 4.2 读取 Nacos 配置

- 方法：`GET`
- 路径：`/api/nacos/config`
- 用途：读取单个配置，或在 `dataId` 留空时读取配置列表

#### Query 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| `dataId` | `string` | 否 | `""` | 配置 ID；留空表示读取全量列表 |
| `group` | `string` | 否 | `DEFAULT_GROUP` | Nacos 分组 |
| `tenant` | `string` | 否 | `null` | Nacos namespaceId |
| `field` | `string` | 否 | `null` | JSON/YAML 点路径，如 `deviceStatus.records` |
| `pageNo` | `number` | 否 | `1` | 仅全量模式有效 |
| `pageSize` | `number` | 否 | `200` | 仅全量模式有效，最大 `1000` |

#### 单配置读取示例

请求：

```http
GET /api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP&field=deviceStatus.refreshSeconds
```

响应：

```json
{
  "mode": "single",
  "dataId": "device-status.json",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "field": "deviceStatus.refreshSeconds",
  "content": "{\"deviceStatus\":{\"refreshSeconds\":30}}",
  "parsed": {
    "deviceStatus": {
      "refreshSeconds": 30
    }
  },
  "value": 30,
  "total": null,
  "items": null,
  "mergedParams": null
}
```

#### 全量读取示例

请求：

```http
GET /api/nacos/config?dataId=&group=DEFAULT_GROUP&pageNo=1&pageSize=200
```

响应：

```json
{
  "mode": "all",
  "dataId": null,
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "field": null,
  "content": null,
  "parsed": null,
  "value": null,
  "total": 2,
  "items": [
    {
      "dataId": "device-status.json",
      "group": "DEFAULT_GROUP",
      "tenant": null,
      "content": "{\"deviceStatus\":{\"refreshSeconds\":30}}",
      "parsed": {
        "deviceStatus": {
          "refreshSeconds": 30
        }
      },
      "value": null
    }
  ],
  "mergedParams": {
    "deviceStatus": {
      "refreshSeconds": 30
    }
  }
}
```

后端说明：

- `dataId` 非空时，后端调用 Nacos 单配置读取接口
- `field` 非空时，会尝试将配置按 `JSON/YAML` 解析后取字段值
- `dataId` 为空时，后端进入全量列表模式，并返回 `items` 和 `mergedParams`

前端说明：

- 配置编辑页直接调用此接口即可，不需要前端自己对接 Nacos 原生 API
- 若只是读一个配置文件原文，使用 `mode=single`
- 若要做配置概览页，使用 `mode=all`

---

### 4.3 发布 Nacos 配置

- 方法：`POST`
- 路径：`/api/nacos/config`
- 用途：将配置内容发布到 Nacos
- Header：`X-Publish-Key`

#### Header

| 参数名 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `X-Publish-Key` | `string` | 是 | 服务端发布密钥 |

#### Body

| 字段名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| `dataId` | `string` | 是 | - | 配置 ID |
| `group` | `string` | 否 | `DEFAULT_GROUP` | Nacos 分组 |
| `tenant` | `string \| null` | 否 | `null` | namespaceId |
| `type` | `string` | 否 | `text` | 配置类型，建议 `json` 或 `yaml` |
| `content` | `string` | 是 | - | 配置内容 |

请求示例：

```json
{
  "dataId": "device-status.json",
  "group": "DEFAULT_GROUP",
  "tenant": null,
  "type": "json",
  "content": "{\"deviceStatus\":{\"refreshSeconds\":30}}"
}
```

成功响应：

```json
{
  "success": true,
  "message": "Config published to Nacos"
}
```

后端说明：

- 发布前会校验 `X-Publish-Key`
- 若服务端未配置 `PUBLISH_API_KEY`，返回 `503`
- 实际发布时由 FastAPI 代发到 Nacos `/v1/cs/configs`

前端说明：

- 发布接口只建议用于内部页面或受控运维工具
- 公共大屏不要直接暴露发布能力

---

### 4.4 获取设备状态筛选项

- 方法：`GET`
- 路径：`/api/device-status/options`
- 用途：返回 `8083` 设备状态控件可用的区域和设备下拉选项

#### Query 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| `region` | `string` | 否 | `全部` | 当前选择区域 |
| `regionId` | `string` | 否 | `null` | `region` 的兼容别名 |

响应示例：

```json
{
  "regions": ["全部", "A区", "F区", "L区", "成品库", "火车道", "道路", "厂房", "作业区"],
  "devices": ["全部", "人员智能门/联锁门", "摄像机", "车辆识别与道闸"]
}
```

后端说明：

- 当前基于演示数据生成筛选项
- 若传具体区域，`devices` 仅返回该区域下存在的设备类型

前端说明：

- 页面初始化先调一次
- 切换区域后再调一次，以刷新设备下拉项

---

### 4.5 获取设备状态记录

- 方法：`GET`
- 路径：`/api/device-status/records`
- 用途：返回 `8083` 设备状态控件的明细记录

#### Query 参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---:|---|---|
| `region` | `string` | 否 | `全部` | 区域筛选 |
| `regionId` | `string` | 否 | `null` | `region` 兼容别名 |
| `device` | `string` | 否 | `全部` | 设备筛选 |
| `deviceType` | `string` | 否 | `null` | `device` 兼容别名 |
| `dataId` | `string` | 否 | `""` | 指定从 Nacos 读取设备状态配置 |
| `group` | `string` | 否 | `DEFAULT_GROUP` | Nacos 分组 |
| `tenant` | `string` | 否 | `null` | namespaceId |
| `field` | `string` | 否 | `deviceStatus.records` | 指定从配置中取哪段数据 |

响应示例：

```json
{
  "records": [
    {
      "region": "A区",
      "device": "人员智能门/联锁门",
      "online": 120,
      "offline": 12
    },
    {
      "region": "A区",
      "device": "摄像机",
      "online": 86,
      "offline": 6
    }
  ],
  "updatedAt": "2026-04-16T10:00:00+08:00"
}
```

后端说明：

- `dataId` 为空时，返回后端内置 mock 数据
- `dataId` 非空时，后端从 Nacos 读取并解析配置
- 支持以下 3 种配置结构：

```json
[
  { "region": "A区", "device": "摄像机", "online": 1, "offline": 0 }
]
```

```json
{
  "records": [
    { "region": "A区", "device": "摄像机", "online": 1, "offline": 0 }
  ]
}
```

```json
{
  "deviceStatus": {
    "records": [
      { "region": "A区", "device": "摄像机", "online": 1, "offline": 0 }
    ]
  }
}
```

前端说明：

- 返回的始终是 `records` 数组，前端可以最小改动接入
- 推荐前端自行统计：
  - `online = sum(records.online)`
  - `offline = sum(records.offline)`
  - `total = online + offline`
  - `onlineRate = total === 0 ? 0 : Number(((online / total) * 100).toFixed(1))`

## 5. 设备状态控件联调时序

### 5.1 页面初始化

1. 调 `GET /api/device-status/options`
2. 调 `GET /api/device-status/records?region=全部&device=全部`
3. 将返回结果绑定到前端的 `regions`、`devices`、`records`

### 5.2 切换区域

1. 调 `GET /api/device-status/options?region=<selectedRegion>`
2. 调 `GET /api/device-status/records?region=<selectedRegion>&device=全部`

### 5.3 切换设备

1. 调 `GET /api/device-status/records?region=<selectedRegion>&device=<selectedDevice>`

### 5.4 自动刷新

- 建议每 `30s` 刷新一次 `records`
- 页面卸载时清理定时器

### 5.5 当前限制

- `GET /api/device-status/options` 当前只基于后端内置演示数据生成筛选项
- `GET /api/device-status/records` 支持通过 `dataId` 改为读取 Nacos 配置
- 如果 `records` 使用了自定义 `dataId`，而该配置中的区域/设备集合和演示数据不一致，当前 `options` 接口不会自动跟随变化
- 这种场景下，建议前端从 `records` 自行派生筛选项，或后续扩展 `options` 接口的数据源能力

## 6. 前端 TypeScript 类型建议

```ts
export interface HealthResponse {
  status: string;
}

export interface ConfigItem {
  dataId: string;
  group: string;
  tenant: string | null;
  content: string;
  parsed: unknown | null;
  value: unknown | null;
}

export interface ConfigReadResponse {
  mode: "single" | "all";
  dataId: string | null;
  group: string | null;
  tenant: string | null;
  field: string | null;
  content: string | null;
  parsed: unknown | null;
  value: unknown | null;
  total: number | null;
  items: ConfigItem[] | null;
  mergedParams: Record<string, unknown> | null;
}

export interface PublishConfigBody {
  dataId: string;
  group?: string;
  tenant?: string | null;
  type?: string;
  content: string;
}

export interface PublishConfigResponse {
  success: boolean;
  message: string;
}

export interface DeviceStatusRecord {
  region: string;
  device: string;
  online: number;
  offline: number;
}

export interface DeviceStatusOptionsResponse {
  regions: string[];
  devices: string[];
}

export interface DeviceStatusRecordsResponse {
  records: DeviceStatusRecord[];
  updatedAt: string;
}
```

## 7. 前端调用示例

```ts
const API_BASE = "";

export async function getHealth() {
  const resp = await fetch(`${API_BASE}/api/health`);
  const data = await resp.json();
  if (!resp.ok) throw new Error("health check failed");
  return data;
}

export async function readNacosConfig(params: {
  dataId?: string;
  group?: string;
  tenant?: string;
  field?: string;
  pageNo?: number;
  pageSize?: number;
}) {
  const query = new URLSearchParams({
    dataId: params.dataId ?? "",
    group: params.group ?? "DEFAULT_GROUP",
    pageNo: String(params.pageNo ?? 1),
    pageSize: String(params.pageSize ?? 200),
  });
  if (params.tenant) query.set("tenant", params.tenant);
  if (params.field) query.set("field", params.field);

  const resp = await fetch(`${API_BASE}/api/nacos/config?${query.toString()}`);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.detail || "读取配置失败");
  return data;
}

export async function publishNacosConfig(
  body: PublishConfigBody,
  publishKey: string
) {
  const resp = await fetch(`${API_BASE}/api/nacos/config`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Publish-Key": publishKey,
    },
    body: JSON.stringify({
      group: "DEFAULT_GROUP",
      type: "json",
      ...body,
    }),
  });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.detail || "发布配置失败");
  return data;
}

export async function getDeviceStatusOptions(region = "全部") {
  const query = new URLSearchParams({ region });
  const resp = await fetch(`${API_BASE}/api/device-status/options?${query.toString()}`);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.detail || "获取筛选项失败");
  return data;
}

export async function getDeviceStatusRecords(params: {
  region?: string;
  device?: string;
  dataId?: string;
  group?: string;
  tenant?: string;
  field?: string;
}) {
  const query = new URLSearchParams({
    region: params.region ?? "全部",
    device: params.device ?? "全部",
    dataId: params.dataId ?? "",
    group: params.group ?? "DEFAULT_GROUP",
    field: params.field ?? "deviceStatus.records",
  });
  if (params.tenant) query.set("tenant", params.tenant);

  const resp = await fetch(`${API_BASE}/api/device-status/records?${query.toString()}`);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data?.detail || "获取设备状态失败");
  return data;
}
```

## 8. 后端维护说明

### 8.1 变更接口后要做的事

1. 修改 `backend/app/main.py`
2. 重新导出 OpenAPI 文件
3. 同步更新本文档中的示例和字段说明

### 8.2 OpenAPI 导出命令

```powershell
cd backend
python .\scripts\generate_openapi.py
```

## 9. 当前范围说明

本文档描述的是当前项目已经实现的接口。  
如果后续需要新增“园区概览”“在线门禁”“车辆在场”“火车道状态”等聚合接口，建议新增独立路由，例如：

- `GET /api/dashboard/overview`

这样可以和当前的 `nacos-config`、`device-status` 责任边界保持清晰。  
在它真正落地到代码和 OpenAPI 之前，应继续把它视为方案稿，而不是已实现接口。
