from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    super_admin_ids: str = ""

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # "redis" (production, docker-compose) yoki "memory" (Redis'siz lokal test uchun;
    # FSM holatlari bot qayta ishga tushganda yo'qoladi).
    storage_backend: str = "redis"

    log_level: str = "INFO"

    # Reyting Mini App manzili (https://domen.uz kabi). Bo'sh bo'lsa, "🏆 Reyting"
    # tugmasi Mini App o'rniga oddiy matnli reytingni chiqaradi.
    webapp_url: str = ""

    @property
    def super_admin_id_list(self) -> list[int]:
        return [int(x) for x in self.super_admin_ids.split(",") if x.strip()]

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
