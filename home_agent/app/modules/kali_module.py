import os
from typing import Any, Optional
import socket

from app.core.module_base import ModuleBase, ModuleCapability, ActionResult, ActionStatus
from app.core.config import settings


class KaliModule(ModuleBase):
    name = "kali"
    description = "Kali Linux VM control via SSH: run commands, manage tools, security testing"
    version = "1.0.0"
    
    def __init__(self):
        super().__init__()
        self.host = settings.kali_host
        self.user = settings.kali_user
        self.password = settings.kali_password
        self.port = settings.kali_port
        self._client = None
    
    def _register_capabilities(self) -> None:
        self._capabilities = [
            ModuleCapability(
                name="kali.run_command",
                description="Run a command on the Kali VM via SSH",
                parameters={
                    "command": "Command to execute on Kali"
                },
                requires_confirmation=True,
                dangerous=True
            ),
            ModuleCapability(
                name="kali.check_connection",
                description="Check if Kali VM is reachable via SSH",
                parameters={}
            ),
            ModuleCapability(
                name="kali.list_tools",
                description="List available security tools on Kali",
                parameters={}
            ),
            ModuleCapability(
                name="kali.start_service",
                description="Start a service on Kali (e.g., apache2, ssh, postgresql)",
                parameters={
                    "service": "Service name to start"
                },
                requires_confirmation=True
            ),
            ModuleCapability(
                name="kali.get_ip",
                description="Get the IP address of the Kali VM",
                parameters={}
            ),
        ]
    
    def _get_ssh_client(self):
        try:
            import paramiko
            
            if self._client is None or not self._client.get_transport() or not self._client.get_transport().is_active():
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.user,
                    password=self.password,
                    timeout=10
                )
            
            return self._client
        except ImportError:
            raise Exception("paramiko not installed")
        except Exception as e:
            raise Exception(f"SSH connection failed: {str(e)}")
    
    async def execute(self, action: str, params: dict[str, Any]) -> ActionResult:
        action_map = {
            "kali.run_command": self._run_command,
            "run_command": self._run_command,
            "kali.check_connection": self._check_connection,
            "check_connection": self._check_connection,
            "kali.list_tools": self._list_tools,
            "list_tools": self._list_tools,
            "kali.start_service": self._start_service,
            "start_service": self._start_service,
            "kali.get_ip": self._get_ip,
            "get_ip": self._get_ip,
        }
        
        handler = action_map.get(action)
        if handler:
            return await handler(params)
        
        return ActionResult(
            status=ActionStatus.ERROR,
            message=f"Unknown action: {action}"
        )
    
    async def _run_command(self, params: dict[str, Any]) -> ActionResult:
        command = params.get("command", "")
        
        if not command:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Command is required"
            )
        
        if not self.host:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Kali host not configured. Set KALI_HOST in .env file."
            )
        
        try:
            client = self._get_ssh_client()
            
            stdin, stdout, stderr = client.exec_command(command, timeout=60)
            
            output = stdout.read().decode("utf-8")
            error = stderr.read().decode("utf-8")
            exit_code = stdout.channel.recv_exit_status()
            
            result_text = output or error or "Command completed"
            
            return ActionResult(
                status=ActionStatus.SUCCESS if exit_code == 0 else ActionStatus.ERROR,
                message=result_text[:2000],
                data={
                    "command": command,
                    "stdout": output[:2000],
                    "stderr": error[:2000],
                    "exit_code": exit_code
                }
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to run command on Kali: {str(e)}"
            )
    
    async def _check_connection(self, params: dict[str, Any]) -> ActionResult:
        if not self.host:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Kali host not configured. Set KALI_HOST in .env file.",
                data={"configured": False}
            )
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result != 0:
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Cannot reach Kali at {self.host}:{self.port}. Is the VM running and SSH enabled?",
                    data={"reachable": False, "host": self.host, "port": self.port}
                )
            
            client = self._get_ssh_client()
            stdin, stdout, stderr = client.exec_command("echo 'connected'")
            output = stdout.read().decode("utf-8").strip()
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Connected to Kali at {self.host}:{self.port}",
                data={"reachable": True, "host": self.host, "port": self.port, "authenticated": True}
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Connection check failed: {str(e)}",
                data={"reachable": False, "error": str(e)}
            )
    
    async def _list_tools(self, params: dict[str, Any]) -> ActionResult:
        common_tools = [
            "nmap", "nikto", "burpsuite", "metasploit", "sqlmap",
            "hydra", "john", "hashcat", "aircrack-ng", "wireshark",
            "gobuster", "dirb", "wfuzz", "ffuf", "nuclei"
        ]
        
        if not self.host:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Kali not connected. Common tools include:\n" + ", ".join(common_tools),
                data={"tools": common_tools, "verified": False}
            )
        
        try:
            client = self._get_ssh_client()
            
            available = []
            for tool in common_tools:
                stdin, stdout, stderr = client.exec_command(f"which {tool}")
                if stdout.read().decode("utf-8").strip():
                    available.append(tool)
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Available tools: {', '.join(available)}",
                data={"tools": available, "verified": True}
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to list tools: {str(e)}"
            )
    
    async def _start_service(self, params: dict[str, Any]) -> ActionResult:
        service = params.get("service", "")
        
        if not service:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Service name is required"
            )
        
        if not self.host:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Kali host not configured"
            )
        
        try:
            client = self._get_ssh_client()
            
            stdin, stdout, stderr = client.exec_command(f"sudo systemctl start {service}")
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code == 0:
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message=f"Started service: {service}",
                    data={"service": service, "started": True}
                )
            else:
                error = stderr.read().decode("utf-8")
                return ActionResult(
                    status=ActionStatus.ERROR,
                    message=f"Failed to start {service}: {error}",
                    data={"service": service, "started": False}
                )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to start service: {str(e)}"
            )
    
    async def _get_ip(self, params: dict[str, Any]) -> ActionResult:
        if not self.host:
            return ActionResult(
                status=ActionStatus.ERROR,
                message="Kali host not configured"
            )
        
        try:
            client = self._get_ssh_client()
            
            stdin, stdout, stderr = client.exec_command("hostname -I | awk '{print $1}'")
            ip = stdout.read().decode("utf-8").strip()
            
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"Kali IP: {ip}",
                data={"ip": ip, "configured_host": self.host}
            )
        
        except Exception as e:
            return ActionResult(
                status=ActionStatus.ERROR,
                message=f"Failed to get IP: {str(e)}"
            )
    
    async def get_state(self) -> dict[str, Any]:
        connection_result = await self._check_connection({})
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "configured": bool(self.host),
            "connected": connection_result.status == ActionStatus.SUCCESS
        }
    
    def __del__(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
