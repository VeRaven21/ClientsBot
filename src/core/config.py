from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    WORK_START_HOUR: int = 9
    WORK_END_HOUR: int = 18
    BOOKING_INTERVAL_MINUTES: int = 30

    model_config = {"env_file": ".env", "extra": "allow"}

    def get_admin_ids(self) -> List[int]:
        """Получить список ID администраторов"""
        if not self.ADMIN_IDS:
            return []
        return [int(id.strip()) for id in self.ADMIN_IDS.split(",") if id.strip()]


settings = Settings()
