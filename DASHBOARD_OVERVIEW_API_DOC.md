# 首页概览接口协议（方案稿）

## 1. 文档定位

本文档描述的是首页概览接口方案，不是当前仓库已经实现的 FastAPI 路由。

截至 `2026-04-22`：

- 当前仓库已实现接口见 `API_DOC.md`
- `GET /api/dashboard/overview` 仍属于建议新增接口
- 该接口不在当前 `backend/openapi.json` 中

## 2. 适用场景

如果首页需要一次性拉取概览卡片、筛选器和图表公共数据，适合单独提供一个聚合接口，而不是把这些字段塞进已有的详情接口里。

适合放进这个接口的数据包括：

- 在线门禁数
- 区域总数
- 在场车辆数
- 铁轨状态
- 设备记录列表
- 设备区域筛选项
- 设备类型筛选项

## 3. 推荐路径

```http
GET /api/dashboard/overview
```

## 4. 返回结构建议

如果这个接口属于业务侧大屏后端，可以继续沿用业务侧统一包装：

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "onlineAccess": 12,
    "areaTotal": 8,
    "vehiclesOnSite": 23,
    "railStatus": "normal",
    "deviceRegions": ["全部", "A区", "B区", "作业区"],
    "deviceTypes": ["全部", "摄像头", "智能门禁", "车辆识别"],
    "deviceRecords": [
      {
        "region": "A区",
        "deviceType": "摄像头",
        "online": 18,
        "offline": 2,
        "total": 20
      }
    ]
  }
}
```

如果未来决定把它落到当前这个 FastAPI 仓库里，就需要先统一一件事：

- 是继续沿用业务侧 `success/message/data` 包装
- 还是和当前 FastAPI 一样，直接返回裸 JSON 响应模型

在没有做出这个决定前，这份文档只能视为协议方案，不应当写成“已实现”。

## 5. 字段说明

### 5.1 顶部概览卡片

- `onlineAccess`：在线门禁数量
- `areaTotal`：区域总数
- `vehiclesOnSite`：当前在场车辆数
- `railStatus`：铁轨状态，建议返回稳定枚举值或稳定文案

### 5.2 筛选字段

- `deviceRegions`：设备区域筛选列表
- `deviceTypes`：设备类型筛选列表

建议都包含一个“全部”选项，减少前端额外拼装逻辑。

### 5.3 图表与表格数据源

`deviceRecords` 用于承载首页图表和表格共同依赖的数据。

建议每条记录至少包含：

- `region`
- `deviceType`
- `online`
- `offline`
- `total`

如果后端不想直接给 `total`，也可以让前端自行计算；但如果多个组件都要用，后端直接补齐更省事。

## 6. 和当前仓库接口的边界

这组概览字段不要和下面这些已实现接口混讲：

- `GET /api/health`
- `GET /api/nacos/config`
- `POST /api/nacos/config`
- `GET /api/device-status/options`
- `GET /api/device-status/records`

原因很简单：

- 当前仓库实现的是配置桥和 `8083` 设备状态接口
- 首页概览属于另一类聚合展示职责
- 这组字段目前只存在于方案文档，不存在于当前 FastAPI 路由和 OpenAPI 中

## 7. 汇报建议

汇报时建议直接这样说：

- 当前已落地接口：按 `API_DOC.md` 讲
- 首页概览：属于建议新增能力，推荐单独走 `GET /api/dashboard/overview`

这样可以避免把“未来方案”和“当前代码能力”混为一谈。

## 8. 一句话结论

`GET /api/dashboard/overview` 适合作为首页概览聚合接口，但截至 `2026-04-22` 它仍是方案稿，不属于当前仓库已经实现的 API。
