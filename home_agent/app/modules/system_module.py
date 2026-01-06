import os
import platform
from datetime import datetime
from typing import Any
from pathlib import Path

from app.core.module_base import ModuleBase, ModuleCapability, ActionResult, ActionStatus
from app.core.audit_log import audit_log


class SystemModule(ModuleBase):
    name = "system"
    description = "System utilities: screenshots, status, notes, and general system info"
    version = "1.0.0"
    
    def _register_capabilities(self) -> None:
        self._capabilities = [
            ModuleCapability(
                name="system.screenshot",
                description="Take a screenshot of the current screen",
                parameters={"save_path": "Optional path to save screenshot"}
            ),
            ModuleCapability(
                name="system.status",
                description="Get current system status including time, platform, and running state",
                parameters={}
            ),
            ModuleCapability(
                name="system.add_note",
                description="Save a note for later reference",
                parameters={"content": "The note content to save"}
            ),
            ModuleCapability(
                name="system.get_notes",
                description="Retrieve saved notes",
                parameters={"limit": "Number of notes to retrieve (default 10)"}
            ),
            ModuleCapability(
                name="system.list_windows",
                description="List all open windows on the system",
                parameters={}
            ),
        ]
    
    async def execute(self, action: str, params: dict[str, Any]) -> ActionResult:
        action_map = {
            "system.screenshot": self._take_screenshot,
            "screenshot": self._take_screenshot,
            "system.status": self._get_status,
            "status": self._get_status,
            "system.add_note": self._add_note,
            "add_note": self._add_note,
            "system.get_notes": self._get_notes,
            "get_notes": self._get_notes,
            "system.list_windows": self._list_windows,
            "list_windows": self._list_windows,
        }
        
        handler = action_map.get(action)
        if handler:
            return await handler(params)
        
        return ActionResult(
            status=ActionStatus.ERROR,
            message=f"Unknown action: {action}"
        )
    
    async def _take_screenshot(self, params: dict[str, Any]) -> ActionResult:
        try:
            import pyautogui
            
            save_path = params.get("save_path", f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Screenshot taken successfully",
                screenshot_path=save_path,
                data={"path": save_path}
            )
        except ImportError:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="pyautogui not available - cannot take screenshots on this system"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to take screenshot: {str(e)}"
            )
    
    async def _get_status(self, params: dict[str, Any]) -> ActionResult:
        try:
            status_info = {
                "time": datetime.now().isoformat(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "jarvis_status": "online"
            }
            
            try:
                import psutil
                status_info["cpu_percent"] = psutil.cpu_percent()
                status_info["memory_percent"] = psutil.virtual_memory().percent
            except ImportError:
                pass
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Jarvis online on {status_info['hostname']} ({status_info['platform']})",
                data=status_info
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to get status: {str(e)}"
            )
    
    async def _add_note(self, params: dict[str, Any]) -> ActionResult:
        content = params.get("content", "")
        if not content:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Note content is required"
            )
        
        try:
            note_id = audit_log.add_note(content)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Note saved (ID: {note_id})",
                data={"note_id": note_id, "content": content}
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to save note: {str(e)}"
            )
    
    async def _get_notes(self, params: dict[str, Any]) -> ActionResult:
        limit = params.get("limit", 10)
        
        try:
            notes = audit_log.get_notes(limit=limit)
            
            if not notes:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="No notes found",
                    data={"notes": []}
                )
            
            notes_text = "\n".join([
                f"[{n['timestamp']}] {n['content']}" for n in notes
            ])
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Found {len(notes)} notes:\n{notes_text}",
                data={"notes": notes}
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to get notes: {str(e)}"
            )
    
    async def _list_windows(self, params: dict[str, Any]) -> ActionResult:
        try:
            if platform.system() == "Windows":
                try:
                    from pywinauto import Desktop
                    desktop = Desktop(backend="uia")
                    windows = []
                    for win in desktop.windows():
                        try:
                            title = win.window_text()
                            if title:
                                windows.append({
                                    "title": title,
                                    "class": win.class_name(),
                                    "visible": win.is_visible()
                                })
                        except Exception:
                            continue
                    
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        message=f"Found {len(windows)} windows",
                        data={"windows": windows}
                    )
                except ImportError:
                    return ActionResult(
                        status=ActionStatus.ERROR,
                        message="pywinauto not available"
                    )
            else:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="Window listing only available on Windows",
                    data={"windows": []}
                )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to list windows: {str(e)}"
            )
    
    async def get_state(self) -> dict[str, Any]:
        status_result = await self._get_status({})
        return status_result.data or {}
