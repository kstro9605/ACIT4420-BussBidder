import csv
import unittest
from datetime import date, timedelta
from dataLoader import load_trips, row_to_trip_with_validation

class TestDataLoader(unittest.TestCase):
    def test_trip_date_cannot_be_before_today(self):
        with open('testing/data_loading/valid_test.csv', newline='', encoding='utf-8') as file:
            row = next(csv.DictReader(file))
        row["travel_date"] = row["arrival_date"] = (
            date.today() + timedelta(days=1)
        ).isoformat()
        row["travel_date"] = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "Trip date .* is before the current date"):
            row_to_trip_with_validation(row)

    def test_arrival_date_cannot_be_before_today(self):
        with open('testing/data_loading/valid_test.csv', newline='', encoding='utf-8') as file:
            row = next(csv.DictReader(file))
        row["travel_date"] = row["arrival_date"] = (
            date.today() + timedelta(days=1)
        ).isoformat()
        row["arrival_date"] = (date.today() - timedelta(days=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "Arrival date .* is before the current date"):
            row_to_trip_with_validation(row)

    def test_load_data_valid_file(self):
        data = load_trips('testing/data_loading/valid_test.csv')
        self.assertIsNotNone(data, "Data should not be None for a valid file")

    def test_load_data_invalid_file(self):
        with self.assertRaises(FileNotFoundError):
            load_trips('testing/data_loading/nonexistant_file.csv')

    def test_load_data_incorrect_format(self):
        with self.assertRaises(ValueError):
            load_trips('testing/data_loading/incorrect_format.txt')

    def test_load_data_empty_file(self):
        with self.assertRaises(ValueError):
            load_trips('testing/data_loading/empty_file.csv')

    def test_load_valid_trip_data(self):
        trips, errors = load_trips('testing/data_loading/valid_test.csv')
        self.assertEqual(len(trips), 2, "Should load 2 valid trips")
        self.assertEqual(len(errors), 0, "There should be no errors for valid data")

    def test_load_invalid_trip_data(self):
        trips, errors = load_trips('testing/data_loading/failing_data.csv')
        self.assertEqual(len(trips), 0, "Should load 0 valid trips")
        self.assertGreater(len(errors), 0, "There should be errors for invalid data")
        