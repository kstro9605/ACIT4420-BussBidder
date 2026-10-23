import csv
from datetime import date, time
from tripsService import Trip

VALID_COMPANIES = {"SolRuta", "Camino Express", "CostaLink", "VerdeBus", "NocheVia"}
VALID_DESTINATIONS = {"Barcelona", "Madrid", "Valencia", "Seville", "Bilbao", "Granada", "Malaga", "Zaragoza", "Alicante", "Cordoba", "Toledo", "Cadiz", "San Sebastian", "Santiago de Compostela", "Salamanca", "Murcia"}

def Main():
    trips,errors = load_trips("trips.csv")
    print(f"Loaded {len(trips)} trips with {len(errors)} errors.")
    print("Errors:")
    for error in errors:
        print(f"  {error}")


def parse_bool(value):
    value = value.strip().upper()
    if value == "TRUE":
        return True
    if value == "FALSE":
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def row_to_trip_with_validation(row):
    trip_id=row["offer_id"]
    if not trip_id:
        raise ValueError("Trip ID is a mandatory field and cannot be empty.")
    
    trip_company=row["company"]
    if trip_company not in VALID_COMPANIES:
        raise ValueError(f"Invalid trip company: {trip_company}.")
    
    trip_destination=row["destination"]
    if trip_destination not in VALID_DESTINATIONS:
        raise ValueError(f"Invalid trip destination: {trip_destination}.")
    
    try:
        trip_date=date.fromisoformat(row["travel_date"])
        arrival_date=date.fromisoformat(row["arrival_date"])
    except ValueError as e:
        raise ValueError(f"Invalid date, expected YYYY-MM-DD, Error: {e}")
    
    try:
        departure_time=time.fromisoformat(row["departure_time"])
        arrival_time=time.fromisoformat(row["arrival_time"])
    except ValueError as e:
        raise ValueError(f"Invalid time, expected HH:MM, Error: {e}")

    try:
        duration_minutes=int(row["duration_minutes"])
    except ValueError as e:
        raise ValueError(f"Invalid duration, expected integer, Error: {e}")
    if duration_minutes <= 0:
        raise ValueError("Duration must be a positive integer.")
    
    try:
        if row["price_euro"] == "":
            raise ValueError("Price is a mandatory field and cannot be empty.")
        price_euro=float(row["price_euro"])
    except ValueError as e:
        raise ValueError(f"Invalid price data. Error: {e}")
    
    try:
        transfers=int(row["transfers"])
    except ValueError as e:
        raise ValueError(f"Invalid transfers data. Error: {e}")
    
    transfer_locations = (
        [location.strip() for location in row["transfer_via"].split("/")
            if location.strip()]
        if row["transfer_via"].strip()
        else []
    )

    try:
        luggage_allowance=int(row["luggage_allowance_kg"])
    except ValueError as e:
        raise ValueError(f"Invalid luggage allowance data. Error: {e}")
    
    changeable=parse_bool(row["changeable"])

    refundable=parse_bool(row["refundable"])

    try:
        seats_available=int(row["available_seats"])
    except ValueError as e:
        raise ValueError(f"Invalid seats available data. Error: {e}")
    
    try:
        customer_rating=float(row["customer_rating"])
    except ValueError as e:
        raise ValueError(f"Invalid customer rating data. Error: {e}")
    
    try:
        environmental_impact = (
            float(row["environmental_measure_kg_co2e_per_passenger"])
            if row["environmental_measure_kg_co2e_per_passenger"].strip()
            else None
        )
    except ValueError as e:
        raise ValueError(f"Invalid environmental impact data. Error: {e}")

    return Trip(
        trip_id,
        trip_company,
        trip_destination,
        trip_date,
        arrival_date,
        departure_time,
        arrival_time,
        duration_minutes,
        price_euro,
        transfers,
        transfer_locations,
        luggage_allowance,
        changeable,
        refundable,
        seats_available,
        customer_rating,
        environmental_impact
    )

def load_trips(filename):
    trips = []
    errors = []

    with open(filename, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for line_number, row in enumerate(reader, start=2):
            try:
                trip = row_to_trip_with_validation(row)
                trips.append(trip)

            except (ValueError, TypeError, KeyError) as error:
                errors.append(
                    f"CSV line {line_number} "
                    f"({row.get('offer_id', 'unknown ID')}): {error}"
                )
    return trips, errors

if __name__ == "__main__":
    Main()