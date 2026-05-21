"""Cloud render service client (interface)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

log = get_logger("cloud.render")


@dataclass
class CloudCredentials:
    endpoint: str
    api_key: str


class CloudRenderClient:
    """Placeholder client for offloading heavy renders to a remote worker."""

    def __init__(self, creds: CloudCredentials) -> None:
        self.creds = creds

    def submit(self, source: Path, payload: dict[str, Any]) -> str:
        log.info("Cloud submit (stub): {} payload_keys={}", source, list(payload))
        return "job-not-submitted"

    def status(self, job_id: str) -> dict[str, Any]:
        return {"id": job_id, "status": "not_implemented"}

    def download(self, job_id: str, target: Path) -> Path:
        log.info("Cloud download (stub) -> {}", target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"")
        return target
