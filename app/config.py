from dataclasses import dataclass
import os


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    bot_token: str
    database_url: str
    daylight_start_hour: int = 8
    daylight_end_hour: int = 20
    debug: bool = False

    @classmethod
    def load(cls, require_bot_token: bool = True) -> "Settings":
        bot_token = os.environ.get("BOT_TOKEN")
        if require_bot_token and not bot_token:
            raise RuntimeError("BOT_TOKEN is required")
        bot_token_value = bot_token or ""

        database_url = os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/tarobot",
        )
        daylight_start_hour = _env_int("DAYLIGHT_START_HOUR", 8)
        daylight_end_hour = _env_int("DAYLIGHT_END_HOUR", 20)
        debug = _env_bool("DEBUG", False)

        return cls(
            bot_token=bot_token_value,
            database_url=database_url,
            daylight_start_hour=daylight_start_hour,
            daylight_end_hour=daylight_end_hour,
            debug=debug,
        )


settings = Settings.load()
