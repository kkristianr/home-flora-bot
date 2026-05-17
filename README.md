# Telegram Bot for monitoring home plants

Self-hosted home plant monitoring with Xiaomi Mi Flora / Flower Care sensors.

It reads plant sensor data, stores local history, compares readings with OpenPlantbook care ranges, and shows a mobile-friendly Telegram bot UI for plant status and charts.

## What It Does

- Reads Mi Flora BLE sensors.
- Tracks temperature, moisture, conductivity, light, and battery.
- Stores readings locally.
- Uses OpenPlantbook min/max ranges for each plant.
- Shows plant pictures, status, and 1h / 24h / 7d charts in Telegram.
- Runs the infrastructure in Docker.

On macOS, the BLE reader runs locally because Docker Desktop does not expose the built-in Bluetooth adapter. On Raspberry Pi, the BLE reader can move into Docker later.

## Setup

Requirements:

- Docker Desktop
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Mi Flora / Flower Care sensor
- Telegram bot token and chat ID
- OpenPlantbook API key

Create `.env`:

```sh
cp .env.example .env
```

Fill in:

```sh
OPENPLANTBOOK_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

Install dependencies:

```sh
make bootstrap
```

Scan for sensors:

```sh
make scan
```

Configure plants in `config/plants.json`:

```json
{
  "slug": "ficus-lyrata",
  "name": "Ficus lyrata",
  "plant_id": "ficus lyrata",
  "sensor_address": "18B2C760-2C41-F033-BA87-9A5849CA1BD1"
}
```

Start reading the sensor:

```sh
make stream
```

Start the bot:

```sh
make bot-up
```

In Telegram:

```text
/plants
```

## Useful Commands

```sh
make mqtt-up      # start MQTT
make mqtt-tail    # inspect readings
make bot-logs     # inspect bot logs
make lint         # ruff check
make format       # ruff format + safe fixes
```

## Built On

- [ThomDietrich/miflora-mqtt-daemon](https://github.com/ThomDietrich/miflora-mqtt-daemon), as the main reference for Mi Flora + MQTT workflows.
- [basnijholt/miflora](https://github.com/basnijholt/miflora), as part of the Mi Flora Python ecosystem.
- [Bleak](https://github.com/hbldh/bleak), for macOS BLE access.
- [OpenPlantbook](https://open.plantbook.io), for plant care ranges and images.

Most of the code in this project was written with AI assistance.
