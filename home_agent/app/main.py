import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Any, Optional
import logging

from app.core.config import settings
from app.core.registry import registry, dispatcher
from app.core.audit_log import audit_log
from app.core.ai_interpreter import ai_interpreter
from app.core.module_base import ActionResult, ActionStatus

from app.modules.system_module import SystemModule
from app.modules.windows_module import WindowsModule
from app.modules.cursor_module import CursorModule
from app.modules.kali_module import KaliModule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_modules():
    registry.register(SystemModule())
    registry.register(WindowsModule())
    registry.register(CursorModule())
    registry.register(KaliModule())
    logger.info(f"Registered {len(registry.get_all())} modules")


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_modules()
    logger.info("Jarvis Home Agent started")
    yield
    logger.info("Jarvis Home Agent shutting down")


app = FastAPI(
    title="Jarvis Home Agent",
    description="Personal AI Assistant - Home Agent API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None


class ActionRequest(BaseModel):
    capability: str
    params: dict[str, Any] = {}
    user_id: Optional[str] = None
    confirmed: bool = False


class ConfirmRequest(BaseModel):
    capability: str
    params: dict[str, Any] = {}
    user_id: Optional[str] = None


@app.get("/")
async def root():
    return {
        "name": "Jarvis Home Agent",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/message")
async def process_message(request: MessageRequest):
    try:
        interpretation = await ai_interpreter.interpret(
            request.message,
            user_id=request.user_id
        )
        
        if interpretation.get("action"):
            result = await ai_interpreter.execute_interpreted(interpretation)
            
            return {
                "thought": interpretation.get("thought"),
                "response": interpretation.get("response"),
                "action_result": {
                    "status": result.status,
                    "message": result.message,
                    "data": result.data,
                    "screenshot_path": result.screenshot_path
                }
            }
        else:
            return {
                "thought": interpretation.get("thought"),
                "response": interpretation.get("response"),
                "action_result": None
            }
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/action")
async def execute_action(request: ActionRequest):
    try:
        cap_info = registry.find_capability(request.capability)
        
        if cap_info is None:
            raise HTTPException(
                status_code=404,
                detail=f"Capability '{request.capability}' not found"
            )
        
        module, action = cap_info
        cap = module.get_capability(request.capability)
        
        if cap and cap.requires_confirmation and not request.confirmed:
            return {
                "status": "requires_confirmation",
                "message": f"Action '{request.capability}' requires confirmation",
                "capability": request.capability,
                "params": request.params
            }
        
        result = await dispatcher.dispatch(request.capability, request.params)
        
        audit_log.log_action(
            module=module.name,
            action=action,
            status=result.status,
            user_id=request.user_id,
            params=request.params,
            result=result.message
        )
        
        return {
            "status": result.status,
            "message": result.message,
            "data": result.data,
            "screenshot_path": result.screenshot_path
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/action/confirm")
async def confirm_action(request: ConfirmRequest):
    action_request = ActionRequest(
        capability=request.capability,
        params=request.params,
        user_id=request.user_id,
        confirmed=True
    )
    return await execute_action(action_request)


@app.get("/modules")
async def list_modules():
    modules = []
    for module in registry.get_all():
        modules.append({
            "name": module.name,
            "description": module.description,
            "version": module.version,
            "enabled": module.enabled,
            "capabilities": [
                {
                    "name": cap.name,
                    "description": cap.description,
                    "parameters": cap.parameters,
                    "requires_confirmation": cap.requires_confirmation,
                    "dangerous": cap.dangerous
                }
                for cap in module.capabilities
            ]
        })
    return {"modules": modules}


@app.get("/modules/{module_name}")
async def get_module(module_name: str):
    module = registry.get(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    
    state = await module.get_state()
    
    return {
        "name": module.name,
        "description": module.description,
        "version": module.version,
        "enabled": module.enabled,
        "state": state,
        "capabilities": [
            {
                "name": cap.name,
                "description": cap.description,
                "parameters": cap.parameters,
                "requires_confirmation": cap.requires_confirmation,
                "dangerous": cap.dangerous
            }
            for cap in module.capabilities
        ]
    }


@app.post("/modules/{module_name}/enable")
async def enable_module(module_name: str):
    module = registry.get(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    
    module.enable()
    return {"message": f"Module '{module_name}' enabled"}


@app.post("/modules/{module_name}/disable")
async def disable_module(module_name: str):
    module = registry.get(module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module '{module_name}' not found")
    
    module.disable()
    return {"message": f"Module '{module_name}' disabled"}


@app.get("/capabilities")
async def list_capabilities():
    return {"capabilities": registry.list_capabilities()}


@app.get("/logs")
async def get_logs(limit: int = 20):
    logs = audit_log.get_recent_logs(limit=limit)
    return {"logs": logs}


@app.get("/screenshot/{filename}")
async def get_screenshot(filename: str):
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return FileResponse(filename, media_type="image/png")


@app.post("/notes")
async def add_note(content: str):
    note_id = audit_log.add_note(content)
    return {"note_id": note_id, "message": "Note saved"}


@app.get("/notes")
async def get_notes(limit: int = 10):
    notes = audit_log.get_notes(limit=limit)
    return {"notes": notes}


@app.post("/conversation/clear")
async def clear_conversation():
    ai_interpreter.clear_history()
    return {"message": "Conversation history cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
