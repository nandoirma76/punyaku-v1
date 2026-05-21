"""Lightweight hardware monitor used by the dashboard widget.

Sampling is cheap (<5 ms per probe). For GPU/VRAM we try ``pynvml`` first,
``GPUtil`` next, and fall back to a "no GPU" snapshot if neither is
available. All accesses are best-effort and never raise to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.utils.logger import get_logger

log = get_logger("hardware")


@dataclass
class GpuStat:
    index: int
    name: str
    load_pct: float
    mem_used_mb: float
    mem_total_mb: float
    temperature_c: float | None = None

    @property
    def mem_pct(self) -> float:
        return (self.mem_used_mb / self.mem_total_mb * 100.0) if self.mem_total_mb else 0.0


@dataclass
class HardwareSnapshot:
    cpu_pct: float
    cpu_freq_mhz: float
    cpu_cores_logical: int
    cpu_cores_physical: int
    ram_used_mb: float
    ram_total_mb: float
    ram_pct: float
    swap_used_mb: float
    swap_total_mb: float
    gpus: list[GpuStat] = field(default_factory=list)
    cpu_temperature_c: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "cpu_pct": self.cpu_pct,
            "cpu_freq_mhz": self.cpu_freq_mhz,
            "cpu_cores_logical": self.cpu_cores_logical,
            "cpu_cores_physical": self.cpu_cores_physical,
            "ram_used_mb": self.ram_used_mb,
            "ram_total_mb": self.ram_total_mb,
            "ram_pct": self.ram_pct,
            "swap_used_mb": self.swap_used_mb,
            "swap_total_mb": self.swap_total_mb,
            "gpus": [g.__dict__ for g in self.gpus],
            "cpu_temperature_c": self.cpu_temperature_c,
        }


def _bytes_to_mb(value: float) -> float:
    return value / 1024.0 / 1024.0


def _gpu_via_pynvml() -> list[GpuStat]:
    try:
        import pynvml  # type: ignore[import-not-found]
    except Exception:
        return []
    try:
        pynvml.nvmlInit()
    except Exception:
        return []
    out: list[GpuStat] = []
    try:
        count = pynvml.nvmlDeviceGetCount()
        for i in range(count):
            h = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(h)
            if isinstance(name, bytes):
                name = name.decode("utf-8", errors="ignore")
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            try:
                temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                temp = None
            out.append(GpuStat(
                index=i,
                name=str(name),
                load_pct=float(util.gpu),
                mem_used_mb=_bytes_to_mb(float(mem.used)),
                mem_total_mb=_bytes_to_mb(float(mem.total)),
                temperature_c=float(temp) if temp is not None else None,
            ))
    finally:
        import contextlib

        with contextlib.suppress(Exception):
            pynvml.nvmlShutdown()
    return out


def _gpu_via_gputil() -> list[GpuStat]:
    try:
        import GPUtil  # type: ignore[import-not-found]
    except Exception:
        return []
    try:
        gpus = GPUtil.getGPUs()
    except Exception:
        return []
    return [
        GpuStat(
            index=g.id,
            name=g.name,
            load_pct=float(g.load) * 100.0,
            mem_used_mb=float(g.memoryUsed),
            mem_total_mb=float(g.memoryTotal),
            temperature_c=float(g.temperature) if g.temperature else None,
        )
        for g in gpus
    ]


def _cpu_temperature() -> float | None:
    try:
        import psutil  # type: ignore[import-not-found]
    except Exception:
        return None
    sensors = getattr(psutil, "sensors_temperatures", None)
    if not sensors:
        return None
    try:
        data = sensors()
    except Exception:
        return None
    for entries in data.values():
        for entry in entries:
            if entry.current:
                return float(entry.current)
    return None


def snapshot() -> HardwareSnapshot:
    """Sample CPU, RAM, and GPU state right now."""
    try:
        import psutil  # type: ignore[import-not-found]
    except Exception:
        return HardwareSnapshot(
            cpu_pct=0.0,
            cpu_freq_mhz=0.0,
            cpu_cores_logical=0,
            cpu_cores_physical=0,
            ram_used_mb=0.0,
            ram_total_mb=0.0,
            ram_pct=0.0,
            swap_used_mb=0.0,
            swap_total_mb=0.0,
        )

    vm = psutil.virtual_memory()
    sm = psutil.swap_memory()
    freq = psutil.cpu_freq()

    gpus = _gpu_via_pynvml() or _gpu_via_gputil()

    return HardwareSnapshot(
        cpu_pct=float(psutil.cpu_percent(interval=None)),
        cpu_freq_mhz=float(freq.current) if freq else 0.0,
        cpu_cores_logical=psutil.cpu_count(logical=True) or 0,
        cpu_cores_physical=psutil.cpu_count(logical=False) or 0,
        ram_used_mb=_bytes_to_mb(float(vm.used)),
        ram_total_mb=_bytes_to_mb(float(vm.total)),
        ram_pct=float(vm.percent),
        swap_used_mb=_bytes_to_mb(float(sm.used)),
        swap_total_mb=_bytes_to_mb(float(sm.total)),
        gpus=gpus,
        cpu_temperature_c=_cpu_temperature(),
    )
