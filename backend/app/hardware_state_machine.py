from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


SHANGHAI_TZ = timezone(timedelta(hours=8))


ONLINE = "online"
OFFLINE = "offline"
FAULT = "fault"
MAINTENANCE = "maintenance"

NORMAL = "normal"
OPEN = "open"
CLOSED = "closed"
LOCKED = "locked"
ALARM = "alarm"
WARNING = "warning"


def now_iso() -> str:
    return datetime.now(SHANGHAI_TZ).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class DeviceProfile:
    device_type: str
    display_name: str
    unit: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    alarm_min: float | None = None
    alarm_max: float | None = None
    normal_statuses: tuple[str, ...] = (NORMAL,)
    fault_rate: float = 0.015
    offline_rate: float = 0.01
    recover_rate: float = 0.22
    alarm_rate: float = 0.02


@dataclass
class HardwareDevice:
    device_id: str
    name: str
    area_id: str
    area_name: str
    profile: DeviceProfile
    online_status: str = ONLINE
    work_status: str = NORMAL
    alarm_status: str = NORMAL
    value: float | None = None
    battery: int | None = None
    signal: int | None = None
    sequence: int = 0
    last_heartbeat_at: str = field(default_factory=now_iso)
    last_changed_at: str = field(default_factory=now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "id": self.device_id,
            "name": self.name,
            "areaId": self.area_id,
            "areaName": self.area_name,
            "deviceType": self.profile.device_type,
            "deviceTypeName": self.profile.display_name,
            "onlineStatus": self.online_status,
            "workStatus": self.work_status,
            "alarmStatus": self.alarm_status,
            "value": self.value,
            "unit": self.profile.unit,
            "battery": self.battery,
            "signal": self.signal,
            "sequence": self.sequence,
            "lastHeartbeatAt": self.last_heartbeat_at,
            "lastChangedAt": self.last_changed_at,
            "metadata": self.metadata,
        }


