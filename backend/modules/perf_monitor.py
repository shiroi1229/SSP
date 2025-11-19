"""Performance monitor for capturing system resource metrics."""

from __future__ import annotations

import datetime
from typing import Dict

import psutil


class PerfMonitor:
    def collect(self) -> Dict[str, object]:
        cpu = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory().percent
        swap = psutil.swap_memory().percent
        disk = psutil.disk_usage(".").percent
        load = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0.0, 0.0, 0.0)
        return {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "cpu_percent": cpu,
            "memory_percent": memory,
            "swap_percent": swap,
            "disk_percent": disk,
            "load": {"1m": round(load[0], 2), "5m": round(load[1], 2), "15m": round(load[2], 2)},
        }


perf_monitor = PerfMonitor()
