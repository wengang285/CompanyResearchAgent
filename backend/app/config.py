"""应用配置管理"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # LLM Configuration (OpenAI Compatible)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    
    # Serper API
    serper_api_key: str = ""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./research.db"
    
    # App Config
    debug: bool = True
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"
    
    # PDF Font
    pdf_font_path: str = "C:/Windows/Fonts/msyh.ttc"
    pdf_font_name: str = "MicrosoftYaHei"
    
    # Auth
    secret_key: str = "your-secret-key-please-change-in-production-env"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()



