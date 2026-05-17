# Architecture

Goal: self-hosted plant monitor with local history, Telegram alerts, and care thresholds from OpenPlantbook.

## Current Mac Setup

Docker runs infrastructure:

- Mosquitto MQTT broker
- Telegram bot
- SQLite history volume

macOS reads BLE natively with `bleak`, because Docker Desktop on Mac does not expose the built-in Bluetooth adapter to Linux containers.

Current data flow:

```text
Mi Flora sensor -> Python BLE reader -> MQTT -> SQLite -> Telegram bot
```

## Code Boundaries

The Telegram bot is split by responsibility:

- `flora.settings`: environment-backed runtime settings
- `flora.plants`: local plant registry from `config/plants.json`
- `flora.storage`: SQLite schema, readings, and OpenPlantbook cache
- `flora.openplantbook`: OpenPlantbook HTTP client
- `flora.mqtt_ingest`: MQTT subscription and reading persistence
- `flora.status`: green/orange/red status evaluation and compact plant card text
- `flora.charting`: 7-day charts with plant-specific target bands
- `flora.telegram_bot`: Telegram commands and callbacks

The BLE reader remains a small Mac-first script under `scripts/` until Raspberry Pi migration. It publishes plain MQTT readings and does not know about Telegram, charts, or OpenPlantbook.

## Raspberry Pi Setup

On Raspberry Pi, the same services can run in Docker. The BLE reader can also move into Docker because Linux exposes Bluetooth devices through BlueZ.

Expected data flow:

```text
Mi Flora sensor -> Docker BLE reader -> MQTT -> database -> Telegram bot
```

## Plant Metadata

Local plant assignments live in `config/plants.json`.

The current sensor is assigned to OpenPlantbook plant ID:

```text
ficus lyrata
```

OpenPlantbook is used for plant care thresholds via:

- `plant/search`
- `plant/detail`

API-key authentication is enough for these read-only endpoints. Store the token in `.env` as `OPENPLANTBOOK_API_KEY`.

## Next Build Steps

1. Send Telegram alerts when readings are outside range.
2. Add tests for `flora.status`, `flora.storage`, and MQTT payload ingestion.
3. Move BLE reader into Docker on Raspberry Pi.
