from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    app_name: str = "RWS Chat"
    debug: bool = False
    people_csv_path: Path = APP_DIR / "data" / "people.csv"
    regions_path: Path = APP_DIR / "data" / "regions.json"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
