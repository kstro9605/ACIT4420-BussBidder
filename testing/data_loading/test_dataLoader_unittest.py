import csv
import unittest
from datetime import date, timedelta
from dataLoader import load_trips, row_to_trip_with_validation

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        print(f"\nStarting {self.id()}", flush=True)

    def test_trip_date_cannot_be_before_today(self):
        print("Checking that a trip date before today is rejected.", flush=True)
        with open('testing/data_loading/valid_test.csv', newline='', encoding='utf-8') as file:
            row = next(csv.DictReader(file))
        row["travel_date"] = row["arrival_date"] = (
            date.today() + timedelta(days=1)
        ).isoformat()
        row["travel_date"] = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "Trip date .* is before the current date"):
            row_to_trip_with_validation(row)
        print(f"Rejected past trip date: {row['travel_date']}.", flush=True)

    def test_arrival_date_cannot_be_before_today(self):
        print("Checking that an arrival date before today is rejected.", flush=True)
        with open('testing/data_loading/valid_test.csv', newline='', encoding='utf-8') as file:
            row = next(csv.DictReader(file))
        row["travel_date"] = row["arrival_date"] = (
            date.today() + timedelta(days=1)
        ).isoformat()
        row["arrival_date"] = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "Arrival date .* is before the current date"):
            row_to_trip_with_validation(row)
        print(f"Rejected past arrival date: {row['arrival_date']}.", flush=True)

    def test_load_data_valid_file(self):
        print("Loading the valid CSV and checking a result is returned.", flush=True)
        data = load_trips('testing/data_loading/valid_test.csv')
        self.assertIsNotNone(data, "Data should not be None for a valid file")
        print(f"Loader returned {len(data[0])} trip(s) and {len(data[1])} error(s).", flush=True)

    def test_load_data_invalid_file(self):
        print("Checking that a missing CSV file raises FileNotFoundError.", flush=True)
        with self.assertRaises(FileNotFoundError):
            load_trips('testing/data_loading/nonexistant_file.csv')
        print("Missing file was rejected as expected.", flush=True)

    def test_load_data_incorrect_format(self):
        print("Checking that a non-CSV file is rejected.", flush=True)
        with self.assertRaises(ValueError):
            load_trips('testing/data_loading/incorrect_format.txt')
        print("Incorrect file format was rejected as expected.", flush=True)

    def test_load_data_empty_file(self):
        print("Checking that an empty CSV file is rejected.", flush=True)
        with self.assertRaises(ValueError):
            load_trips('testing/data_loading/empty_file.csv')
        print("Empty file was rejected as expected.", flush=True)

    def test_load_valid_trip_data(self):
        print("Loading valid trip rows and checking counts and errors.", flush=True)
        trips, errors = load_trips('testing/data_loading/valid_test.csv')
        self.assertEqual(len(trips), 2, "Should load 2 valid trips")
        self.assertEqual(len(errors), 0, "There should be no errors for valid data")
        print(f"Loaded {len(trips)} valid trip(s); {len(errors)} row error(s).", flush=True)

    def test_load_invalid_trip_data(self):
        print("Loading the failing-data CSV and checking invalid rows are reported.", flush=True)
        trips, errors = load_trips('testing/data_loading/failing_data.csv')
        self.assertEqual(len(trips), 0, "Should load 0 valid trips")
        self.assertGreater(len(errors), 0, "There should be errors for invalid data")
        print(f"Loaded {len(trips)} valid trip(s); captured {len(errors)} row error(s):", flush=True)
        for error in errors:
            print(f"  {error}", flush=True)
        