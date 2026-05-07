# 8083 设备状态控件数据交互文档（实现对齐版）

## 1. 适用范围

本文件针对当前 `8083` 大屏前端中的“设备状态”控件，描述的是已经在本仓库落地的接口能力。

截至 `2026-04-22`，已实现接口为：

- `GET /api/device-status/options`
- `GET /api/device-status/records`

默认情况下，后端使用内置演示数据；`records` 接口在传入 `dataId` 时，也支持从 Nacos 配置读取。

## 2. 当前前端实现现状

从 `8083` 打包代码可见，控件核心输入结构是：

- `records`: `[{ region, device, online, offline }]`
- `regions`: `string[]`
- `devices`: `string[]`

当前组件筛选逻辑为：

- 区域默认值：`全部`
- 设备默认值：`全部`
- 区域筛选：`record.region === selectedRegion || selectedRegion === "全部"`
- 设备筛选：`record.device === selectedDevice || selectedDevice === "全部"`

常用聚合指标为：

- `online = sum(records.online)`
- `offline = sum(records.offline)`
- `total = online + offline`
- `rate = total > 0 ? (online / total * 100).toFixed(1) : "0.0"`

## 3. 已实现接口契约

### 3.1 获取筛选项

- 方法：`GET`
- 路径：`/api/device-status/options`

#### Query

- `region`：可选，默认 `全部`
- `regionId`：可选，`region` 的兼容别名

#### 响应示例

```json
{
  "regions": ["全部", "A区", "F区", "L区", "成品库", "火车道", "道路", "厂房", "作业区"],
  "devices": ["全部", "人员智能门/联锁门", "摄像机", "车辆识别与道闸"]
}
```

#### 实现说明

- 当前接口基于后端内置演示数据生成筛选项
- 传入具体区域时，`devices` 只返回该区域下存在的设备
- 当前接口不支持通过 `dataId` 切换到 Nacos 配置源

### 3.2 获取设备状态记录

- 方法：`GET`
- 路径：`/api/device-status/records`

#### Query

- `region`：可选，默认 `全部`
- `regionId`：可选，`region` 的兼容别名
- `device`：可选，默认 `全部`
- `deviceType`：可选，`device` 的兼容别名
- `dataId`：可选，默认空；为空时返回内置演示数据
- `group`：可选，默认 `DEFAULT_GROUP`
- `tenant`：可选，Nacos namespaceId
- `field`：可选，默认 `deviceStatus.records`

#### 响应示例

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
  "updatedAt": "2026-04-22T18:00:00+08:00"
}
```

#### 数据源说明

- `dataId` 为空：返回后端内置演示数据
- `dataId` 非空：从 Nacos 读取配置，再按 `field` 提取数据
- 默认 `field` 为 `deviceStatus.records`

支持以下 `3` 种配置结构：

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

#### 字段校验

- `region`、`device` 必须为非空字符串
- `online`、`offline` 必须为非负整数
- 如果筛选值不存在，接口返回 `400`

## 4. 当前限制和同步说明

这部分需要前后端都知道：

- `records` 接口支持从 Nacos 读取
- `options` 接口当前仍然只基于后端内置演示数据

也就是说，如果前端把 `records` 指到某个自定义 `dataId`，而该配置里的区域或设备集合与演示数据不同，当前 `options` 接口不会自动跟着变化。

现阶段有两种处理方式：

1. 联调时优先使用默认演示数据源，保持 `options` 和 `records` 一致
2. 如果必须用自定义 `dataId`，前端自行从 `records` 派生筛选项，或后续补做 `options` 的配置源扩展

## 5. 前端接入顺序

### 5.1 页面初始化

1. 调 `GET /api/device-status/options`
2. 调 `GET /api/device-status/records?region=全部&device=全部`
3. 将返回结果绑定给 `regions`、`devices`、`records`

### 5.2 切换区域

1. 调 `GET /api/device-status/options?region=<selectedRegion>`
2. 调 `GET /api/device-status/records?region=<selectedRegion>&device=全部`

### 5.3 切换设备

1. 调 `GET /api/device-status/records?region=<selectedRegion>&device=<selectedDevice>`

### 5.4 自动刷新

- 建议每 `30s` 刷新一次 `records`
- 页面离开时清理定时器

## 6. 错误处理约定

- `200`：成功
- `400`：筛选值非法，例如未知 `region` 或 `device`
- `404`：Nacos 字段或配置不存在
- `422`：配置结构非法，或 `online/offline` 不是非负整数
- `500/502`：后端异常或 Nacos 访问异常

前端建议：

- 请求失败时保留上一次成功数据
- 做轻量提示，不要直接清空页面

## 7. 联调验收标准

1. 区域/设备切换后，环图、在线/离线/总数实时变化
2. `全部` 筛选逻辑正确
3. `onlineRate` 保留 `1` 位小数
4. 后端接口失败时页面不崩溃
5. 刷新周期可配置，默认 `30` 秒

## 8. 参考请求示例

```bash
# 1) 筛选项
curl "http://101.43.49.78:8000/api/device-status/options"

# 2) 记录（全部）
curl "http://101.43.49.78:8000/api/device-status/records?region=全部&device=全部"

# 3) 记录（指定）
curl "http://101.43.49.78:8000/api/device-status/records?region=A区&device=人员智能门/联锁门"
```
