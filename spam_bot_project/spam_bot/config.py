from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str
    admin_telegram_ids: str = ""

    # Railway/Render kabi platformalar odatda bitta tayyor ulanish qatorini
    # (DATABASE_URL) beradi; berilgan bo'lsa, quyidagi POSTGRES_* qiymatlaridan
    # ustun turadi.
    database_url_override: str = Field(default="", validation_alias="DATABASE_URL")

    postgres_db: str = ""
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Har bir guruhning Gemini API kalitini shifrlash uchun Fernet kaliti.
    # Yaratish: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    key_encryption_secret: str

    # Botning ommaviy HTTPS manzili, /setkey bir martalik havolasini yaratish uchun.
    base_url: str = ""
    web_host: str = "0.0.0.0"
    # Railway kabi platformalar portni "PORT" nomi bilan beradi.
    web_port: int = Field(default=8080, validation_alias=AliasChoices("WEB_PORT", "PORT"))

    gemini_model: str = "gemini-2.5-flash"
    gemini_price_in: float = 0.30
    gemini_price_out: float = 2.50

    # Bitta operator bo'lmagan foydalanuvchi botni admin qilib qo'sha oladigan
    # maksimal guruhlar soni (suiiste'moldan himoya).
    max_groups_per_owner: int = 20

    # Yangi guruh uchun bepul sinov muddati (kun).
    trial_days: int = 3
    # Bir marta to'lov bilan uzaytiriladigan obuna davri (kun).
    subscription_period_days: int = 30
    # Obuna narxi, Telegram Stars'da (valyuta "XTR", tashqi to'lov tizimi shart emas).
    subscription_price_stars: int = 100

    # Ertalabki hisobot yuboriladigan mahalliy soat (Asia/Tashkent).
    report_hour: int = 9

    # Spam hisobot matnlari va foydalanish yozuvlarini necha kundan keyin tozalash.
    retention_days: int = 90

    log_level: str = "INFO"
    tz: str = "Asia/Tashkent"

    @property
    def admin_id_list(self) -> list[int]:
        return [int(x) for x in self.admin_telegram_ids.split(",") if x.strip()]

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            url = self.database_url_override
            # Railway/Heroku "postgres://" beradi; SQLAlchemy+asyncpg
            # "postgresql+asyncpg://" ko'rinishini kutadi.
            if url.startswith("postgres://"):
                url = "postgresql://" + url[len("postgres://") :]
            if url.startswith("postgresql://"):
                url = "postgresql+asyncpg://" + url[len("postgresql://") :]
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
