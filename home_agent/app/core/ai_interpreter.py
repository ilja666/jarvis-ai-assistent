import json
import requests
from typing import Any, Optional
from app.core.config import settings
from app.core.registry import registry, dispatcher
from app.core.module_base import ActionResult, ActionStatus
from app.core.audit_log import audit_log


SYSTEM_PROMPT = """You are Jarvis, a personal AI assistant that controls a Windows PC and various applications.

You have access to the following modules and their capabilities:
{capabilities}

When the user gives you a request, you must:
1. Understand what they want to accomplish
2. Decide which module and action to use
3. Return a JSON response with your decision

IMPORTANT: Always respond with valid JSON in this exact format:
{{
    "thought": "Brief explanation of what you understood and why you chose this action",
    "action": {{
        "capability": "module.action_name",
        "params": {{}}
    }},
    "response": "What to tell the user"
}}

If you cannot fulfill the request or need clarification, use:
{{
    "thought": "Explanation of the issue",
    "action": null,
    "response": "Your response to the user explaining the situation"
}}

Available capabilities and their parameters:
{capability_details}

Be helpful, concise, and take action when possible. Don't ask for confirmation unless the action is dangerous."""


class AIInterpreter:
    def __init__(self):
        self.ollama_url = settings.ollama_url
        self.model = settings.ollama_model
        self.conversation_history: list[dict] = []
    
    def _get_capabilities_summary(self) -> str:
        caps = registry.list_capabilities()
        lines = []
        for module_name, cap_list in caps.items():
            module = registry.get(module_name)
            if module:
                lines.append(f"- {module_name}: {module.description}")
                for cap in cap_list:
                    lines.append(f"  - {cap}")
        return "\n".join(lines) if lines else "No modules loaded yet."
    
    def _get_capability_details(self) -> str:
        details = []
        for module in registry.get_enabled():
            for cap in module.capabilities:
                param_str = json.dumps(cap.parameters) if cap.parameters else "{}"
                details.append(f"- {cap.name}: {cap.description}")
                details.append(f"  Parameters: {param_str}")
                if cap.dangerous:
                    details.append("  WARNING: This action is dangerous and requires confirmation")
        return "\n".join(details) if details else "No capabilities available."
    
    def _build_system_prompt(self) -> str:
        return SYSTEM_PROMPT.format(
            capabilities=self._get_capabilities_summary(),
            capability_details=self._get_capability_details()
        )
    
    async def interpret(self, user_message: str, user_id: Optional[str] = None) -> dict[str, Any]:
        system_prompt = self._build_system_prompt()
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        messages_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}" 
            for msg in self.conversation_history[-5:]
        ])
        
        full_prompt = f"{system_prompt}\n\nConversation:\n{messages_text}\n\nRespond with JSON:"
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            
            if response.status_code != 200:
                return await self._fallback_interpret(user_message)
            
            ai_response = response.json().get("response", "")
            
            try:
                parsed = json.loads(ai_response)
            except json.JSONDecodeError:
                start = ai_response.find("{")
                end = ai_response.rfind("}") + 1
                if start != -1 and end > start:
                    parsed = json.loads(ai_response[start:end])
                else:
                    return await self._fallback_interpret(user_message)
            
            self.conversation_history.append({
                "role": "assistant",
                "content": parsed.get("response", "Done.")
            })
            
            audit_log.log_action(
                module="ai_interpreter",
                action="interpret",
                status="success",
                user_id=user_id,
                params={"message": user_message},
                result=json.dumps(parsed)
            )
            
            return parsed
            
        except requests.exceptions.RequestException as e:
            return await self._fallback_interpret(user_message)
        except Exception as e:
            return {
                "thought": f"Error: {str(e)}",
                "action": None,
                "response": f"Sorry, I encountered an error: {str(e)}"
            }
    
    async def _fallback_interpret(self, user_message: str) -> dict[str, Any]:
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["screenshot", "screen", "show me", "what's on"]):
            return {
                "thought": "User wants to see the screen",
                "action": {"capability": "system.screenshot", "params": {}},
                "response": "Taking a screenshot..."
            }
        
        if any(word in message_lower for word in ["open", "start", "launch", "run"]):
            for app in ["chrome", "firefox", "notepad", "cursor", "code", "word", "excel", "outlook", "cmd", "powershell"]:
                if app in message_lower:
                    return {
                        "thought": f"User wants to open {app}",
                        "action": {"capability": "windows.open_app", "params": {"app": app}},
                        "response": f"Opening {app}..."
                    }
        
        if any(word in message_lower for word in ["status", "how are you", "what's up"]):
            return {
                "thought": "User asking for status",
                "action": {"capability": "system.status", "params": {}},
                "response": "Checking system status..."
            }
        
        if any(word in message_lower for word in ["note", "remember", "save"]):
            return {
                "thought": "User wants to save a note",
                "action": {"capability": "system.add_note", "params": {"content": user_message}},
                "response": "Saving note..."
            }
        
        if any(word in message_lower for word in ["help", "what can you do", "capabilities"]):
            caps = self._get_capabilities_summary()
            return {
                "thought": "User asking for help",
                "action": None,
                "response": f"I can help you with:\n{caps}\n\nJust tell me what you want to do in natural language!"
            }
        
        return {
            "thought": "Could not determine intent, passing to AI for general response",
            "action": None,
            "response": f"I received your message: '{user_message}'. I'm not sure what action to take. Could you be more specific about what you'd like me to do?"
        }
    
    async def execute_interpreted(self, interpretation: dict[str, Any]) -> ActionResult:
        action = interpretation.get("action")
        
        if action is None:
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=interpretation.get("response", "No action needed."),
                data={"type": "message_only"}
            )
        
        capability = action.get("capability", "")
        params = action.get("params", {})
        
        result = await dispatcher.dispatch(capability, params)
        
        if result.status == ActionStatus.SUCCESS:
            result.message = interpretation.get("response", result.message)
        
        return result
    
    def clear_history(self) -> None:
        self.conversation_history = []


ai_interpreter = AIInterpreter()
