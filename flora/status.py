import html
from typing import Any

from .plants import Plant

RANGES = {
    "temperature": ("🌡", "T", "°C", "min_temp", "max_temp"),
    "moisture": ("💧", "M", "%", "min_soil_moist", "max_soil_moist"),
    "conductivity": ("🧂", "EC", "µS/cm", "min_soil_ec", "max_soil_ec"),
    "light": ("☀️", "L", "lux", "min_light_lux", "max_light_lux"),
    "humidity": ("💨", "RH", "%", "min_env_humid", "max_env_humid"),
}


def range_for(detail: dict[str, Any], key: str) -> tuple[float | None, float | None]:
    if key not in RANGES:
        return None, None
    _, _, _, min_key, max_key = RANGES[key]
    return detail.get(min_key), detail.get(max_key)


def status_for(value: float | None, min_value: float | None, max_value: float | None) -> tuple[str, str]:
    if value is None or min_value is None or max_value is None:
        return "⚪", "n/a"
    if min_value <= value <= max_value:
        return "🟢", "ok"
    span = max(max_value - min_value, 1)
    margin = span * 0.15
    if min_value - margin <= value < min_value:
        return "🟠", "low"
    if max_value < value <= max_value + margin:
        return "🟠", "high"
    return ("🔴", "low") if value < min_value else ("🔴", "high")


def fmt_number(value: Any) -> str:
    if value is None:
        return "?"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def metric_line(detail: dict[str, Any], latest: dict[str, Any] | None, key: str) -> str:
    icon, label, unit, _, _ = RANGES[key]
    min_value, max_value = range_for(detail, key)
    value = latest.get(key) if latest else None
    status, word = status_for(value, min_value, max_value)
    return (
        f"{status} {icon} <b>{label}</b> {fmt_number(value)}{unit} "
        f"({fmt_number(min_value)}-{fmt_number(max_value)}{unit}) {word}"
    )


def battery_line(latest: dict[str, Any] | None) -> str:
    value = latest.get("battery") if latest else None
    if value is None:
        return "⚪ 🔋 <b>Bat</b> ?"
    status = "🟢" if value >= 30 else "🟠" if value >= 15 else "🔴"
    return f"{status} 🔋 <b>Bat</b> {fmt_number(value)}%"


def plant_card_lines(plant: Plant, detail: dict[str, Any], latest: dict[str, Any] | None) -> list[str]:
    name = detail.get("display_pid") or plant.name
    return [
        f"🪴 <b>{html.escape(name)}</b>",
        metric_line(detail, latest, "moisture"),
        metric_line(detail, latest, "light"),
        metric_line(detail, latest, "temperature"),
        metric_line(detail, latest, "conductivity"),
        battery_line(latest),
    ]
