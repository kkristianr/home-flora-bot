import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    plants_config: Path
    db_path: Path
    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    openplantbook_api_key: str
    openplantbook_base_url: str
    telegram_bot_token: str
    telegram_chat_id: str | None


def load_settings() -> Settings:
    return Settings(
        plants_config=Path(os.environ.get("PLANTS_CONFIG", "config/plants.json")),
        db_path=Path(os.environ.get("DB_PATH", "/data/flora.sqlite")),
        mqtt_host=os.environ.get("MQTT_HOST", "mqtt"),
        mqtt_port=int(os.environ.get("MQTT_PORT", "1883")),
        mqtt_topic=os.environ.get("MQTT_TOPIC", "miflora/#"),
        openplantbook_api_key=os.environ.get("OPENPLANTBOOK_API_KEY", ""),
        openplantbook_base_url=os.environ.get("OPENPLANTBOOK_BASE_URL", "https://open.plantbook.io/api/v1"),
        telegram_bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID"),
    )
