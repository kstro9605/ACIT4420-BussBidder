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