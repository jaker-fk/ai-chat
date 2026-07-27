from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
ENV = dotenv_values(ENV_PATH)


@dataclass(frozen=True)
class Settings:
    app_name: str = ENV.get("APP_NAME", "AI对话应用")
    database_url: str = ENV.get("DATABASE_URL", "")
    jwt_secret: str = ENV.get("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = ENV.get("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(ENV.get("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

    response_success_code: int = int(ENV.get("RESPONSE_SUCCESS_CODE", "0"))
    response_default_success_message: str = ENV.get("RESPONSE_DEFAULT_SUCCESS_MESSAGE", "success")
    response_default_error_message: str = ENV.get("RESPONSE_DEFAULT_ERROR_MESSAGE", "error")

    openai_api_key: str | None = ENV.get("OPENAI_API_KEY")
    openai_base_url: str = ENV.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = ENV.get("OPENAI_MODEL", "gpt-4o-mini")
    deepseek_api_key: str | None = ENV.get("DEEPSEEK_API_KEY")
    deepseek_base_url: str = ENV.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = ENV.get("DEEPSEEK_MODEL", "deepseek-chat")


settings = Settings()