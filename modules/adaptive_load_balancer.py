"""
Adaptive Load Balancer module for R-v0.4.

It inspects current CPU/memory usage via psutil and selects an operating mode
based on thresholds defined in config/load_balancer_config.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import psutil

CONFIG_PATH = Path("config/load_balancer_config.json")


@dataclass
class LoadMode:
  name: str
  cpu_max: float
  mem_max: float
  action: str


class AdaptiveLoadBalancer:
  def __init__(self, config_path: Path = CONFIG_PATH):
    self.config_path = config_path
    self.modes: List[LoadMode] = []
    self.reload_config()

  def reload_config(self) -> None:
    if not self.config_path.exists():
      self.modes = [
          LoadMode("normal", 0.65, 0.7, "full"),
          LoadMode("degraded", 0.8, 0.85, "reduce_parallelism"),
          LoadMode("throttle", 0.95, 0.95, "pause_heavy_jobs"),
      ]
      return
    data = json.loads(self.config_path.read_text(encoding="utf-8"))
    self.modes = [
        LoadMode(m["name"], float(m["cpu_max"]), float(m["mem_max"]), m.get("action", "full"))
        for m in data.get("modes", [])
    ]
    if not self.modes:
      raise ValueError("Load balancer config must define at least one mode.")

  def get_metrics(self) -> dict:
    return {
        "cpu": psutil.cpu_percent(interval=0.1) / 100.0,
        "memory": psutil.virtual_memory().percent / 100.0,
    }

  def select_mode(self, cpu: float, memory: float) -> LoadMode:
    for mode in self.modes:
      if cpu <= mode.cpu_max and memory <= mode.mem_max:
        return mode
    return self.modes[-1]

  def get_state(self) -> dict:
    metrics = self.get_metrics()
    mode = self.select_mode(metrics["cpu"], metrics["memory"])
    return {
        "metrics": metrics,
        "mode": {"name": mode.name, "action": mode.action},
        "modes": [mode.__dict__ for mode in self.modes],
    }


balancer = AdaptiveLoadBalancer()
