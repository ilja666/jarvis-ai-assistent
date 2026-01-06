from typing import Optional
from app.core.module_base import ModuleBase, ActionResult, ActionStatus


class ModuleRegistry:
    _instance: Optional["ModuleRegistry"] = None
    
    def __new__(cls) -> "ModuleRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._modules: dict[str, ModuleBase] = {}
        return cls._instance
    
    def register(self, module: ModuleBase) -> None:
        self._modules[module.name] = module
    
    def unregister(self, name: str) -> bool:
        if name in self._modules:
            del self._modules[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[ModuleBase]:
        return self._modules.get(name)
    
    def get_all(self) -> list[ModuleBase]:
        return list(self._modules.values())
    
    def get_enabled(self) -> list[ModuleBase]:
        return [m for m in self._modules.values() if m.enabled]
    
    def list_capabilities(self) -> dict[str, list[str]]:
        result = {}
        for module in self.get_enabled():
            result[module.name] = [cap.name for cap in module.capabilities]
        return result
    
    def find_capability(self, capability: str) -> Optional[tuple[ModuleBase, str]]:
        if "." in capability:
            module_name, action = capability.split(".", 1)
            module = self.get(module_name)
            if module and module.enabled and module.has_capability(capability):
                return (module, action)
        
        for module in self.get_enabled():
            if module.has_capability(capability):
                return (module, capability)
        
        return None


class Dispatcher:
    def __init__(self, registry: ModuleRegistry):
        self.registry = registry
    
    async def dispatch(self, capability: str, params: dict) -> ActionResult:
        result = self.registry.find_capability(capability)
        
        if result is None:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Capability '{capability}' not found in any enabled module"
            )
        
        module, action = result
        
        cap = module.get_capability(capability)
        if cap and cap.requires_confirmation:
            return ActionResult(
                status=ActionStatus.REQUIRES_CONFIRMATION,
                message=f"Action '{capability}' requires confirmation",
                data={"capability": capability, "params": params}
            )
        
        try:
            return await module.execute(action, params)
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Error executing '{capability}': {str(e)}"
            )


registry = ModuleRegistry()
dispatcher = Dispatcher(registry)
