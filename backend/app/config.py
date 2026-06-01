from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://zhalobi_user:zhalobi_pass@localhost:5432/zhalobi"
    secret_key: str = "zhalobi-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    escalation_hours: int = 72

    class Config:
        env_file = ".env"


settings = Settings()
