import unittest
from dataLoader import load_trips

class TestDataLoader(unittest.TestCase):
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
        