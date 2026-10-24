from datetime import date, time

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


    def find_trips(self, companies=None, destinations=None, desired_date=None, max_price=None, min_rating=None, 
                   max_transfers=None, number_of_seats=None, arrival_date=None, departure_time=None, 
                   arrival_time=None, luggage_allowance=None, changeable=None, refundable=None, environmental_impact=None):
        results = self.trips
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
            results = [trip for trip in results if trip.arrival_date == arrival_date]
        if departure_time is not None:
            print("Departure time filter applied")
            results = [trip for trip in results if trip.departure_time == departure_time]
        if arrival_time is not None:
            print("Arrival time filter applied")
            results = [trip for trip in results if trip.arrival_time == arrival_time]
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

    def display_search_results(self, trips):
        for trip in trips:
            print(trip)
