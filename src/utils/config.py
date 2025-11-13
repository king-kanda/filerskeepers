"""Configuration management using Pydantic settings."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # MongoDB
    mongodb_url: str = Field(default="mongodb://localhost:27017")
    mongodb_db_name: str = Field(default="books_scraper")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_keys: str = Field(default="dev-key-1,dev-key-2")

    # Rate Limiting
    rate_limit_per_hour: int = Field(default=100)

    # Crawler
    target_url: str = Field(default="https://books.toscrape.com")
    max_concurrent_requests: int = Field(default=10)
    request_timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    retry_delay: int = Field(default=2)

    # Scheduler
    crawl_schedule_hour: int = Field(default=2)
    crawl_schedule_minute: int = Field(default=0)

    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/app.log")

    # Email Alerts (Optional)
    smtp_host: str = Field(default="smtp.gmail.com")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    alert_email: str = Field(default="")

    @property
    def api_keys_list(self) -> List[str]:
        """Parse API keys from comma-separated string."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def email_alerts_enabled(self) -> bool:
        """Check if email alerts are configured."""
        return bool(self.smtp_user and self.smtp_password and self.alert_email)


# Global settings instance
settings = Settings()
