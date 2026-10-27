"""配置类，应用配置，get_settings只实例化一次"""

from pydantic_settings import BaseSettings,SettingsConfigDict

from functools import lru_cache

class Settings(BaseSettings):

    """配置规则"""
    model_config=SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    """具体配置项和规则"""
    llm_api_key:str=""
    llm_base_url:str="https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_timeout_seconds: float = 90.0
    jwt_secret: str = "dev-only-secret-change-me"

@lru_cache
def get_settings() ->  Settings:
    """自动缓存输入参数和结果"""
    return Settings()


