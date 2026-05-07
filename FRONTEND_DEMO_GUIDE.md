# 前端演示文档

## 1. 演示目标

这次演示给前端重点说明两件事：

1. Nacos 配置桥已经跑通，前端可以直接调接口读取/发布配置
2. `8083` 设备状态控件已经有可联调的 mock 接口，前端可以先按协议接入

## 2. 当前演示环境

- 服务器 IP：`101.43.49.78`
- 前端演示页：`http://101.43.49.78:9001`
- 后端 Swagger：`http://101.43.49.78:8000/docs`
- 后端健康检查：`http://101.43.49.78:8000/api/health`

说明：

- 服务器上的 `9000` 和 `8083` 已被其他服务占用，所以本次演示页使用 `9001`
- `8000` 是本项目 FastAPI 服务

## 3. 演示结论先讲

建议你开场先直接说这段：

“这次我给大家看两部分。第一部分是已经真实跑起来的 Nacos 配置桥，前端现在就可以调。第二部分是 `8083` 设备状态控件的联调接口，我已经补了 mock 数据接口，前端可以先按这个协议接，后面再无缝切真实数据源。” 

## 4. 推荐演示顺序

### 第一步：证明服务是活的

打开：

- `http://101.43.49.78:8000/api/health`

预期返回：

```json
{"status":"ok"}
```

你可以说：

“先看服务已经在线，后端接口不是文档状态，是已经部署运行的状态。”

### 第二步：打开 Swagger 给前端看接口清单

打开：

- `http://101.43.49.78:8000/docs`

重点让前端看这 5 个接口：

1. `GET /api/health`
2. `GET /api/nacos/config`
3. `POST /api/nacos/config`
4. `GET /api/device-status/options`
5. `GET /api/device-status/records`

你可以说：

“前两个是配置桥的核心能力，后两个是这次专门给 `8083` 设备状态控件补的联调接口。”

### 第三步：演示 Nacos 配置读取

在 Swagger 里调用：

```http
GET /api/nacos/config?dataId=&group=DEFAULT_GROUP
```

说明点：

- `dataId` 留空时会返回全量配置
- 如果只想取某个字段，可以传 `field`

再演示一个单字段读取例子：

```http
GET /api/nacos/config?dataId=device-status.json&group=DEFAULT_GROUP&field=deviceStatus.refreshSeconds
```

你可以说：

“这一层解决的是前端如何直接通过 HTTP 读取 Nacos 配置，不需要自己去对接 Nacos 原生接口。”

### 第四步：演示 8083 设备状态筛选项接口

在 Swagger 里调用：

```http
GET /api/device-status/options
```

预期返回结构：

```json
{
  "regions": ["全部", "A区", "F区", "L区", "成品库"],
  "devices": ["全部", "人员智能门/联锁门", "摄像机", "车辆识别与道闸"]
}
```

说明点：

- `regions` 和 `devices` 都是字符串数组
- 这是为了直接兼容当前 `8083` 组件，减少前端改动

如果想演示区域联动，再调：

```http
GET /api/device-status/options?region=A区
```

### 第五步：演示 8083 设备状态记录接口

在 Swagger 里调用：

```http
GET /api/device-status/records
```

再调用一个筛选版本：

```http
GET /api/device-status/records?region=A区&device=摄像机
```

预期返回结构：

```json
{
  "records": [
    {
      "region": "A区",
      "device": "摄像机",
      "online": 86,
      "offline": 6
    }
  ],
  "updatedAt": "2026-04-13T18:00:00+08:00"
}
```

你可以说：

“当前接口直接返回 `records` 数组，前端可以沿用现在组件的聚合逻辑，自己算 `online`、`offline`、`total` 和在线率，这样对接成本最低。”

## 5. 前端要怎么接

你可以直接给前端这个结论：

1. 页面初始化时调一次 `GET /api/device-status/options`
2. 再调一次 `GET /api/device-status/records?region=全部&device=全部`
3. 切换区域时，先刷新 `options`，再刷新 `records`
4. 切换设备时，只刷新 `records`
5. 建议每 `30s` 刷新一次 `records`

## 6. 这次演示要特别讲清楚的边界

这一段很重要，建议你明确说：

“这次设备状态接口是联调用 mock 版，目的是先把前端接入方式和字段协议定下来。也就是说，前端现在可以先按这个接口结构接；后面如果切真实业务数据源，接口结构尽量不变。” 

还要补一句：

“树菜单、测点详情、任务管理、首页概览这些业务接口范围稿是另一套文档，不在这次 FastAPI 演示部署里。” 

## 7. 前端可能会问的问题

### 1) 现在返回的是不是真实数据？

回答：

“默认是 mock 数据，为了先让前端把流程跑通；如果传 `dataId`，后端也支持从 Nacos 指定配置里读取 `deviceStatus.records`。” 

### 2) 为啥不用 `summary`，而是返回 `records`？

回答：

“因为当前 `8083` 打包组件本身就是按 `records + regions + devices` 这套输入结构工作的，返回 `records` 对前端改动最小。” 

### 3) 参数名到底是 `region` 还是 `regionId`，`device` 还是 `deviceType`？

回答：

“后端现在两套都兼容，前端按你们习惯来就行。” 

### 4) 后面切真实数据会不会要重写前端？

回答：

“目标就是不重写。现在先把协议定住，后面主要换的是后端数据来源，不是前端调用方式。” 

## 8. 演示时可以直接贴给前端的请求示例

```bash
curl "http://101.43.49.78:8000/api/health"

curl "http://101.43.49.78:8000/api/device-status/options"

curl "http://101.43.49.78:8000/api/device-status/options?region=A区"

curl "http://101.43.49.78:8000/api/device-status/records"

curl "http://101.43.49.78:8000/api/device-status/records?region=A区&device=摄像机"
```

## 9. 一句话总结

你最后可以这样收：

“今天这套已经能演示、能联调、能先接入。前端现在按 `options + records` 接就行，后面真实数据接进来时，尽量不改你们调用层。” 
