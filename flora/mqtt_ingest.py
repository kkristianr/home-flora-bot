import json
import logging

import paho.mqtt.client as mqtt

from .settings import Settings
from .storage import Storage

logger = logging.getLogger(__name__)


def plant_slug_from_topic(topic: str) -> str | None:
    parts = topic.split("/")
    if len(parts) >= 2 and parts[0] == "miflora":
        return parts[1]
    return None


class MqttIngestor:
    def __init__(self, settings: Settings, storage: Storage):
        self.settings = settings
        self.storage = storage

    def start(self) -> mqtt.Client:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect(self.settings.mqtt_host, self.settings.mqtt_port, keepalive=60)
        client.loop_start()
        return client

    def _on_connect(self, client, userdata, flags, reason_code, properties) -> None:
        logger.info("Connected to MQTT: %s", reason_code)
        client.subscribe(self.settings.mqtt_topic)

    def _on_message(self, client, userdata, message) -> None:
        slug = plant_slug_from_topic(message.topic)
        if not slug:
            return

        try:
            data = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            logger.warning("Ignoring non-JSON MQTT payload on %s", message.topic)
            return

        if "error" in data:
            return

        self.storage.save_reading(slug, data)
        logger.info("Stored reading for %s", slug)
