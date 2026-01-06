import os
import subprocess
import platform
from typing import Any, Optional
from pathlib import Path

from app.core.module_base import ModuleBase, ModuleCapability, ActionResult, ActionStatus


class WindowsModule(ModuleBase):
    name = "windows"
    description = "Windows application control: open apps, manage windows, run commands"
    version = "1.0.0"
    
    APP_PATHS = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "notepad": "notepad.exe",
        "calc": "calc.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "code": "code.cmd",
        "vscode": "code.cmd",
        "cursor": r"C:\Users\Ilja\AppData\Local\Programs\cursor\Cursor.exe",
        "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
        "wordpad": "wordpad.exe",
        "paint": "mspaint.exe",
        "snipping": "snippingtool.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "control": "control.exe",
        "settings": "ms-settings:",
    }
    
    def _register_capabilities(self) -> None:
        self._capabilities = [
            ModuleCapability(
                name="windows.open_app",
                description="Open a Windows application by name",
                parameters={
                    "app": "Application name (e.g., chrome, notepad, cursor, word)",
                    "args": "Optional command line arguments"
                }
            ),
            ModuleCapability(
                name="windows.close_app",
                description="Close a running application",
                parameters={"app": "Application name to close"},
                requires_confirmation=True,
                dangerous=True
            ),
            ModuleCapability(
                name="windows.focus_window",
                description="Bring a window to the foreground",
                parameters={"title": "Window title (partial match)"}
            ),
            ModuleCapability(
                name="windows.run_command",
                description="Run a shell command",
                parameters={"command": "Command to execute"},
                requires_confirmation=True,
                dangerous=True
            ),
            ModuleCapability(
                name="windows.list_apps",
                description="List available applications that can be opened",
                parameters={}
            ),
            ModuleCapability(
                name="windows.type_text",
                description="Type text into the currently focused window",
                parameters={"text": "Text to type"}
            ),
            ModuleCapability(
                name="windows.press_key",
                description="Press a keyboard key or combination",
                parameters={"keys": "Key(s) to press (e.g., 'enter', 'ctrl+s', 'alt+tab')"}
            ),
        ]
    
    async def execute(self, action: str, params: dict[str, Any]) -> ActionResult:
        action_map = {
            "windows.open_app": self._open_app,
            "open_app": self._open_app,
            "windows.close_app": self._close_app,
            "close_app": self._close_app,
            "windows.focus_window": self._focus_window,
            "focus_window": self._focus_window,
            "windows.run_command": self._run_command,
            "run_command": self._run_command,
            "windows.list_apps": self._list_apps,
            "list_apps": self._list_apps,
            "windows.type_text": self._type_text,
            "type_text": self._type_text,
            "windows.press_key": self._press_key,
            "press_key": self._press_key,
        }
        
        handler = action_map.get(action)
        if handler:
            return await handler(params)
        
        return ActionResult(
            status=ActionStatus.ERROR,
            message=f"Unknown action: {action}"
        )
    
    async def _open_app(self, params: dict[str, Any]) -> ActionResult:
        app_name = params.get("app", "").lower().strip()
        args = params.get("args", "")
        
        if not app_name:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Application name is required"
            )
        
        if platform.system() != "Windows":
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Windows module only works on Windows systems"
            )
        
        try:
            app_path = self.APP_PATHS.get(app_name)
            
            if app_path:
                if app_path.startswith("ms-"):
                    os.startfile(app_path)
                else:
                    if args:
                        subprocess.Popen([app_path, args], shell=True)
                    else:
                        subprocess.Popen([app_path], shell=True)
                
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Opened {app_name}",
                    data={"app": app_name, "path": app_path}
                )
            else:
                try:
                    subprocess.Popen(app_name, shell=True)
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        message=f"Started {app_name} (as command)",
                        data={"app": app_name}
                    )
                except FileNotFoundError:
                    return ActionResult(
                        status=ActionStatus.ERROR,
                        message=f"Application '{app_name}' not found. Use 'list_apps' to see available apps."
                    )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to open {app_name}: {str(e)}"
            )
    
    async def _close_app(self, params: dict[str, Any]) -> ActionResult:
        app_name = params.get("app", "").lower().strip()
        
        if not app_name:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Application name is required"
            )
        
        try:
            process_names = {
                "chrome": "chrome.exe",
                "firefox": "firefox.exe",
                "edge": "msedge.exe",
                "notepad": "notepad.exe",
                "cursor": "Cursor.exe",
                "code": "Code.exe",
                "word": "WINWORD.EXE",
                "excel": "EXCEL.EXE",
                "outlook": "OUTLOOK.EXE",
            }
            
            process_name = process_names.get(app_name, f"{app_name}.exe")
            
            result = subprocess.run(
                ["taskkill", "/IM", process_name, "/F"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Closed {app_name}",
                    data={"app": app_name}
                )
            else:
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Could not close {app_name}: {result.stderr}"
                )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to close {app_name}: {str(e)}"
            )
    
    async def _focus_window(self, params: dict[str, Any]) -> ActionResult:
        title = params.get("title", "")
        
        if not title:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Window title is required"
            )
        
        try:
            from pywinauto import Desktop
            
            desktop = Desktop(backend="uia")
            
            for win in desktop.windows():
                try:
                    win_title = win.window_text()
                    if title.lower() in win_title.lower():
                        win.set_focus()
                        return ActionResult(
                            status=ActionStatus.SUCCESS,
                            message=f"Focused window: {win_title}",
                            data={"title": win_title}
                        )
                except Exception:
                    continue
            
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"No window found matching '{title}'"
            )
        
        except ImportError:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="pywinauto not available"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to focus window: {str(e)}"
            )
    
    async def _run_command(self, params: dict[str, Any]) -> ActionResult:
        command = params.get("command", "")
        
        if not command:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Command is required"
            )
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stdout or result.stderr or "Command completed"
            
            return ActionResult(
                status=ActionStatus.SUCCESS if result.returncode == 0 else ActionStatus.ERROR,
                message=output[:1000],
                data={
                    "command": command,
                    "return_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )
        
        except subprocess.TimeoutExpired:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Command timed out after 30 seconds"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to run command: {str(e)}"
            )
    
    async def _list_apps(self, params: dict[str, Any]) -> ActionResult:
        apps_list = "\n".join([f"- {name}" for name in sorted(self.APP_PATHS.keys())])
        
        return ActionResult(
            status=ActionStatus.SUCCESS,
            message=f"Available applications:\n{apps_list}",
            data={"apps": list(self.APP_PATHS.keys())}
        )
    
    async def _type_text(self, params: dict[str, Any]) -> ActionResult:
        text = params.get("text", "")
        
        if not text:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Text is required"
            )
        
        try:
            import pyautogui
            import time
            
            time.sleep(0.5)
            pyautogui.write(text, interval=0.02)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Typed text ({len(text)} characters)",
                data={"text_length": len(text)}
            )
        
        except ImportError:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="pyautogui not available"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to type text: {str(e)}"
            )
    
    async def _press_key(self, params: dict[str, Any]) -> ActionResult:
        keys = params.get("keys", "")
        
        if not keys:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Keys are required"
            )
        
        try:
            import pyautogui
            
            if "+" in keys:
                key_combo = keys.lower().split("+")
                pyautogui.hotkey(*key_combo)
            else:
                pyautogui.press(keys.lower())
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Pressed: {keys}",
                data={"keys": keys}
            )
        
        except ImportError:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="pyautogui not available"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to press key: {str(e)}"
            )
    
    async def get_state(self) -> dict[str, Any]:
        return {
            "platform": platform.system(),
            "available_apps": list(self.APP_PATHS.keys())
        }
