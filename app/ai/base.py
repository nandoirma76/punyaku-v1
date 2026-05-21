"""Plugin contract shared by every AI enhancement back-end.

Concrete plug-ins implement :class:`AIPlugin` and self-register via the
module-level ``register()`` mechanism so the UI can list them without
forcing a heavy import (PyTorch / ONNX / CUDA) at start-up.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelDescriptor:
    """Metadata that lets the auto-installer find / download a model."""

    name: str
    url: str
    sha256: str | None = None
    size_mb: float | None = None
    required_for: list[str] = field(default_factory=list)


class AIPlugin(ABC):
    """Abstract base class for AI plugins.

    Subclasses are encouraged to import their heavy dependencies inside
    :meth:`load` (NOT at module scope) so that the rest of the application
    can run without them.
    """

    name: str = "unnamed"
    category: str = "generic"
    requires_gpu: bool = False
    description: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the back-end can be loaded on this machine."""

    @abstractmethod
    def required_models(self) -> list[ModelDescriptor]:
        """List the model files needed by this plugin."""

    @abstractmethod
    def load(self) -> None:
        """Load model weights / runtime. May raise; never called eagerly."""

    @abstractmethod
    def process(self, payload: Any, **kwargs: Any) -> Any:
        """Run inference. ``payload`` is plugin-specific (frame, audio, ...)."""


_REGISTRY: dict[str, type[AIPlugin]] = {}


def register(cls: type[AIPlugin]) -> type[AIPlugin]:
    """Class decorator: ``@register`` adds the class to the global registry."""
    _REGISTRY[cls.__name__] = cls
    return cls


def list_plugins() -> list[type[AIPlugin]]:
    return list(_REGISTRY.values())


def find(name: str) -> type[AIPlugin] | None:
    return _REGISTRY.get(name)
