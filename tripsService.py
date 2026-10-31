from datetime import date, time
from constants import FORM_FIELDS, VALID_COMPANIES, VALID_DESTINATIONS

class Trip():
    def __init__(self, trip_id, trip_company, trip_destination, trip_date, arrival_date, departure_time, arrival_time, duration_minutes, price_euro, transfers, transfer_locations, luggage_allowance, changeable, refundable, seats_available, customer_rating, environmental_impact):
        self.trip_id = trip_id
        self.trip_company = trip_company
        self.trip_destination = trip_destination
        self.trip_date = trip_date
        self.arrival_date = arrival_date
        self.departure_time = departure_time
        self.arrival_time = arrival_time
        self.duration = duration_minutes
        self.trip_price = price_euro
        self.transfers = transfers
        self.transfer_locations = transfer_locations
        self.luggage_allowance = luggage_allowance
        self.changes_allowed = changeable
        self.refundable = refundable
        self.seats_available = seats_available
        self.customer_rating = customer_rating
        self.environmental_impact = environmental_impact

    def __str__(self):
        return f"Trip ID: {self.trip_id}, Company: {self.trip_company}, Destination: {self.trip_destination}, Date: {self.trip_date}, price: {self.trip_price} Euro, Duration: {self.duration} minutes, Transfers: {self.transfers}, Seats Available: {self.seats_available}, Customer Rating: {self.customer_rating}, Environmental Impact: {self.environmental_impact}"

