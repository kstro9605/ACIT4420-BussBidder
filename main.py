from webInterface import run_web_interface
from priorityHierarchy import Hierarchy, Priority, PriorityType
from priority import Qualifier, QualifierOperator
from datetime import date, time
from dataLoader import load_trips
from tripsService import TripPlanner
from pathlib import Path

def main():
    #run_web_interface()
    priority_bundle = []

    qualifier=Qualifier(QualifierOperator.LATER_THAN, time.fromisoformat("17:00"))

    priority_bundle.append({"priority_type":PriorityType.DEPARTURE_AFTER,"priority_weight": 7, "priority_qualifier": qualifier})
    priority_bundle.append({"priority_type":PriorityType.LOWER_PRICE,"priority_weight": 37})
    priority_bundle.append({"priority_type":PriorityType.FLEXIBLE,"priority_weight": 26})
    priority_bundle.append({"priority_type":PriorityType.FEWER_TRANSFERS,"priority_weight": 19})
    priority_bundle.append({"priority_type":PriorityType.DURATION,"priority_weight": 11})

    test_hierarchy = Hierarchy()
    test_hierarchy.create_priorities(priority_bundle)

    csv_path = Path(__file__).resolve().parent / "data" / "trips.csv"
    trips, errors = load_trips(csv_path)
    print(f"Loaded {len(trips)} valid trip(s) from {csv_path}.")
    if errors:
        print(f"Skipped {len(errors)} invalid trip row(s):")
        for error in errors:
            print(f"  {error}")

    planner = TripPlanner()
    planner.add_trips(trips)

    payload = planner.find_trips()

    graded_trips = test_hierarchy.score(payload)
    #graded_trips.sort(key=lambda item: item[0], reverse=True)

    print(graded_trips[0][0], graded_trips[0][1].trip_id)
    print(graded_trips[1][0], graded_trips[1][1].trip_id)
    print(graded_trips[2][0], graded_trips[2][1].trip_id)
    print(graded_trips[-1][0], graded_trips[-1][1].trip_id)



    


if __name__ == "__main__":
    main()