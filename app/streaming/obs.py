"""OBS WebSocket integration (interface).

The implementation requires the ``obs-websocket`` server enabled inside
OBS (Tools -> WebSocket Server). The plugin exposes start/stop streaming,
scene switching, and source updates -- but only when the user provides
host/port/password in the Settings page.
"""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any

from app.utils.logger import get_logger

log = get_logger("streaming.obs")


@dataclass
class OBSConfig:
    host: str = "localhost"
    port: int = 4455
    password: str = ""


class OBSWebSocketClient:
    """Minimal placeholder for OBS WebSocket v5 integration.

    A full implementation should use the ``obsws-python`` library. We avoid
    the hard dependency and ship the interface only.
    """

    def __init__(self, cfg: OBSConfig) -> None:
        self.cfg = cfg

    def ping(self) -> bool:
        try:
            with socket.create_connection((self.cfg.host, self.cfg.port), timeout=1.0):
                return True
        except OSError:
            return False

    def send(self, op: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        log.info("OBS send: {} {}", op, payload)
        return {"status": "skipped", "reason": "OBSWebSocketClient is interface-only; install obsws-python"}


def export_command(host: str, port: int, password: str) -> str:
    """Helper for the UI: convert credentials into the OBS WebSocket URL."""
    return json.dumps({"host": host, "port": port, "password": password})
