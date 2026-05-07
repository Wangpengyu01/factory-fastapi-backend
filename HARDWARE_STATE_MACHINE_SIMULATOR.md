# 硬件状态机模拟器设计文档

整理日期：`2026-05-07`

本文档说明如何用 Python 把各类硬件抽象成状态机，并在真实硬件未完成对接前，通过模拟器随机生成设备状态，供 `8083` 前端和 FastAPI 接口读取。

## 1. 设计目标

核心目标：

| 目标 | 说明 |
|---|---|
| 快速联调 | 前端和接口不等硬件，先用模拟状态跑通 |
| 抽象统一 | 门禁、道闸、摄像机、烟感、温感、报警器都统一成设备状态机 |
| 接口稳定 | 前端只读 `/api/...`，不关心数据来自模拟器还是真实硬件 |
| 后续可替换 | 硬件接入后只替换数据 provider，不重写前端和 API |
| Python 实现 | 当前阶段性能不是第一优先级，开发速度优先 |

## 2. 总体架构

```text
8083 前端
  -> /api/dashboard/overview
  -> /api/device-status/options
  -> /api/device-status/summary
  -> /api/device-status/records
      -> FastAPI
        -> DeviceStatusService
          -> HardwareStateMachineSimulator
            -> 每个硬件对象自己的状态机
```

后续真实硬件接入：

```text
FastAPI
  -> DeviceStatusService
    -> HardwareProvider
      -> SimulatorProvider     本地开发 / 演示
      -> RealHardwareProvider  真实门禁 / 道闸 / 传感器 / 视频平台
```

## 3. 状态机抽象

每个硬件统一抽象成一个 `HardwareDevice`。

核心字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `string` | 设备 ID |
| `name` | `string` | 设备名称 |
| `areaId` | `string` | 区域 ID |
| `areaName` | `string` | 区域名称 |
| `deviceType` | `string` | 设备类型 |
| `deviceTypeName` | `string` | 设备类型中文名 |
| `onlineStatus` | `string` | 在线状态 |
| `workStatus` | `string` | 工作状态 |
| `alarmStatus` | `string` | 告警状态 |
| `value` | `number/null` | 传感器数值 |
| `unit` | `string/null` | 单位 |
| `battery` | `number/null` | 电量 |
| `signal` | `number/null` | 信号强度 |
| `sequence` | `number` | 状态变化序号 |
| `lastHeartbeatAt` | `string` | 最后心跳时间 |
| `lastChangedAt` | `string` | 最后状态变化时间 |
| `metadata` | `object` | 扩展数据 |

## 4. 状态枚举

### 4.1 在线状态

| 值 | 说明 |
|---|---|
| `online` | 在线 |
| `offline` | 离线 |
| `fault` | 故障 |
| `maintenance` | 维护 |

### 4.2 工作状态

| 值 | 说明 |
|---|---|
| `normal` | 正常 |
| `open` | 开启 |
| `closed` | 关闭 |
| `locked` | 锁定 |
| `alarm` | 告警态 |
| `warning` | 预警态 |
| `fault` | 故障态 |
| `offline` | 离线态 |
| `maintenance` | 维护态 |

### 4.3 告警状态

| 值 | 说明 |
|---|---|
| `normal` | 无告警 |
| `warning` | 预警 |
| `alarm` | 告警 |

## 5. 已模拟的硬件类型

| 类型 | 中文名 | 行为 |
|---|---|---|
| `door` | 人员智能门/联锁门 | open/closed/locked 随机变化，可故障、离线 |
| `vehicle` | 车辆识别与道闸 | open/closed 随机变化，可故障、离线 |
| `rail` | 火车道联动门 | open/closed 随机变化，可故障、离线 |
| `camera` | 摄像机 | 在线、离线、故障 |
| `acoustic` | 声光报警 | 可随机进入告警 |
| `photoelectric` | 光电报警 | 可随机进入告警 |
| `smoke` | 烟感器 | 数值随机游走，超过阈值进入告警 |
| `temperature` | 温感器 | 数值随机游走，超过阈值进入告警 |
| `nvr` | NVR | 在线、离线、故障 |
| `ai` | AI分析服务器 | 在线、离线、故障 |

## 6. 状态推进规则

模拟器每次 `tick` 会遍历所有设备，并按概率推进状态：

| 当前状态 | 可能变化 |
|---|---|
| `online` | 保持在线、进入 `offline`、进入 `fault`、进入 `alarm` |
| `offline` | 保持离线、恢复 `online` |
| `fault` | 保持故障、恢复 `online` |
| `maintenance` | 保持维护、恢复 `online` |
| 传感器数值 | 在范围内随机游走，偶发超过阈值 |

默认自动推进：

