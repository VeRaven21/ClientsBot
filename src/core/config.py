from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    BOT_TOKEN: str

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