class HardwareStateMachineSimulator:
    def __init__(self, *, seed: int | None = None) -> None:
        self._random = random.Random(seed)
        self._lock = threading.RLock()
        self._tick_no = 0
        self._devices: dict[str, HardwareDevice] = {}
        self._seed_defaults()

    @property
    def tick_no(self) -> int:
        with self._lock:
            return self._tick_no

    def snapshot(
        self,
        *,
        area_id: str | None = None,
        device_type: str | None = None,
        online_status: str | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            devices = list(self._devices.values())

        result: list[dict[str, Any]] = []
        for device in devices:
            if area_id and area_id != "all" and device.area_id != area_id:
                continue
            if device_type and device_type != "all" and device.profile.device_type != device_type:
                continue
            if online_status and online_status != "all" and device.online_status != online_status:
                continue
            result.append(device.snapshot())
        return result

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        with self._lock:
            device = self._devices.get(device_id)
            return device.snapshot() if device else None

    def tick(self, *, steps: int = 1) -> dict[str, Any]:
        steps = max(1, min(steps, 100))
        with self._lock:
            for _ in range(steps):
                self._tick_no += 1
                for device in self._devices.values():
                    self._advance_device(device)

            return {
                "tick": self._tick_no,
                "updatedAt": now_iso(),
                "total": len(self._devices),
                "items": [device.snapshot() for device in self._devices.values()],
            }

    def apply_command(
        self,
        device_id: str,
        *,
        command: str,
        operator: str = "simulator",
        reason: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        with self._lock:
            device = self._devices.get(device_id)
            if not device:
                return None

            command = command.strip().lower()
            before = device.snapshot()

            if command == "recover":
                device.online_status = ONLINE
                device.alarm_status = NORMAL
                device.work_status = self._normal_work_status(device)
            elif command == "offline":
                device.online_status = OFFLINE
                device.work_status = OFFLINE
                device.alarm_status = WARNING
            elif command == "fault":
                device.online_status = FAULT
                device.work_status = FAULT
                device.alarm_status = ALARM
            elif command == "maintenance":
                device.online_status = MAINTENANCE
                device.work_status = MAINTENANCE
                device.alarm_status = WARNING
            elif command == "clear_alarm":
                device.alarm_status = NORMAL
                if device.online_status == ONLINE:
                    device.work_status = self._normal_work_status(device)
            elif command == "set_alarm":
                device.alarm_status = ALARM
                if device.online_status == ONLINE:
                    device.work_status = ALARM
            elif command in {"open", "close", "lock", "unlock", "reset"}:
                self._apply_control_command(device, command)
            else:
                return {
                    "accepted": False,
                    "message": f"Unsupported command: {command}",
                    "device": before,
                }

            device.sequence += 1
            device.last_changed_at = now_iso()
            device.last_heartbeat_at = now_iso()
            device.metadata["lastCommand"] = {
                "command": command,
                "operator": operator,
                "reason": reason,
                "payload": payload or {},
                "at": device.last_changed_at,
            }

            return {
                "accepted": True,
                "command": command,
                "before": before,
                "after": device.snapshot(),
            }

    def aggregate_device_status_records(self) -> list[dict[str, Any]]:
        buckets: dict[tuple[str, str], dict[str, Any]] = {}
        with self._lock:
            devices = list(self._devices.values())

        for device in devices:
            key = (device.area_name, device.profile.display_name)
            bucket = buckets.setdefault(
                key,
                {
                    "region": device.area_name,
                    "device": device.profile.display_name,
                    "online": 0,
                    "offline": 0,
                },
            )
            if device.online_status == ONLINE and device.alarm_status != ALARM:
                bucket["online"] += 1
            else:
                bucket["offline"] += 1

        return sorted(buckets.values(), key=lambda item: (item["region"], item["device"]))

    def summary(self) -> dict[str, Any]:
        with self._lock:
            devices = list(self._devices.values())

        total = len(devices)
        online = sum(1 for device in devices if device.online_status == ONLINE)
        offline = total - online
        alarm = sum(1 for device in devices if device.alarm_status == ALARM)
        fault = sum(1 for device in devices if device.online_status == FAULT)
        return {
            "tick": self.tick_no,
            "totalDevices": total,
            "onlineDevices": online,
            "offlineDevices": offline,
            "faultDevices": fault,
            "alarmDevices": alarm,
            "onlineRate": round((online / total * 100) if total else 0, 2),
            "updatedAt": now_iso(),
        }

    def _advance_device(self, device: HardwareDevice) -> None:
        changed = False
        profile = device.profile
        rnd = self._random.random

        device.sequence += 1
        device.last_heartbeat_at = now_iso()

        if device.online_status == ONLINE:
            if rnd() < profile.offline_rate:
                device.online_status = OFFLINE
                device.work_status = OFFLINE
                device.alarm_status = WARNING
                changed = True
            elif rnd() < profile.fault_rate:
                device.online_status = FAULT
                device.work_status = FAULT
                device.alarm_status = ALARM
                changed = True
            else:
                changed = self._advance_online_device(device) or changed
        elif device.online_status in {OFFLINE, FAULT, MAINTENANCE}:
            if rnd() < profile.recover_rate:
                device.online_status = ONLINE
                device.work_status = self._normal_work_status(device)
                device.alarm_status = NORMAL
                changed = True

        if device.battery is not None and self._random.random() < 0.05:
            device.battery = max(0, min(100, device.battery + self._random.choice([-1, 0, 1])))

        if device.signal is not None and self._random.random() < 0.2:
            device.signal = max(0, min(100, device.signal + self._random.randint(-5, 5)))

        if changed:
            device.last_changed_at = now_iso()

    def _advance_online_device(self, device: HardwareDevice) -> bool:
        changed = False
        profile = device.profile

        if profile.min_value is not None and profile.max_value is not None:
            current = device.value
            if current is None:
                current = self._random.uniform(profile.min_value, profile.max_value)
            span = profile.max_value - profile.min_value
            current += self._random.uniform(-span * 0.03, span * 0.03)

            if self._random.random() < profile.alarm_rate:
                if profile.alarm_max is not None:
                    current = self._random.uniform(profile.alarm_max, profile.max_value)
                elif profile.alarm_min is not None:
                    current = self._random.uniform(profile.min_value, profile.alarm_min)

            current = max(profile.min_value, min(profile.max_value, current))
            rounded = round(current, 2)
            changed = changed or device.value != rounded
            device.value = rounded

            in_alarm = (
                (profile.alarm_min is not None and rounded < profile.alarm_min)
                or (profile.alarm_max is not None and rounded > profile.alarm_max)
            )
            device.alarm_status = ALARM if in_alarm else NORMAL
            device.work_status = ALARM if in_alarm else self._normal_work_status(device)
            changed = changed or in_alarm
            return changed

        if self._random.random() < profile.alarm_rate:
            device.alarm_status = ALARM
            device.work_status = ALARM
            changed = True
        elif device.alarm_status == ALARM and self._random.random() < 0.3:
            device.alarm_status = NORMAL
            device.work_status = self._normal_work_status(device)
            changed = True

        return changed

    def _apply_control_command(self, device: HardwareDevice, command: str) -> None:
        if command == "open":
            device.work_status = OPEN
            device.online_status = ONLINE
            device.alarm_status = NORMAL
        elif command == "close":
            device.work_status = CLOSED
            device.online_status = ONLINE
            device.alarm_status = NORMAL
        elif command == "lock":
            device.work_status = LOCKED
            device.online_status = ONLINE
            device.alarm_status = NORMAL
        elif command == "unlock":
            device.work_status = CLOSED
            device.online_status = ONLINE
            device.alarm_status = NORMAL
        elif command == "reset":
            device.online_status = ONLINE
            device.work_status = self._normal_work_status(device)
            device.alarm_status = NORMAL

    def _normal_work_status(self, device: HardwareDevice) -> str:
        if device.profile.normal_statuses:
            return self._random.choice(device.profile.normal_statuses)
        return NORMAL

    def _seed_defaults(self) -> None:
        profiles = {
            "door": DeviceProfile(
                "door",
                "人员智能门/联锁门",
                normal_statuses=(OPEN, CLOSED, LOCKED),
                fault_rate=0.012,
                offline_rate=0.008,
            ),
            "vehicle": DeviceProfile(
                "vehicle",
                "车辆识别与道闸",
                normal_statuses=(OPEN, CLOSED),
                fault_rate=0.012,
                offline_rate=0.008,
            ),
            "rail": DeviceProfile(
                "rail",
                "火车道联动门",
                normal_statuses=(OPEN, CLOSED),
                fault_rate=0.01,
                offline_rate=0.006,
            ),
            "camera": DeviceProfile("camera", "摄像机", fault_rate=0.018, offline_rate=0.012),
            "acoustic": DeviceProfile("acoustic", "声光报警", alarm_rate=0.035),
            "photoelectric": DeviceProfile("photoelectric", "光电报警", alarm_rate=0.04),
            "smoke": DeviceProfile(
                "smoke",
                "烟感器",
                unit="ppm",
                min_value=0,
                max_value=1200,
                alarm_max=650,
                alarm_rate=0.035,
            ),
            "temperature": DeviceProfile(
                "temperature",
                "温感器",
                unit="C",
                min_value=-10,
                max_value=90,
                alarm_max=60,
                alarm_rate=0.03,
            ),
            "nvr": DeviceProfile("nvr", "NVR", fault_rate=0.01, offline_rate=0.006),
            "ai": DeviceProfile("ai", "AI分析服务器", fault_rate=0.012, offline_rate=0.006),
        }
        areas = [
            ("r01", "A区"),
            ("r02", "F区"),
            ("r03", "L区"),
            ("r04", "成品库"),
            ("r05", "火车道"),
            ("r06", "道路"),
            ("r07", "厂房"),
            ("r08", "作业区"),
        ]
        layout = {
            "r01": {"door": 8, "camera": 8, "vehicle": 2, "smoke": 4, "temperature": 4},
            "r02": {"door": 6, "camera": 6, "vehicle": 4, "acoustic": 3},
            "r03": {"door": 5, "camera": 5, "smoke": 5, "temperature": 5},
            "r04": {"door": 4, "camera": 8, "photoelectric": 4, "nvr": 2},
            "r05": {"rail": 4, "camera": 4, "acoustic": 3, "photoelectric": 3},
            "r06": {"vehicle": 6, "camera": 4, "photoelectric": 2},
            "r07": {"smoke": 8, "temperature": 8, "camera": 4},
            "r08": {"door": 4, "camera": 6, "ai": 2, "acoustic": 2},
        }
        area_names = dict(areas)

        for area_id, devices_by_type in layout.items():
            area_name = area_names[area_id]
            for device_type, count in devices_by_type.items():
                profile = profiles[device_type]
                for index in range(1, count + 1):
                    self._add_device(area_id, area_name, profile, index)

    def _add_device(
        self,
        area_id: str,
        area_name: str,
        profile: DeviceProfile,
        index: int,
    ) -> None:
        device_id = f"{profile.device_type}_{area_id}_{index:03d}"
        value = None
        if profile.min_value is not None and profile.max_value is not None:
            low = profile.min_value
            high = profile.alarm_max * 0.75 if profile.alarm_max is not None else profile.max_value
            value = round(self._random.uniform(low, high), 2)

        device = HardwareDevice(
            device_id=device_id,
            name=f"{area_name}{profile.display_name}{index}",
            area_id=area_id,
            area_name=area_name,
            profile=profile,
            work_status=self._random.choice(profile.normal_statuses),
            value=value,
            battery=self._random.randint(55, 100),
            signal=self._random.randint(60, 100),
        )
        self._devices[device_id] = device


SIMULATOR = HardwareStateMachineSimulator()
