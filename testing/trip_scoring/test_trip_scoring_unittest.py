import datetime
import unittest
from dataLoader import load_trips
from tripsService import TripPlanner
from user import User
from priorityHierarchy import Hierarchy
from priority import PriorityType, Priority, Qualifier, QualifierOperator

class TestTripScoring(unittest.TestCase):
    def setUp(self):
        print(f"\nStarting {self.id()}", flush=True)
        # Load trips from a test CSV file
        self.trips, errors = load_trips('testing/data_loading/valid_test.csv')
        self.assertEqual(len(errors), 0, "There should be no errors for valid data")
        print(f"Loaded {len(self.trips)} valid test trips.", flush=True)
        
        # Create a user and set up a hierarchy with priorities
        self.user = User(username="testuser", name="Test User", password="password", email="testuser@example.com")
        hierarchy = Hierarchy()
        hierarchy.add_priority(Priority(PriorityType.LOWER_PRICE, 30))
        hierarchy.add_priority(Priority(PriorityType.DEPARTURE_BEFORE, 20, qualifier=Qualifier(QualifierOperator.EARLIER_THAN, datetime.time(12, 0)))) 
        hierarchy.add_priority(Priority(PriorityType.ARRIVAL_BEFORE, 20, qualifier=Qualifier(QualifierOperator.EARLIER_THAN, datetime.time(18, 0)))) 
        hierarchy.add_priority(Priority(PriorityType.DURATION, 10))
        hierarchy.add_priority(Priority(PriorityType.FEWER_TRANSFERS, 10))
        self.user.hierarchy = hierarchy

    def test_priority_addition_over_limit(self):
        # Test adding a priority over the allowed limit of 100 points
        print("Checking that adding a priority above 100 total weight is rejected.", flush=True)
        self.assertRaises(ValueError, self.user.hierarchy.add_priority, Priority(PriorityType.FLEXIBLE, 15))  

    def test_priority_add_existing_type(self):
        print("Checking that adding a duplicate priority type is rejected.", flush=True)
        # Test adding a priority of an existing type
        self.assertRaises(ValueError, self.user.hierarchy.add_priority, Priority(PriorityType.LOWER_PRICE, 10))

    def test_priority_negative_weight(self):
        print("Checking that a negative priority weight is rejected.", flush=True)
        # Test adding a priority with a negative weight
        self.assertRaises(ValueError, self.user.hierarchy.add_priority, Priority(PriorityType.DURATION, -5))

    def test_nonexistent_priority(self):
        print("Checking that an unknown PriorityType cannot be accessed.", flush=True)
        # Test creating a priority with a nonexistent type
        with self.assertRaises(AttributeError):
            PriorityType.FREE_MEAL

    def test_no_qualifier_for_timeframe(self):
        print("Checking that a time-based priority requires a qualifier.", flush=True)
        # Test creating a timeframe priority without a qualifier
        with self.assertRaises(ValueError):
            Priority(PriorityType.DEPARTURE_BEFORE, 10)

    def test_trip_scoring(self):
        print("Scoring all loaded trips with the user's priority hierarchy.", flush=True)
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        # Score the trips based on the user's hierarchy
        scored_trips = self.user.hierarchy.score(self.trips)
        
        # Ensure that scored_trips is not empty
        self.assertGreater(len(scored_trips), 0, "There should be scored trips available")
        for score, trip in scored_trips:
            print(f"Trip {trip.trip_id}: total score {score.score_value:.2f}", flush=True)

    def test_trip_score_breakdown(self):
        print("Checking total scores and per-priority score breakdowns.", flush=True)
        # Score the trips based on the user's hierarchy
        scored_trips = self.user.hierarchy.score(self.trips)

        # Check that each scored trip has a breakdown of scores
        for scoring, scored_trip in scored_trips:
            print(
                f"Trip {scored_trip.trip_id}: total={scoring.score_value:.2f}, "
                f"priority components={len(scoring.priority_scores)}",
                flush=True,
            )
            self.assertIsInstance(scoring.priority_scores, list, "Each scored trip should have a list of priority scores")
            self.assertIsInstance(scoring.score_value, float, "Each scored trip should have a total score value")

    def test_valid_find_trip_via_id(self):
        print("Looking up the known valid trip IDs OF001 and OF002.", flush=True)
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        #Valid test data contains two trips with IDs "OF001" and "OF002"
        trip = trip_planner.find_trips(trip_id="OF001")
        self.assertIsNotNone(trip, "Trip should be found for a valid offer ID")
        print(f"OF001 lookup returned {len(trip)} trip(s).", flush=True)

        trip2 = trip_planner.find_trips(trip_id="OF002")
        self.assertIsNotNone(trip2, "Trip should be found for a valid offer ID")
        print(f"OF002 lookup returned {len(trip2)} trip(s).", flush=True)

    def test_invalid_find_trip_via_id(self):
        print("Looking up an unknown trip ID; expecting no results.", flush=True)
        # Create a TripPlanner with the loaded trips and the user's hierarchy
        trip_planner = TripPlanner()
        trip_planner.add_trips(self.trips)

        # Test with an invalid offer ID will return an empty list, as no trip should be found
        trip = trip_planner.find_trips(trip_id="INVALID_ID")
        self.assertEqual(trip, [],"No trip should be found for an invalid offer ID")
        print(f"INVALID_ID lookup returned {len(trip)} trip(s).", flush=True)

    def test_user_based_priority_ranking(self):
        print("Comparing rankings for budget-minded and duration-minded users.", flush=True)
        planner = TripPlanner()
        planner.add_trips(self.trips)

        short_trip_user = User(username="PreferShort", name="ShortUser", password="password", email="testshortuser@example.com")
        hierarchy = Hierarchy()
        hierarchy.add_priority(Priority(PriorityType.DURATION, 40))
        hierarchy.add_priority(Priority(PriorityType.LOWER_PRICE, 10))
        hierarchy.add_priority(Priority(PriorityType.DEPARTURE_BEFORE, 20, qualifier=Qualifier(QualifierOperator.EARLIER_THAN, datetime.time(12, 0)))) 
        hierarchy.add_priority(Priority(PriorityType.ARRIVAL_BEFORE, 20, qualifier=Qualifier(QualifierOperator.EARLIER_THAN, datetime.time(18, 0)))) 
        hierarchy.add_priority(Priority(PriorityType.FEWER_TRANSFERS, 10))
        short_trip_user.hierarchy = hierarchy

        budget_minded_scoring = self.user.hierarchy.score(planner.find_trips())
        duration_minded_scoring = short_trip_user.hierarchy.score(planner.find_trips())

        self.assertNotEqual(budget_minded_scoring, duration_minded_scoring, "Trip scoring returns for the two different users should not be equal")
        print(
            "Budget-minded ranking: "
            + ", ".join(
                f"{trip.trip_id} ({score.score_value:.2f})"
                for score, trip in budget_minded_scoring
            ),
            flush=True,
        )
        print(
            "Duration-minded ranking: "
            + ", ".join(
                f"{trip.trip_id} ({score.score_value:.2f})"
                for score, trip in duration_minded_scoring
            ),
            flush=True,
        )

        first_trip_id_budget = budget_minded_scoring[0][1].trip_id
        first_trip_id_duration = duration_minded_scoring[0][1].trip_id

        self.assertNotEqual(first_trip_id_budget,first_trip_id_duration)
        print(
            f"Top trips differ: budget={first_trip_id_budget}, "
            f"duration={first_trip_id_duration}.",
            flush=True,
        )