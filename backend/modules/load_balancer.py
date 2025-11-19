"""Adaptive load balancing service used by R-v0.4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from modules.adaptive_load_balancer import AdaptiveLoadBalancer, CONFIG_PATH
from modules.log_manager import log_manager


class LoadBalancerService:
    def __init__(self):
        self._balancer = AdaptiveLoadBalancer()
        self._config_path = CONFIG_PATH

    def get_state(self) -> Dict[str, Any]:
        return self._balancer.get_state()

    def reload_config(self) -> None:
        log_manager.info("[LoadBalancerService] Reloading load balancer config.")
        self._balancer.reload_config()

    def update_modes(self, modes: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {"modes": modes}
        self._config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.reload_config()
        return self.get_state()


load_balancer_service = LoadBalancerService()
