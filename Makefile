ADDRESS ?=
PLANT ?= ficus-lyrata

.PHONY: bootstrap lint format mqtt-up mqtt-down mqtt-tail bot-up bot-logs scan stream

bootstrap:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

mqtt-up:
	docker compose up -d mqtt

mqtt-down:
	docker compose down

mqtt-tail:
	docker compose run --rm mqtt-tail

bot-up:
	docker compose up -d --build bot

bot-logs:
	docker compose logs -f bot

scan:
	uv run python scripts/miflora_ble_probe.py scan

stream: mqtt-up
	uv run python scripts/miflora_ble_probe.py stream $(ADDRESS) --plant "$(PLANT)"
