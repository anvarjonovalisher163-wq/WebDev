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

    # Email orqali kirish (magic-link) - SMTP orqali yuboriladi. Bo'sh
    # bo'lsa, login sahifasida email tugmasi "tez orada" deb ko'rsatiladi.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Google orqali kirish (OAuth 2.0). Google Cloud Console'da yaratilgan
    # ilovaning ma'lumotlari. Bo'sh bo'lsa, tugma "tez orada" ko'rsatiladi.
    google_client_id: str = ""
    google_client_secret: str = ""

    # Telefon raqam orqali kirish (SMS OTP) - Eskiz.uz orqali. Bo'sh bo'lsa,
    # tugma "tez orada" ko'rsatiladi.
    eskiz_email: str = ""
    eskiz_password: str = ""

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    @property
    def google_oauth_configured(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def eskiz_configured(self) -> bool:
        return bool(self.eskiz_email and self.eskiz_password)

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