```env
USE_STATE_MACHINE_SIMULATOR=true
SIMULATOR_AUTO_TICK=true
SIMULATOR_TICK_SECONDS=5
```

## 7. API 接入

### 7.1 读取模拟器汇总

`GET /api/simulator/summary`

返回：

```json
{
  "code": 200,
  "success": true,
  "message": "操作成功",
  "data": {
    "tick": 12,
    "totalDevices": 105,
    "onlineDevices": 98,
    "offlineDevices": 7,
    "faultDevices": 2,
    "alarmDevices": 3,
    "onlineRate": 93.33,
    "updatedAt": "2026-05-07T09:00:00+08:00"
  }
}
```

### 7.2 读取模拟设备列表

`GET /api/simulator/devices`

Query：

| 参数 | 类型 | 说明 |
|---|---|---|
| `areaId` | `string` | 区域 ID |
| `deviceType` | `string` | 设备类型 |
| `onlineStatus` | `string` | 在线状态 |

示例：

```bash
curl "http://localhost:8000/api/simulator/devices?areaId=r01&deviceType=smoke"
```

### 7.3 读取单个模拟设备

`GET /api/simulator/devices/{deviceId}`

示例：

```bash
curl "http://localhost:8000/api/simulator/devices/smoke_r01_001"
```

### 7.4 手动推进状态

`POST /api/simulator/tick?steps=1`

示例：

```bash
curl -X POST "http://localhost:8000/api/simulator/tick?steps=10"
```

### 7.5 手动下发模拟命令

`POST /api/simulator/devices/{deviceId}/command`

Body：

```json
{
  "command": "fault",
  "reason": "联调测试",
  "operator": "tester",
  "payload": {}
}
```

支持命令：

| 命令 | 说明 |
|---|---|
| `recover` | 恢复在线正常 |
| `offline` | 强制离线 |
| `fault` | 强制故障 |
| `maintenance` | 强制维护 |
| `set_alarm` | 强制告警 |
| `clear_alarm` | 清除告警 |
| `open` | 打开 |
| `close` | 关闭 |
| `lock` | 锁定 |
| `unlock` | 解锁 |
| `reset` | 复位 |

## 8. 与 8083 接口的关系

开启 `USE_STATE_MACHINE_SIMULATOR=true` 后，以下接口会从状态机聚合数据：

| 接口 | 数据来源 |
|---|---|
| `GET /api/dashboard/overview` | 状态机聚合 |
| `GET /api/device-status/options` | 状态机聚合 |
| `GET /api/device-status/summary` | 状态机聚合 |
| `GET /api/device-status/records` | 状态机聚合 |

`/api/device-status/records` 输出仍保持 8083 需要的结构：

```json
{
  "records": [
    {
      "region": "A区",
      "device": "烟感器",
      "online": 3,
      "offline": 1
    }
  ],
  "updatedAt": "2026-05-07T09:00:00+08:00"
}
```

前端不需要知道这些数据来自模拟器。

## 9. 真实硬件接入方式

真实硬件接入时，不改前端，不改 API 路径，只替换数据来源。

建议定义统一接口：

```py
class HardwareProvider:
    def list_devices(self) -> list[dict]:
        raise NotImplementedError

    def get_device(self, device_id: str) -> dict | None:
        raise NotImplementedError

    def send_command(self, device_id: str, command: str, payload: dict) -> dict:
        raise NotImplementedError
```

开发阶段：

```py
provider = SimulatorProvider()
```

真实阶段：

```py
provider = RealHardwareProvider()
```

后端 service 层只调用 provider，不直接关心底层是模拟器、数据库、MQTT、Modbus、HTTP SDK 还是厂商平台。

## 10. 后续集成建议

| 阶段 | 做法 |
|---|---|
| 当前阶段 | 使用内存状态机，最快跑通联调 |
| 第二阶段 | 把状态快照定时写入 Redis 或数据库 |
| 第三阶段 | 硬件对接程序写入统一状态表 |
| 第四阶段 | FastAPI 从统一状态表读取 |
| 第五阶段 | 控制类接口通过消息队列下发到硬件适配器 |

推荐最终链路：

```text
硬件适配器
  -> 统一状态表 / Redis / 消息队列
    -> FastAPI
      -> 8083 前端
```

控制命令链路：

```text
8083 前端
  -> FastAPI command 接口
    -> command 表 / 消息队列
      -> 硬件适配器
        -> 真实硬件
```

## 11. 当前已落地文件

| 文件 | 说明 |
|---|---|
| `backend/app/hardware_state_machine.py` | 状态机模拟器核心 |
| `backend/app/main.py` | 已接入 simulator API 和 8083 设备状态聚合 |
| `backend/.env.example` | 新增模拟器开关 |
| `HARDWARE_STATE_MACHINE_SIMULATOR.md` | 本设计文档 |
