import io
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from .status import range_for
from .storage import Storage
from .time import parse_time, utc_now

CHART_WINDOWS = {
    "1h": ("1 hour", timedelta(hours=1), "%H:%M"),
    "24h": ("24 hours", timedelta(hours=24), "%m-%d %H:%M"),
    "7d": ("7 days", timedelta(days=7), "%m-%d"),
}


@dataclass(frozen=True)
class ChartWindow:
    key: str
    label: str
    duration: timedelta
    date_format: str


def chart_window(key: str) -> ChartWindow:
    label, duration, date_format = CHART_WINDOWS.get(key, CHART_WINDOWS["7d"])
    safe_key = key if key in CHART_WINDOWS else "7d"
    return ChartWindow(key=safe_key, label=label, duration=duration, date_format=date_format)


def chart_png(storage: Storage, slug: str, detail: dict[str, Any], window: ChartWindow) -> io.BytesIO | None:
    rows = storage.readings_since(slug, utc_now() - window.duration)
    if not rows:
        return None

    timestamps = [parse_time(row[0]) for row in rows]
    fig, axes = plt.subplots(5, 1, figsize=(10, 11), sharex=True)
    fig.suptitle(f"Last {window.label}", fontsize=14, fontweight="bold")
    for axis, key, index, label in [
        (axes[0], "temperature", 1, "deg C"),
        (axes[1], "moisture", 2, "%"),
        (axes[2], "conductivity", 3, "uS/cm"),
        (axes[3], "light", 4, "lux"),
        (axes[4], "battery", 5, "%"),
    ]:
        values = [row[index] for row in rows]
        _draw_status_bands(axis, key, detail)
        axis.plot(timestamps, values, marker="o", linewidth=1.8, color="#1f4e79")
        axis.set_ylabel(label)
        axis.set_title(key.title())
        axis.grid(True, alpha=0.3)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter(window.date_format))
    fig.autofmt_xdate()
    fig.tight_layout(rect=(0, 0, 1, 0.98))

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return buffer


def _draw_status_bands(axis, key: str, detail: dict[str, Any]) -> None:
    min_value, max_value = range_for(detail, key)
    if min_value is not None and max_value is not None:
        span = max(max_value - min_value, 1)
        margin = span * 0.15
        axis.axhspan(min_value, max_value, color="#69b96f", alpha=0.22)
        axis.axhspan(min_value - margin, min_value, color="#f2b84b", alpha=0.18)
        axis.axhspan(max_value, max_value + margin, color="#f2b84b", alpha=0.18)
        axis.axhline(min_value, color="#3d8b40", linewidth=0.8)
        axis.axhline(max_value, color="#3d8b40", linewidth=0.8)
    elif key == "battery":
        axis.axhspan(30, 100, color="#69b96f", alpha=0.22)
        axis.axhspan(15, 30, color="#f2b84b", alpha=0.18)
        axis.axhspan(0, 15, color="#d9534f", alpha=0.12)
