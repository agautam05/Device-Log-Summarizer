"""Create temperature and error-count charts from summary JSON."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_summary(json_path):
    path = Path(json_path)
    if not path.is_file():
        raise FileNotFoundError(f"Summary JSON not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("Summary JSON must contain a list.")
    required = {"device_id", "average_temperature", "error_count"}
    for index, item in enumerate(data):
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError(f"Invalid summary entry at position {index}.")
    return data


def create_charts(json_path, output_dir="output"):
    data = load_summary(json_path)
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)

    devices = [item["device_id"] for item in data]
    averages = [float(item["average_temperature"]) for item in data]
    errors = [int(item["error_count"]) for item in data]

    fig, ax = plt.subplots(figsize=(9, 5))
    if devices:
        bars = ax.bar(devices, averages)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        ax.set_ylim(0, max(90, max(averages) * 1.15))
    else:
        ax.text(0.5, 0.5, "No devices passed the filter",
                ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Average Temperature by Device")
    ax.set_xlabel("Device ID")
    ax.set_ylabel("Average Temperature")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    fig.tight_layout()
    temperature_file = folder / "temperature_chart.png"
    fig.savefig(temperature_file, dpi=160, bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    if devices:
        bars = ax.bar(devices, errors)
        ax.bar_label(bars, padding=3)
        ax.set_ylim(0, max(1, max(errors) + 1))
    else:
        ax.text(0.5, 0.5, "No device data available",
                ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Error Records by Device")
    ax.set_xlabel("Device ID")
    ax.set_ylabel("Number of ERROR records")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    fig.tight_layout()
    error_file = folder / "error_chart.png"
    fig.savefig(error_file, dpi=160, bbox_inches="tight")
    plt.close(fig)

    return temperature_file, error_file


def main():
    parser = argparse.ArgumentParser(description="Generate device telemetry charts.")
    parser.add_argument("--input", default="output/summary.json")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args()
    try:
        files = create_charts(args.input, args.output_dir)
        for file in files:
            print(f"Chart saved: {file}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, TypeError, KeyError) as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
