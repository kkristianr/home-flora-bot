#!/usr/bin/env python3
import argparse
import asyncio
import json
import re
import struct
from datetime import UTC, datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

ROOT_SERVICE = "0000fe95-0000-1000-8000-00805f9b34fb"
CMD_CHAR = "00001a00-0000-1000-8000-00805f9b34fb"
DATA_CHAR = "00001a01-0000-1000-8000-00805f9b34fb"
FIRMWARE_CHAR = "00001a02-0000-1000-8000-00805f9b34fb"
REALTIME_MODE = bytes.fromhex("a01f")
SCAN_SECONDS = 10
POLL_SECONDS = 15
MQTT_HOST = "localhost"
MQTT_PORT = 1883
CONFIG_PATH = Path("config/plants.json")


def utc_now():
    return datetime.now(UTC).isoformat()


def looks_like_miflora(device, advertisement_data):
    name = device.name or advertisement_data.local_name or ""
    service_uuids = [uuid.lower() for uuid in advertisement_data.service_uuids]
    return "flower care" in name.lower() or ROOT_SERVICE in service_uuids


async def scan():
    print(f"Scanning for BLE devices for {SCAN_SECONDS} seconds...", flush=True)
    found = {}

    def on_detection(device, advertisement_data):
        if looks_like_miflora(device, advertisement_data):
            found[device.address] = (device, advertisement_data)

    scanner = BleakScanner(on_detection)
    await scanner.start()
    await asyncio.sleep(SCAN_SECONDS)
    await scanner.stop()

    if not found:
        print("No Flower care sensor found.")
        return

    for device, advertisement_data in found.values():
        name = device.name or advertisement_data.local_name or "(no name)"
        rssi = getattr(advertisement_data, "rssi", None)
        print(f"{device.address}\t{name}\trssi={rssi}")


def parse_measurement(raw):
    if len(raw) < 10:
        raise ValueError(f"Expected at least 10 bytes from sensor data characteristic, got {len(raw)}")

    temperature_raw = struct.unpack_from("<h", raw, 0)[0]
    light = struct.unpack_from("<I", raw, 3)[0]
    moisture = raw[7]
    conductivity = struct.unpack_from("<H", raw, 8)[0]

    return {
        "light": light,
        "moisture": moisture,
        "temperature": round(temperature_raw / 10, 1),
        "conductivity": conductivity,
    }


def topic_name(text):
    return re.sub(r"[^a-z0-9_-]+", "-", text.strip().lower()).strip("-") or "plant"


def load_plant(slug):
    with CONFIG_PATH.open() as config_file:
        plants = json.load(config_file)["plants"]

    if slug is None:
        return plants[0]

    for plant in plants:
        if plant["slug"] == slug:
            return plant

    raise SystemExit(f'Plant "{slug}" not found in {CONFIG_PATH}')


async def first_miflora_address():
    found = []

    def on_detection(device, advertisement_data):
        if looks_like_miflora(device, advertisement_data):
            found.append(device)

    scanner = BleakScanner(on_detection)
    await scanner.start()
    await asyncio.sleep(SCAN_SECONDS)
    await scanner.stop()

    if not found:
        raise RuntimeError(
            "No Flower care sensor found. Run `make scan` and pass the address to `make stream ADDRESS=...`."
        )

    return found[0].address


async def read_once(address):
    async with BleakClient(address) as client:
        battery_raw = await client.read_gatt_char(FIRMWARE_CHAR)
        await client.write_gatt_char(CMD_CHAR, REALTIME_MODE, response=True)
        measurement_raw = await client.read_gatt_char(DATA_CHAR)

    data = parse_measurement(measurement_raw)
    data["battery"] = battery_raw[0] if battery_raw else None
    data["timestamp"] = utc_now()
    return data


def publish_mqtt(topic, payload):
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
    client.publish(topic, json.dumps(payload))
    client.disconnect()


async def stream(plant_slug, address):
    plant = load_plant(plant_slug)
    address = address or plant.get("sensor_address") or await first_miflora_address()
    topic = f"miflora/{topic_name(plant['slug'])}"
    print(f"Using BLE address/id: {address}")
    print(f"Plant: {plant['name']} ({plant['plant_id']})")
    print(f"MQTT topic: {topic}")
    print(f"Polling every {POLL_SECONDS} seconds. Press Ctrl-C to stop.")

    while True:
        try:
            data = await read_once(address)
            data["plant"] = plant["name"]
            data["plant_id"] = plant["plant_id"]
            data["sensor_address"] = address
            print(json.dumps(data, sort_keys=True), flush=True)
            publish_mqtt(topic, data)
        except Exception as exc:
            print(json.dumps({"timestamp": utc_now(), "plant": plant["name"], "error": str(exc)}), flush=True)

        await asyncio.sleep(POLL_SECONDS)


def build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("scan")
    stream_parser = subparsers.add_parser("stream")
    stream_parser.add_argument("address", nargs="?")
    stream_parser.add_argument("--plant")

    return parser


async def main():
    args = build_parser().parse_args()
    try:
        if args.command == "scan":
            await scan()
        elif args.command == "stream":
            await stream(args.plant, args.address)
    except BleakError as exc:
        raise SystemExit(
            f"Bluetooth scan/read failed: {exc}\nOn macOS, run this from a local Terminal with Bluetooth permission."
        ) from exc


if __name__ == "__main__":
    asyncio.run(main())
