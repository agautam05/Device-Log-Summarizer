"""Device telemetry summarizer with validation, analytics, and CLI options."""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REQUIRED_COLUMNS = {"device_id", "status", "temperature"}
VALID_STATUSES = {"ACTIVE", "WARNING", "ERROR"}
logger = logging.getLogger("device_summarizer")


def clean_sensor_readings(values: list[Any]) -> list[float]:
    """Convert valid non-negative readings to floats and cap them at 500."""
    cleaned = []
    for value in values:
        if value is None:
            continue
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if not math.isfinite(number) or number < 0:
            continue
        cleaned.append(min(number, 500.0))
    return cleaned


def _read_rows(csv_path: str | Path) -> tuple[list[dict[str, str]], int]:
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Input path is not a file: {path}")

    rows = []
    skipped = 0
    try:
        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no header.")
            missing = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing:
                raise ValueError("Missing required CSV columns: " + ", ".join(sorted(missing)))

            for line_number, row in enumerate(reader, start=2):
                device_id = (row.get("device_id") or "").strip()
                status = (row.get("status") or "").strip().upper()
                raw_temp = row.get("temperature")

                try:
                    temperature = float(raw_temp)
                except (TypeError, ValueError, OverflowError):
                    logger.warning("Skipping row %s: invalid temperature.", line_number)
                    skipped += 1
                    continue

                if not device_id or not math.isfinite(temperature) or temperature < 0:
                    logger.warning("Skipping row %s: invalid device or temperature.", line_number)
                    skipped += 1
                    continue

                if status not in VALID_STATUSES:
                    logger.warning("Row %s has unknown status '%s'; counting it as non-error.",
                                   line_number, status)
                rows.append({
                    "device_id": device_id,
                    "status": status,
                    "temperature": temperature,
                })
    except csv.Error as exc:
        raise ValueError(f"Could not parse CSV file: {exc}") from exc

    return rows, skipped


def summarize_csv(
    csv_path: str | Path,
    max_average: float = 80.0,
    warning_average: float = 70.0,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Aggregate valid records and exclude devices above max_average."""
    if not math.isfinite(max_average) or not math.isfinite(warning_average):
        raise ValueError("Temperature thresholds must be finite numbers.")
    if warning_average > max_average:
        raise ValueError("Warning threshold cannot exceed the maximum average threshold.")

    rows, skipped = _read_rows(csv_path)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["device_id"]].append(row)

    summaries = []
    filtered_count = 0
    for device_id in sorted(grouped):
        device_rows = grouped[device_id]
        temperatures = [row["temperature"] for row in device_rows]
        average = statistics.mean(temperatures)
        error_count = sum(row["status"] == "ERROR" for row in device_rows)

        if average > max_average:
            filtered_count += 1
            logger.info("Excluding %s: average %.2f exceeds %.2f.",
                        device_id, average, max_average)
            continue

        if error_count:
            health = "ERROR"
        elif average >= warning_average:
            health = "WARNING"
        else:
            health = "HEALTHY"

        summaries.append({
            "device_id": device_id,
            "total_records": len(temperatures),
            "average_temperature": round(average, 2),
            "minimum_temperature": round(min(temperatures), 2),
            "maximum_temperature": round(max(temperatures), 2),
            "median_temperature": round(statistics.median(temperatures), 2),
            "temperature_std_dev": round(statistics.pstdev(temperatures), 2),
            "error_count": error_count,
            "health_status": health,
        })

    counts = {
        "valid_records": len(rows),
        "skipped_records": skipped,
        "devices_found": len(grouped),
        "devices_included": len(summaries),
        "devices_filtered": filtered_count,
    }
    return summaries, counts


def save_json(results: list[dict[str, Any]], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=4, allow_nan=False)
        handle.write("\n")


def print_summary(results: list[dict[str, Any]], counts: dict[str, int]) -> None:
    headers = ("DEVICE", "RECORDS", "AVG", "MIN", "MAX", "ERRORS", "HEALTH")
    rows = [
        (r["device_id"], str(r["total_records"]),
         f'{r["average_temperature"]:.2f}',
         f'{r["minimum_temperature"]:.2f}',
         f'{r["maximum_temperature"]:.2f}',
         str(r["error_count"]), r["health_status"])
        for r in results
    ]
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) if rows
              else len(headers[i]) for i in range(len(headers))]
    line = "  ".join("-" * width for width in widths)
    fmt = "  ".join(f"{{:<{width}}}" for width in widths)
    print(fmt.format(*headers))
    print(line)
    for row in rows:
        print(fmt.format(*row))
    if not rows:
        print("No devices matched the selected filters.")
    print(
        f"\nValid records: {counts['valid_records']} | "
        f"Skipped records: {counts['skipped_records']} | "
        f"Devices filtered: {counts['devices_filtered']}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, summarize, and analyze device telemetry CSV data."
    )
    parser.add_argument("--input", default="device_telemetry.csv",
                        help="Input CSV file.")
    parser.add_argument("--output", default="output/summary.json",
                        help="Destination JSON file.")
    parser.add_argument("--max-average", type=float, default=80.0,
                        help="Exclude devices with average temperature above this value.")
    parser.add_argument("--warning-average", type=float, default=70.0,
                        help="Mark devices at or above this average as WARNING.")
    parser.add_argument("--log-file", default="output/device_summarizer.log",
                        help="Application log file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"),
                  logging.StreamHandler(sys.stderr)],
        force=True,
    )

    try:
        results, counts = summarize_csv(
            args.input, max_average=args.max_average,
            warning_average=args.warning_average
        )
        save_json(results, args.output)
        print_summary(results, counts)
        print(f"\nJSON saved to: {args.output}")
        print(f"Log saved to: {args.log_file}")
        return 0
    except (OSError, ValueError) as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
