import os
import subprocess
import platform
from typing import Any, Optional
from pathlib import Path
import time

from app.core.module_base import ModuleBase, ModuleCapability, ActionResult, ActionStatus
from app.core.config import settings


class CursorModule(ModuleBase):
    name = "cursor"
    description = "Cursor IDE control: open projects, create files, run commands via CLI and filesystem"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.cursor_path = settings.cursor_path
    
    def _register_capabilities(self) -> None:
        self._capabilities = [
            ModuleCapability(
                name="cursor.open",
                description="Open Cursor IDE, optionally with a specific folder or file",
                parameters={
                    "path": "Optional folder or file path to open"
                }
            ),
            ModuleCapability(
                name="cursor.new_file",
                description="Create a new file in a project",
                parameters={
                    "path": "Full path for the new file",
                    "content": "Optional initial content for the file"
                }
            ),
            ModuleCapability(
                name="cursor.open_file",
                description="Open a specific file in Cursor",
                parameters={
                    "path": "Path to the file to open"
                }
            ),
            ModuleCapability(
                name="cursor.run_terminal",
                description="Run a command in Cursor's integrated terminal",
                parameters={
                    "command": "Command to run",
                    "cwd": "Working directory"
                }
            ),
            ModuleCapability(
                name="cursor.git_status",
                description="Get git status of a project",
                parameters={
                    "path": "Path to the git repository"
                }
            ),
            ModuleCapability(
                name="cursor.git_commit",
                description="Commit changes in a git repository",
                parameters={
                    "path": "Path to the git repository",
                    "message": "Commit message"
                },
                requires_confirmation=True
            ),
            ModuleCapability(
                name="cursor.create_project",
                description="Create a new project folder with basic structure",
                parameters={
                    "name": "Project name",
                    "path": "Parent directory for the project",
                    "type": "Project type (python, node, basic)"
                }
            ),
        ]
    
    async def execute(self, action: str, params: dict[str, Any]) -> ActionResult:
        action_map = {
            "cursor.open": self._open_cursor,
            "open": self._open_cursor,
            "cursor.new_file": self._new_file,
            "new_file": self._new_file,
            "cursor.open_file": self._open_file,
            "open_file": self._open_file,
            "cursor.run_terminal": self._run_terminal,
            "run_terminal": self._run_terminal,
            "cursor.git_status": self._git_status,
            "git_status": self._git_status,
            "cursor.git_commit": self._git_commit,
            "git_commit": self._git_commit,
            "cursor.create_project": self._create_project,
            "create_project": self._create_project,
        }
        
        handler = action_map.get(action)
        if handler:
            return await handler(params)
        
        return ActionResult(
            status=ActionStatus.ERROR,
            message=f"Unknown action: {action}"
        )
    
    async def _open_cursor(self, params: dict[str, Any]) -> ActionResult:
        path = params.get("path", "")
        
        try:
            if platform.system() == "Windows":
                if os.path.exists(self.cursor_path):
                    if path:
                        subprocess.Popen([self.cursor_path, path])
                    else:
                        subprocess.Popen([self.cursor_path])
                    
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        message=f"Opened Cursor{' with ' + path if path else ''}",
                        data={"path": path}
                    )
                else:
                    result = subprocess.run(["where", "cursor"], capture_output=True, text=True)
                    if result.returncode == 0:
                        if path:
                            subprocess.Popen(["cursor", path], shell=True)
                        else:
                            subprocess.Popen(["cursor"], shell=True)
                        return ActionResult(
                            status=ActionStatus.SUCCESS,
                            message=f"Opened Cursor via CLI{' with ' + path if path else ''}",
                            data={"path": path}
                        )
                    
                    return ActionResult(
                        status=ActionStatus.ERROR,
                        message="Cursor not found. Please check the installation path."
                    )
            else:
                if path:
                    subprocess.Popen(["cursor", path])
                else:
                    subprocess.Popen(["cursor"])
                
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Opened Cursor{' with ' + path if path else ''}",
                    data={"path": path}
                )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to open Cursor: {str(e)}"
            )
    
    async def _new_file(self, params: dict[str, Any]) -> ActionResult:
        file_path = params.get("path", "")
        content = params.get("content", "")
        
        if not file_path:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="File path is required"
            )
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            path.write_text(content, encoding="utf-8")
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Created file: {file_path}",
                data={"path": str(path), "size": len(content)}
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to create file: {str(e)}"
            )
    
    async def _open_file(self, params: dict[str, Any]) -> ActionResult:
        file_path = params.get("path", "")
        
        if not file_path:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="File path is required"
            )
        
        if not os.path.exists(file_path):
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"File not found: {file_path}"
            )
        
        try:
            if platform.system() == "Windows":
                subprocess.Popen([self.cursor_path, file_path])
            else:
                subprocess.Popen(["cursor", file_path])
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Opened file in Cursor: {file_path}",
                data={"path": file_path}
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to open file: {str(e)}"
            )
    
    async def _run_terminal(self, params: dict[str, Any]) -> ActionResult:
        command = params.get("command", "")
        cwd = params.get("cwd", os.getcwd())
        
        if not command:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Command is required"
            )
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout or result.stderr or "Command completed"
            
            return ActionResult(
                status=ActionStatus.SUCCESS if result.returncode == 0 else ActionStatus.ERROR,
                message=output[:2000],
                data={
                    "command": command,
                    "cwd": cwd,
                    "return_code": result.returncode,
                    "stdout": result.stdout[:2000] if result.stdout else "",
                    "stderr": result.stderr[:2000] if result.stderr else ""
                }
            )
        
        except subprocess.TimeoutExpired:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Command timed out after 60 seconds"
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to run command: {str(e)}"
            )
    
    async def _git_status(self, params: dict[str, Any]) -> ActionResult:
        path = params.get("path", os.getcwd())
        
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Not a git repository or git error: {result.stderr}"
                )
            
            changes = result.stdout.strip().split("\n") if result.stdout.strip() else []
            
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path,
                capture_output=True,
                text=True
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Branch: {branch}\nChanges: {len(changes)} files",
                data={
                    "branch": branch,
                    "changes": changes,
                    "clean": len(changes) == 0
                }
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to get git status: {str(e)}"
            )
    
    async def _git_commit(self, params: dict[str, Any]) -> ActionResult:
        path = params.get("path", os.getcwd())
        message = params.get("message", "")
        
        if not message:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Commit message is required"
            )
        
        try:
            add_result = subprocess.run(
                ["git", "add", "-A"],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if add_result.returncode != 0:
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Failed to stage changes: {add_result.stderr}"
                )
            
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=path,
                capture_output=True,
                text=True
            )
            
            if commit_result.returncode != 0:
                if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        message="Nothing to commit, working tree clean",
                        data={"committed": False}
                    )
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Failed to commit: {commit_result.stderr}"
                )
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Committed: {message}",
                data={"committed": True, "message": message}
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to commit: {str(e)}"
            )
    
    async def _create_project(self, params: dict[str, Any]) -> ActionResult:
        name = params.get("name", "")
        parent_path = params.get("path", os.path.expanduser("~"))
        project_type = params.get("type", "basic")
        
        if not name:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Project name is required"
            )
        
        try:
            project_path = Path(parent_path) / name
            project_path.mkdir(parents=True, exist_ok=True)
            
            if project_type == "python":
                (project_path / "main.py").write_text('"""Main entry point."""\n\n\ndef main():\n    print("Hello, World!")\n\n\nif __name__ == "__main__":\n    main()\n')
                (project_path / "requirements.txt").write_text("")
                (project_path / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\nvenv/\n")
            
            elif project_type == "node":
                (project_path / "index.js").write_text('console.log("Hello, World!");\n')
                (project_path / "package.json").write_text('{\n  "name": "' + name + '",\n  "version": "1.0.0",\n  "main": "index.js"\n}\n')
                (project_path / ".gitignore").write_text("node_modules/\n.env\n")
            
            else:
                (project_path / "README.md").write_text(f"# {name}\n\nProject created by Jarvis.\n")
                (project_path / ".gitignore").write_text("")
            
            subprocess.run(["git", "init"], cwd=str(project_path), capture_output=True)
            
            if platform.system() == "Windows":
                subprocess.Popen([self.cursor_path, str(project_path)])
            else:
                subprocess.Popen(["cursor", str(project_path)])
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Created {project_type} project: {name}",
                data={
                    "name": name,
                    "path": str(project_path),
                    "type": project_type
                }
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to create project: {str(e)}"
            )
    
    async def get_state(self) -> dict[str, Any]:
        return {
            "cursor_path": self.cursor_path,
            "cursor_exists": os.path.exists(self.cursor_path) if platform.system() == "Windows" else True
        }
