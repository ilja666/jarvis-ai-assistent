import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Jarvis Home Agent"
    debug: bool = False
    
    telegram_bot_token: Optional[str] = None
    authorized_user_id: Optional[int] = None
    
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    kali_host: Optional[str] = None
    kali_user: str = "kali"
    kali_password: Optional[str] = None
    kali_port: int = 22
    
    cursor_path: str = r"C:\Users\Ilja\AppData\Local\Programs\cursor\Cursor.exe"
    
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
