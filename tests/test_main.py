import csv
import json
import tempfile
import unittest
from pathlib import Path

from main import clean_sensor_readings, summarize_csv, save_json


class CleaningTests(unittest.TestCase):
    def test_mixed_values_and_clipping(self):
        self.assertEqual(
            clean_sensor_readings(["12.5", None, -4, "bad", 600, 0]),
            [12.5, 500.0, 0.0],
        )

    def test_empty_and_non_finite_values(self):
        self.assertEqual(clean_sensor_readings([]), [])
        self.assertEqual(clean_sensor_readings([None, "nan", "inf", -1]), [])


class SummaryTests(unittest.TestCase):
    def write_csv(self, folder, content):
        path = Path(folder) / "input.csv"
        path.write_text(content, encoding="utf-8")
        return path

    def test_statistics_health_and_filtering(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_csv(folder,
                "device_id,status,temperature\n"
                "A,ACTIVE,40\nA,ERROR,60\n"
                "B,ACTIVE,75\nB,ACTIVE,77\n"
                "C,ERROR,90\nC,ACTIVE,95\n")
            result, counts = summarize_csv(path)
            self.assertEqual([r["device_id"] for r in result], ["A", "B"])
            self.assertEqual(result[0]["average_temperature"], 50.0)
            self.assertEqual(result[0]["error_count"], 1)
            self.assertEqual(result[0]["health_status"], "ERROR")
            self.assertEqual(result[1]["health_status"], "WARNING")
            self.assertEqual(counts["devices_filtered"], 1)

    def test_bad_rows_are_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_csv(folder,
                "device_id,status,temperature\n"
                "A,ACTIVE,25\n"
                "A,ERROR,not-a-number\n"
                ",ACTIVE,30\n")
            result, counts = summarize_csv(path)
            self.assertEqual(result[0]["total_records"], 1)
            self.assertEqual(counts["skipped_records"], 2)

    def test_missing_file_and_missing_columns(self):
        with self.assertRaises(FileNotFoundError):
            summarize_csv("not_here.csv")
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_csv(folder, "device_id,status\nA,ACTIVE\n")
            with self.assertRaises(ValueError):
                summarize_csv(path)

    def test_threshold_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write_csv(folder,
                "device_id,status,temperature\nA,ACTIVE,25\n")
            with self.assertRaises(ValueError):
                summarize_csv(path, max_average=60, warning_average=70)

    def test_json_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "nested" / "summary.json"
            save_json([{"device_id": "A"}], path)
            self.assertEqual(json.loads(path.read_text()), [{"device_id": "A"}])


if __name__ == "__main__":
    unittest.main()