class TripPlanner():
    def __init__(self):
        self.trips = []

    def add_trip(self, trip):
        self.trips.append(trip)

    def add_trips(self, trips):
        self.trips.extend(trips)

    def find_trips(self, trip_id=None, companies=None, destinations=None, desired_date=None, desired_date_from=None,
                   desired_date_to=None, max_price=None, min_rating=None,
                   max_transfers=None, number_of_seats=None, arrival_date=None, departure_time=None, 
                   arrival_date_from=None, arrival_date_to=None,
                   departure_time_from=None, departure_time_to=None,
                   arrival_time=None, arrival_time_from=None, arrival_time_to=None, luggage_allowance=None,
                   changeable=None, refundable=None, environmental_impact=None):
        results = self.trips
        if trip_id:
            results = [trip for trip in results if trip.trip_id in trip_id]
        if companies:
            print("Company filter applied")
            results = [trip for trip in results if trip.trip_company in companies]
        if destinations:
            print("Destination filter applied")
            selected_destinations = {destination.lower() for destination in destinations}
            results = [
                trip for trip in results
                if trip.trip_destination.lower() in selected_destinations
            ]
        if desired_date is not None:
            print("Date filter applied")
            trip_date = date.fromisoformat(desired_date)
            results = [trip for trip in results if trip.trip_date == trip_date]
        if desired_date_from is not None:
            results = [trip for trip in results if trip.trip_date >= desired_date_from]
        if desired_date_to is not None:
            results = [trip for trip in results if trip.trip_date <= desired_date_to]
        if max_price is not None:
            print("Max price filter applied")
            results = [trip for trip in results if trip.trip_price <= max_price]
        if min_rating is not None:
            print("Min rating filter applied")
            results = [trip for trip in results if trip.customer_rating >= min_rating]
        if max_transfers is not None:
            print("Max transfers filter applied")
            results = [trip for trip in results if trip.transfers <= max_transfers]
        if number_of_seats is not None:
            print("Number of seats filter applied")
            results = [trip for trip in results if trip.seats_available >= number_of_seats]
        if arrival_date is not None:
            print("Arrival date filter applied")
            trip_date = date.fromisoformat(arrival_date)
            results = [trip for trip in results if trip.arrival_date == trip_date]
        if arrival_date_from is not None:
            results = [trip for trip in results if trip.arrival_date >= arrival_date_from]
        if arrival_date_to is not None:
            results = [trip for trip in results if trip.arrival_date <= arrival_date_to]
        if departure_time is not None:
            print("Departure time filter applied")
            results = [trip for trip in results if trip.departure_time == departure_time]
        if departure_time_from is not None:
            results = [trip for trip in results if trip.departure_time >= departure_time_from]
        if departure_time_to is not None:
            results = [trip for trip in results if trip.departure_time <= departure_time_to]
        if arrival_time is not None:
            print("Arrival time filter applied")
            results = [trip for trip in results if trip.arrival_time == arrival_time]
        if arrival_time_from is not None:
            results = [trip for trip in results if trip.arrival_time >= arrival_time_from]
        if arrival_time_to is not None:
            results = [trip for trip in results if trip.arrival_time <= arrival_time_to]
        if luggage_allowance is not None:
            print("Luggage allowance filter applied")
            results = [trip for trip in results if trip.luggage_allowance >= luggage_allowance]
        if changeable is not None:
            print("Changeable filter applied")
            results = [trip for trip in results if trip.changes_allowed == changeable]
        if refundable is not None:
            print("Refundable filter applied")
            results = [trip for trip in results if trip.refundable == refundable]
        if environmental_impact is not None:
            print("Environmental impact filter applied")
            results = [trip for trip in results if trip.environmental_impact == environmental_impact]   
        return results

    def parse_search(self, values):
        query = {}
        errors = []
        
        for field in FORM_FIELDS:
            name = field[0]
            label = field[1]
            field_type = field[4]
            raw_values = [value.strip() for value in values.get(name, []) if value.strip()]


            if not raw_values and field_type not in ("date","time"):
                continue

            try:
                if field_type == "time":
                    start_value = values.get(f"{name}_from", [""])[-1].strip()
                    end_value = values.get(f"{name}_to", [""])[-1].strip()
                    if not start_value and not end_value:
                        continue

                    start = time.fromisoformat(start_value) if start_value else None
                    end = time.fromisoformat(end_value) if end_value else None
                    
                    if start is not None and end is not None and start > end:
                        raise ValueError("start time must be on or before end time")
                    if start is not None:
                        query[f"{name}_from"] = start
                    if end is not None:
                        query[f"{name}_to"] = end
                    continue
                
                if field_type == "date":
                    is_flexible = (values.get(f"{name}_is_flexible", [""])[-1].lower() == "true")
                    
                    if is_flexible:
                        start_value = values.get(f"{name}_from", [""])[-1].strip()
                        end_value = values.get(f"{name}_to", [""])[-1].strip()
                        if not start_value or not end_value:
                            raise ValueError(f"enter both the start and end {field_type}s")

                        start = date.fromisoformat(start_value)
                        end = date.fromisoformat(end_value)
                        if start > end:
                            raise ValueError(f"start {field_type} must be on or before end {field_type}")

                        query[f"{name}_from"] = start
                        query[f"{name}_to"] = end
                        continue

                    if not raw_values:
                        continue
                    raw_value = raw_values[-1]
                    date.fromisoformat(raw_value)
                    query[name] = raw_value
                    continue

                if name == "company":
                    for company in raw_values:
                        if company not in VALID_COMPANIES:
                            raise ValueError(f"Invalid company: {company}.")
                    query["companies"] = raw_values
                    continue

                if name == "destination":
                    for destination in raw_values:
                        if destination not in VALID_DESTINATIONS:
                            raise ValueError(f"Invalid destination: {destination}.")
                    query["destinations"] = raw_values
                    continue

                raw_value = raw_values[-1]
                if name in ("max_price", "min_rating"):
                    query[name] = float(raw_value)
                    if query[name] < 0:
                        raise ValueError("must be zero or greater")
                    
                elif name in ("max_transfers", "number_of_seats", "luggage_allowance"):
                    query[name] = int(raw_value)
                    if query[name] < 0:
                        raise ValueError("must be zero or greater")
                    
                elif name in ("changeable", "refundable"):
                    normalized = raw_value.lower()
                    if normalized not in ("true", "false"):
                        raise ValueError("enter true or false")
                    query[name] = normalized == "true"

                else:
                    query[name] = raw_value

            except ValueError as error:
                errors.append(f"{label}: {error}")

        return query, errors
