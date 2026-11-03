# Device Log Summarizer — Advanced Edition

A command-line Python application for validating device telemetry CSV files, calculating device-level statistics, filtering devices by average temperature, exporting JSON, and generating charts.

## Features
- CSV header validation and row-level data validation.
- Sensor reading cleaning: float conversion, invalid/negative filtering, and clipping above 500.
- Per-device record count, mean, minimum, maximum, median, population standard deviation, and ERROR count.
- Configurable maximum-average and warning thresholds.
- Device health labels: HEALTHY, WARNING, ERROR.
- JSON export, terminal summary, and file/console logging.
- Two charts: average temperature and ERROR record count.
- Automated unit tests using Python's standard `unittest`.

## Requirements
Python 3.10+ and pip.

## Setup (Windows PowerShell)
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use `venv\Scripts\activate.bat` from Command Prompt, or run `python -m pip install -r requirements.txt` and `venv\Scripts\python.exe ...`.

## Run
```powershell
python main.py
python chart.py
```

## Custom options
```powershell
python main.py --input device_telemetry.csv --output output/summary.json --max-average 85 --warning-average 70
python chart.py --input output/summary.json --output-dir output
```

Use `python main.py --help` and `python chart.py --help` to see all options.

## Output files
- `output/summary.json` — device summaries.
- `output/temperature_chart.png` — average temperature chart.
- `output/error_chart.png` — error count chart.
- `output/device_summarizer.log` — warnings and execution log.

## Data rules
- Rows with missing device IDs, invalid/non-finite temperatures, or negative temperatures are skipped and logged.
- Unknown status values are retained as records but are not counted as ERROR.
- A device is excluded only when its average is strictly greater than `--max-average`.
- ERROR status takes priority for health classification. Otherwise, an average at or above `--warning-average` is WARNING; all other included devices are HEALTHY.
- The included CSV is demonstration data. Replace it with the assessment's original input file if one was supplied.

## Tests
```powershell
python -m unittest discover -s tests -v
```

## Project structure
```text
device_log_summarizer_advanced/
|-- main.py
|-- chart.py
|-- device_telemetry.csv
|-- requirements.txt
|-- README.md
|-- PROMPT_LOG.md
|-- tests/
|   `-- test_main.py
`-- output/
```
