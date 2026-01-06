import os
import asyncio
import logging
from typing import Optional
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from app.core.config import settings
from app.core.registry import registry
from app.core.audit_log import audit_log
from app.core.ai_interpreter import ai_interpreter
from app.core.module_base import ActionStatus

from app.modules.system_module import SystemModule
from app.modules.windows_module import WindowsModule
from app.modules.cursor_module import CursorModule
from app.modules.kali_module import KaliModule

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

AUTHORIZED_USER_ID: Optional[int] = settings.authorized_user_id

PENDING_CONFIRMATIONS: dict[int, dict] = {}


def register_modules():
    if not registry.get("system"):
        registry.register(SystemModule())
    if not registry.get("windows"):
        registry.register(WindowsModule())
    if not registry.get("cursor"):
        registry.register(CursorModule())
    if not registry.get("kali"):
        registry.register(KaliModule())
    logger.info(f"Registered {len(registry.get_all())} modules for Telegram bot")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global AUTHORIZED_USER_ID
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if AUTHORIZED_USER_ID is None:
        AUTHORIZED_USER_ID = user_id
        audit_log.log_action(
            module="telegram",
            action="authorize",
            status="success",
            user_id=str(user_id),
            result=f"User {user_name} authorized as owner"
        )
        await update.message.reply_text(
            f"Jarvis online, {user_name}. You are now the authorized owner.\n\n"
            "Just tell me what you want to do in natural language. For example:\n"
            "- 'Take a screenshot'\n"
            "- 'Open Chrome'\n"
            "- 'What's the system status?'\n"
            "- 'Create a new Python project called myapp'\n\n"
            "I'll understand and execute your requests."
        )
    elif user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Access denied.")
        audit_log.log_action(
            module="telegram",
            action="access_denied",
            status="error",
            user_id=str(user_id)
        )
        return
    else:
        await update.message.reply_text(
            f"Jarvis ready, {user_name}. What can I do for you?"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global AUTHORIZED_USER_ID
    user_id = update.effective_user.id
    
    if AUTHORIZED_USER_ID is None:
        await update.message.reply_text("Please send /start first to initialize Jarvis.")
        return
    
    if user_id != AUTHORIZED_USER_ID:
        return
    
    message_text = update.message.text.strip()
    
    if user_id in PENDING_CONFIRMATIONS:
        pending = PENDING_CONFIRMATIONS[user_id]
        if message_text.lower() in ["yes", "y", "confirm", "ok", "do it"]:
            del PENDING_CONFIRMATIONS[user_id]
            
            from app.core.registry import dispatcher
            result = await dispatcher.dispatch(pending["capability"], pending["params"])
            
            audit_log.log_action(
                module="telegram",
                action=pending["capability"],
                status=result.status,
                user_id=str(user_id),
                params=pending["params"],
                result=result.message
            )
            
            await send_result(update, result)
            return
        
        elif message_text.lower() in ["no", "n", "cancel", "abort"]:
            del PENDING_CONFIRMATIONS[user_id]
            await update.message.reply_text("Action cancelled.")
            return
    
    await update.message.reply_text("Processing...")
    
    try:
        interpretation = await ai_interpreter.interpret(
            message_text,
            user_id=str(user_id)
        )
        
        thought = interpretation.get("thought", "")
        response = interpretation.get("response", "")
        action = interpretation.get("action")
        
        if action:
            capability = action.get("capability", "")
            params = action.get("params", {})
            
            cap_info = registry.find_capability(capability)
            if cap_info:
                module, _ = cap_info
                cap = module.get_capability(capability)
                
                if cap and cap.requires_confirmation:
                    PENDING_CONFIRMATIONS[user_id] = {
                        "capability": capability,
                        "params": params
                    }
                    
                    warning = " (DANGEROUS)" if cap.dangerous else ""
                    await update.message.reply_text(
                        f"{response}\n\n"
                        f"This action requires confirmation{warning}.\n"
                        f"Reply 'yes' to proceed or 'no' to cancel."
                    )
                    return
            
            result = await ai_interpreter.execute_interpreted(interpretation)
            
            audit_log.log_action(
                module="telegram",
                action=capability,
                status=result.status,
                user_id=str(user_id),
                params=params,
                result=result.message
            )
            
            await send_result(update, result, response)
        
        else:
            await update.message.reply_text(response)
    
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(f"Sorry, an error occurred: {str(e)}")


async def send_result(update: Update, result, ai_response: str = None) -> None:
    message = ai_response or result.message
    
    if result.status == ActionStatus.ERROR:
        message = f"Error: {result.message}"
    
    if result.screenshot_path and os.path.exists(result.screenshot_path):
        try:
            with open(result.screenshot_path, "rb") as photo:
                await update.message.reply_photo(photo, caption=message[:1024])
            
            try:
                os.remove(result.screenshot_path)
            except Exception:
                pass
        except Exception as e:
            await update.message.reply_text(f"{message}\n\n(Failed to send screenshot: {e})")
    else:
        if result.data:
            data_preview = str(result.data)[:500]
            if len(data_preview) < len(str(result.data)):
                data_preview += "..."
            message = f"{message}\n\nDetails: {data_preview}"
        
        if len(message) > 4096:
            for i in range(0, len(message), 4096):
                await update.message.reply_text(message[i:i+4096])
        else:
            await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if AUTHORIZED_USER_ID is not None and user_id != AUTHORIZED_USER_ID:
        return
    
    modules_info = []
    for module in registry.get_enabled():
        caps = [f"  - {cap.name}: {cap.description}" for cap in module.capabilities[:3]]
        if len(module.capabilities) > 3:
            caps.append(f"  - ... and {len(module.capabilities) - 3} more")
        modules_info.append(f"\n{module.name}: {module.description}\n" + "\n".join(caps))
    
    help_text = (
        "Jarvis AI Assistant\n\n"
        "Just tell me what you want in natural language!\n\n"
        "Examples:\n"
        "- 'Take a screenshot'\n"
        "- 'Open Chrome and go to google.com'\n"
        "- 'What apps are running?'\n"
        "- 'Create a new project called myapp'\n"
        "- 'Check Kali connection'\n"
        "- 'Save a note: remember to update the docs'\n\n"
        "Available modules:" + "".join(modules_info)
    )
    
    await update.message.reply_text(help_text)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if AUTHORIZED_USER_ID is not None and user_id != AUTHORIZED_USER_ID:
        return
    
    system_module = registry.get("system")
    if system_module:
        result = await system_module.execute("status", {})
        await send_result(update, result)
    else:
        await update.message.reply_text("System module not available")


async def modules_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if AUTHORIZED_USER_ID is not None and user_id != AUTHORIZED_USER_ID:
        return
    
    modules_list = []
    for module in registry.get_all():
        status = "enabled" if module.enabled else "disabled"
        caps_count = len(module.capabilities)
        modules_list.append(f"- {module.name} ({status}): {caps_count} capabilities")
    
    await update.message.reply_text(
        "Loaded modules:\n\n" + "\n".join(modules_list)
    )


def run_telegram_bot():
    register_modules()
    
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        return
    
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("modules", modules_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Starting Jarvis Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_telegram_bot()
