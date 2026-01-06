from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class ActionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class ActionResult(BaseModel):
    status: ActionStatus
    message: str
    data: Optional[dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    class Config:
        use_enum_values = True


class ModuleCapability(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any] = {}
    requires_confirmation: bool = False
    dangerous: bool = False


class ModuleBase(ABC):
    name: str = "base"
    description: str = "Base module"
    version: str = "1.0.0"
    
    def __init__(self):
        self._enabled = True
        self._capabilities: list[ModuleCapability] = []
        self._register_capabilities()
    
    @abstractmethod
    def _register_capabilities(self) -> None:
        pass
    
    @property
    def capabilities(self) -> list[ModuleCapability]:
        return self._capabilities
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False
    
    def get_capability(self, name: str) -> Optional[ModuleCapability]:
        for cap in self._capabilities:
            if cap.name == name:
                return cap
        return None
    
    def has_capability(self, name: str) -> bool:
        return self.get_capability(name) is not None
    
    @abstractmethod
    async def execute(self, action: str, params: dict[str, Any]) -> ActionResult:
        pass
    
    @abstractmethod
    async def get_state(self) -> dict[str, Any]:
        pass
    
    def __repr__(self) -> str:
        return f"<Module {self.name} v{self.version} enabled={self.enabled}>"
