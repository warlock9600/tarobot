from dataclasses import dataclass
import os


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass
class Settings:
    bot_token: str
    database_url: str
    daylight_start_hour: int = 8
    daylight_end_hour: int = 20

    @classmethod
    def load(cls) -> "Settings":
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            raise RuntimeError("BOT_TOKEN is required")

        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/tarobot",
        )
        daylight_start_hour = _env_int("DAYLIGHT_START_HOUR", 8)
        daylight_end_hour = _env_int("DAYLIGHT_END_HOUR", 20)

        return cls(
            bot_token=bot_token,
            database_url=database_url,
            daylight_start_hour=daylight_start_hour,
            daylight_end_hour=daylight_end_hour,
        )


settings = Settings.load()
