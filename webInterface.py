from datetime import date, time
from math import isfinite
from pathlib import Path

from flask import Flask, render_template, request
from main import load_trips
from tripsService import TripPlanner

VALID_COMPANIES = {"SolRuta", "Camino Express", "CostaLink", "VerdeBus", "NocheVia"}
VALID_DESTINATIONS = {"Barcelona", "Valencia", "Seville", "Bilbao", "Granada", "Malaga", "Zaragoza", "Alicante", "Cordoba", "Toledo", "Cadiz", "San Sebastian", "Santiago de Compostela", "Salamanca", "Murcia"}

FORM_FIELDS = (
    ("company", "Company", "e.g. SolRuta", list(VALID_COMPANIES),"select"),
    ("destination", "Destination", "e.g. Barcelona", list(VALID_DESTINATIONS),"select"),
    ("desired_date", "Travel date", "YYYY-MM-DD", None,"date"),
    ("max_price", "Maximum price (EUR)", "e.g. 50", None,"text"),
    ("min_rating", "Minimum rating", "e.g. 4", None,"text"),
    ("max_transfers", "Maximum transfers", "e.g. 1", None,"text"),
    ("number_of_seats", "Seats needed", "e.g. 2", None,"text"),
    ("arrival_date", "Arrival date", "YYYY-MM-DD", None,"date"),
    ("departure_time", "Departure time", "HH:MM", None,"time"),
    ("arrival_time", "Arrival time", "HH:MM", None,"time"),
    ("luggage_allowance", "Minimum luggage allowance (kg)", "e.g. 15", None,"text"),
    ("changeable", "Changes allowed", None, ["TRUE", "FALSE"], "radio"),
    ("refundable", "Refundability", None, ["TRUE", "FALSE"], "radio"),
)


def _parse_search(values):
    query = {}
    errors = []

    for name, label, placeholder, options, field_type in FORM_FIELDS:
        raw_values = [
            value.strip()
            for value in values.get(name, [])
            if value.strip()
        ]
        if not raw_values:
            continue

        try:
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
            if name == "desired_date":
                date.fromisoformat(raw_value)
                query[name] = raw_value
            elif name == "arrival_date":
                query[name] = date.fromisoformat(raw_value)
            elif name in ("departure_time", "arrival_time"):
                query[name] = time.fromisoformat(raw_value)
            elif name in ("max_price", "min_rating"):
                query[name] = float(raw_value)
                if not isfinite(query[name]):
                    raise ValueError("must be a finite number")
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


def create_app(planner, loaded_count):
    app = Flask(__name__)

    @app.get("/")
    def search_trips():
        values = request.args.to_dict(flat=False)
        if not values:
            return render_template(
                "search.html",
                fields=FORM_FIELDS,
                values={},
                errors=[],
                results=None,
                loaded_count=loaded_count,
            )

        query, errors = _parse_search(values)
        results = planner.find_trips(**query) if not errors else None
        
        return (
            render_template(
                "search.html",
                fields=FORM_FIELDS,
                values={
                    name: entries if name in ("company", "destination") else entries[-1]
                    for name, entries in values.items()
                },
                errors=errors,
                results=results,
                loaded_count=loaded_count,
            ),
            
            400 if errors else 200,
        )

    return app


def run_web_interface(host="127.0.0.1", port=8000):
    csv_path = Path(__file__).resolve().parent / "data" / "trips.csv"
    trips, errors = load_trips(csv_path)
    print(f"Loaded {len(trips)} valid trip(s) from {csv_path}.")
    if errors:
        print(f"Skipped {len(errors)} invalid trip row(s):")
        for error in errors:
            print(f"  {error}")

    planner = TripPlanner()
    planner.add_trips(trips)

    app = create_app(planner, len(trips))
    
    app.run(host=host, port=port, threaded=True, use_reloader=False)

if __name__ == "__main__":
    run_web_interface()
