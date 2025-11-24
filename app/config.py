from pydantic_settings import BaseSettings, SettingsConfigDict

_base_config = SettingsConfigDict(
        env_file="./.env",
        env_ignore_empty=True,
        extra="ignore"
    )

class AppSettings(BaseSettings):
    APP_NAME: str = "FastShip"
    APP_DOMAIN: str = "localhost:8000"

class DatabaseSettings(BaseSettings):
    POSTGRES_USER : str
    POSTGRES_PASSWORD : str
    POSTGRES_SERVER : str
    POSTGRES_PORT : int
    POSTGRES_DB : str

    REDIS_HOST : str
    REDIS_PORT : str
    
    model_config = _base_config

    @property
    def POSTGRES_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    def REDIS_URL(self, db):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{db}"
    
class SecuritySettings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str

    model_config = _base_config

class NotificationSettings(BaseSettings):

    MAIL_USERNAME : str
    MAIL_PASSWORD : str
    MAIL_FROM : str
    MAIL_FROM_NAME : str
    MAIL_SERVER : str
    MAIL_PORT : int
    MAIL_STARTTLS : bool
    MAIL_SSL_TLS : bool
    USE_CREDENTIALS : bool

    TWILIO_SID : str
    TWILIO_AUTH_TOKEN : str
    TWILIO_NUMBER : str

    model_config = _base_config

    def email_config(self) -> dict:
        # connection config expects these exact keys; return only them
        return {
            "MAIL_USERNAME": self.MAIL_USERNAME,
            "MAIL_PASSWORD": self.MAIL_PASSWORD,
            "MAIL_FROM": self.MAIL_FROM,
            "MAIL_FROM_NAME": self.MAIL_FROM_NAME,
            "MAIL_SERVER": self.MAIL_SERVER,
            "MAIL_PORT": self.MAIL_PORT,
            "MAIL_STARTTLS": self.MAIL_STARTTLS,
            "MAIL_SSL_TLS": self.MAIL_SSL_TLS,
            "USE_CREDENTIALS": self.USE_CREDENTIALS,
        }

app_settings = AppSettings()
db_settings = DatabaseSettings()
security_settings = SecuritySettings()
notification_settings = NotificationSettings()