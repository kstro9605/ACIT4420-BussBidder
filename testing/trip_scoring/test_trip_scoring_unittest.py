import datetime
import unittest
from dataLoader import load_trips
from tripsService import TripPlanner
from user import User
from priorityHierarchy import Hierarchy
from priority import PriorityType, Priority, Qualifier, QualifierOperator

class TestTripScoring(unittest.TestCase):
    def setUp(self):
        # Load trips from a test CSV file
        self.trips, errors = load_trips('testing/data_loading/valid_test.csv')
        self.assertEqual(len(errors), 0, "There should be no errors for valid data")
        
        # Create a user and set up a hierarchy with priorities
        self.user = User(username="testuser", name="Test User", password="password", email="testuser@example.com")
        hierarchy = Hierarchy()
        hierarchy.add_priority(Priority(PriorityType.LOWER_PRICE, 30))
        hierarchy.add_priority(Priority(PriorityType.DEPARTURE_BEFORE, 20, qualifier=Qualifier(QualifierOperator.EARLIER_THAN, datetime.time(12, 0))))  # Example: Departure before 12 PM
        hierarchy.add_priority(Priority(PriorityType.ARRIVAL_BEFORE, 20, qualifier=Qualifier(QualifierOperator.EARLIER_THAN, datetime.time(18, 0))))  # Example: Arrival before 6 PM
        hierarchy.add_priority(Priority(PriorityType.DURATION, 10))
        hierarchy.add_priority(Priority(PriorityType.FEWER_TRANSFERS, 10))
        self.user.hierarchy = hierarchy

    def test_priority_addition_over_limit(self):
        # Test adding a priority over the allowed limit of 100 points
        self.assertRaises(ValueError, self.user.hierarchy.add_priority, Priority(PriorityType.FLEXIBLE, 15))  

    def test_priority_add_existing_type(self):
        # Test adding a priority of an existing type
        self.assertRaises(ValueError, self.user.hierarchy.add_priority, Priority(PriorityType.LOWER_PRICE, 10))

    def test_priority_negative_weight(self):
        # Test adding a priority with a negative weight
        self.assertRaises(ValueError, self.user.hierarchy.add_priority, Priority(PriorityType.DURATION, -5))

    def test_nonexistent_priority(self):
        # Test creating a priority with a nonexistent type
        with self.assertRaises(AttributeError):
            PriorityType.FREE_MEAL

    def test_no_qualifier_for_timeframe(self):
        # Test creating a timeframe priority without a qualifier
        with self.assertRaises(ValueError):
            Priority(PriorityType.DEPARTURE_BEFORE, 10)

    def test_trip_scoring(self):
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        # Score the trips based on the user's hierarchy
        scored_trips = self.user.hierarchy.score(self.trips)
        
        # Ensure that scored_trips is not empty
        self.assertGreater(len(scored_trips), 0, "There should be scored trips available")

    def test_trip_score_breakdown(self):
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        # Score the trips based on the user's hierarchy
        scored_trips = self.user.hierarchy.score(self.trips)

        # Check that each scored trip has a breakdown of scores
        for scoring, scored_trip in scored_trips:
            self.assertIsInstance(scoring.priority_scores, list, "Each scored trip should have a list of priority scores")
            self.assertIsInstance(scoring.score_value, float, "Each scored trip should have a total score value")

    def test_valid_find_trip_via_id(self):
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        #Valid test data contains two trips with IDs "OF001" and "OF002"
        trip = trip_planner.find_trips(trip_id="OF001")
        self.assertIsNotNone(trip, "Trip should be found for a valid offer ID")

        trip2 = trip_planner.find_trips(trip_id="OF002")
        self.assertIsNotNone(trip2, "Trip should be found for a valid offer ID")

    def test_invalid_find_trip_via_id(self):
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        # Test with an invalid offer ID will return an empty list, as no trip should be found
        trip = trip_planner.find_trips(trip_id="INVALID_ID")
        print(f"Trip found for invalid offer ID: {trip}")
        self.assertEqual(trip, [],"No trip should be found for an invalid offer ID")
        