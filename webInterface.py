from datetime import date, time
from hmac import compare_digest
from math import isfinite
from pathlib import Path
import secrets

from flask import Flask, redirect, render_template, request, session, url_for
from dataLoader import load_trips
from priority import Priority, PriorityType, Qualifier, QualifierOperator
from priorityHierarchy import Hierarchy
from tripsService import TripPlanner
from user import User
from werkzeug.security import check_password_hash, generate_password_hash

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
        if not raw_values and field_type not in ("date", "time"):
            continue

        try:
            if field_type in ("date", "time"):
                
                is_flexible = (
                    values.get(f"{name}_is_flexible", [""])[-1].lower() == "true"
                )
                if is_flexible:
                    start_value = values.get(f"{name}_from", [""])[-1].strip()
                    end_value = values.get(f"{name}_to", [""])[-1].strip()
                    if not start_value or not end_value:
                        raise ValueError(f"enter both the start and end {field_type}s")

                    parse_value = date.fromisoformat if field_type == "date" else time.fromisoformat
                    start = parse_value(start_value)
                    end = parse_value(end_value)
                    if start > end:
                        raise ValueError(f"start {field_type} must be on or before end {field_type}")

                    query[f"{name}_from"] = start
                    query[f"{name}_to"] = end
                    continue

                if not raw_values:
                    continue
                raw_value = raw_values[-1]
                parse_value = date.fromisoformat if field_type == "date" else time.fromisoformat
                parse_value(raw_value)
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
            if name in ("departure_time", "arrival_time"):
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


def _priority_form_data(user, submitted=None):
    submitted = submitted or {}
    has_submitted_data = bool(submitted)
    selected_names = (
        set(submitted.getlist("priority_type")) if has_submitted_data else set()
    )
    saved_priorities = user.hierarchy.priorities
    entries = []

    for priority_type in PriorityType:
        saved = saved_priorities.get(priority_type)
        if has_submitted_data:
            priority_is_selected = priority_type.name in selected_names
        else:
            priority_is_selected = saved is not None

        qualifier = saved.qualifier if saved else None

        if priority_type.field_name in ("departure_time", "arrival_time"):
            operator_options = (QualifierOperator.EARLIER_THAN,QualifierOperator.LATER_THAN)
        else:
            operator_options = (QualifierOperator.LESS_THAN, QualifierOperator.MORE_THAN)
            
        entries.append(
            {
                "type": priority_type,
                "selected": priority_is_selected,
                "weight": submitted.get(
                    f"weight_{priority_type.name}",
                    str(saved.weight if saved else 0),
                ),
                "qualifier_enabled": (
                    submitted.get(f"qualifier_enabled_{priority_type.name}") == "on" if has_submitted_data
                    else qualifier is not None
                ),
                "operator_options": operator_options,
                "operator": submitted.get(
                    f"operator_{priority_type.name}",
                    qualifier.operator.name if qualifier else operator_options[0].name,
                ),
                "qualifier_value": submitted.get(
                    f"qualifier_value_{priority_type.name}",
                    qualifier.value.isoformat() if qualifier and hasattr(qualifier.value, "isoformat")
                    else str(qualifier.value) if qualifier else "",
                ),
                "qualifier_type": (
                    "time" if priority_type.field_name in ("departure_time", "arrival_time")
                    else "number"
                ),
            }
        )

    return entries


def _save_priority_form(user, form):
    errors = []
    selected_names = form.getlist("priority_type")
    priorities = []
    total_weight = 0
    if len(selected_names) != len(set(selected_names)):
        errors.append("Each priority can only be selected once.")

    for name in selected_names:
        try:
            priority_type = PriorityType[name]
        except KeyError:
            errors.append(f"Unknown priority type: {name}.")
            continue

        try:
            weight = int(form.get(f"weight_{name}", ""))
            if not 0 <= weight <= 100:
                raise ValueError("weight must be between 0 and 100")
        except ValueError as error:
            errors.append(f"{name.replace('_', ' ').title()}: {error}.")
            continue

        total_weight += weight
        qualifier = None
        if (
            priority_type is not PriorityType.FLEXIBLE
            and form.get(f"qualifier_enabled_{name}") == "on"
        ):
            operator_name = form.get(f"operator_{name}", "")
            if priority_type.field_name in ("departure_time", "arrival_time"):
                operator_options = (
                    {"EARLIER_THAN"}
                    if priority_type.name.endswith("BEFORE")
                    else {"LATER_THAN"}
                )
            else:
                operator_options = {"LESS_THAN", "MORE_THAN"}
            if operator_name not in operator_options:
                errors.append(f"Choose a valid qualifier operator for {name}.")
                continue

            raw_value = form.get(f"qualifier_value_{name}", "").strip()
            try:
                if not raw_value:
                    raise ValueError("enter a qualifier value")
                value = (
                    time.fromisoformat(raw_value)
                    if priority_type.field_name in ("departure_time", "arrival_time")
                    else float(raw_value)
                )
                if isinstance(value, float) and not isfinite(value):
                    raise ValueError("enter a finite number")
                qualifier = Qualifier(QualifierOperator[operator_name], value)
            except ValueError as error:
                errors.append(f"{name.replace('_', ' ').title()}: {error}.")
                continue

        priorities.append(
            {
                "priority_type": priority_type,
                "priority_weight": weight,
                **({"priority_qualifier": qualifier} if qualifier else {}),
            }
        )

    if total_weight > 100:
        errors.append(f"Priority weights total {total_weight}; the maximum is 100.")
    if errors:
        return errors

    hierarchy = Hierarchy()
    hierarchy.create_priorities(priorities)
    user.set_hierarchy(hierarchy)
    return []


def create_app(planner, loaded_count):
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
    accounts = {}
    app.extensions["user_accounts"] = accounts

    def csrf_token():
        token = session.get("_csrf_token")
        if token is None:
            token = secrets.token_urlsafe(32)
            session["_csrf_token"] = token
        return token

    def validate_csrf():
        submitted = request.form.get("_csrf_token", "")
        expected = session.get("_csrf_token", "")
        return bool(expected) and compare_digest(submitted, expected)

    def current_user():
        email = session.get("user_email")
        user = accounts.get(email) if email else None
        return accounts.get(email) if email else None

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

    @app.route("/account", methods=["GET", "POST"])
    def account():
        errors = []
        form_values = {}

        if request.method == "POST":
            if not validate_csrf():
                return "Invalid or expired form token. Reload and try again.", 400

            action = request.form.get("action")
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            name = request.form.get("name", "").strip()
            form_values = {"email": email, "name": name}

            if action == "register":
                name = form_values["name"]
                if not name:
                    errors.append("Enter your name.")
                if "@" not in email or any(character.isspace() for character in email):
                    errors.append("Enter a valid email address.")
                if email in accounts:
                    errors.append("An account with that email already exists.")
                if len(password) < 8:
                    errors.append("Password must be at least 8 characters.")

                if not errors:
                    user = User(
                        username=email,
                        password=generate_password_hash(password),
                        email=email,
                        name=name,
                    )
                    user.set_hierarchy(Hierarchy())
                    accounts[email] = user
                    session.clear()
                    session["user_email"] = email
                    return redirect(url_for("manage_user"))
            elif action == "login":
                user = accounts.get(email)
                if not user or not check_password_hash(user.password, password):
                    errors.append("Invalid email or password.")
                else:
                    session.clear()
                    session["user_email"] = email
                    return redirect(url_for("manage_user"))
            else:
                errors.append("Choose login or registration.")

        return render_template(
            "account.html",
            errors=errors,
            values=form_values,
            csrf_token=csrf_token(),
        )

    @app.route("/manage", methods=["GET", "POST"])
    def manage_user():
        user = current_user()
        if user is None:
            return redirect(url_for("account"))

        errors = []
        profile_errors = []
        profile_values = {"name": user.name, "email": user.email}
        priority_values = None

        if request.method == "POST":
            if not validate_csrf():
                return "Invalid or expired form token. Reload and try again.", 400

            action = request.form.get("action")
            if action == "profile":
                print("Profile action")
                name = request.form.get("name", "").strip()
                email = request.form.get("email", "").strip().lower()
                new_password = request.form.get("new_password", "")
                profile_values = {"name": name, "email": email}
                if not name:
                    profile_errors.append("Enter your name.")
                if "@" not in email or any(character.isspace() for character in email):
                    profile_errors.append("Enter a valid email address.")
                if email != user.email and email in accounts:
                    profile_errors.append("An account with that email already exists.")
                if new_password and len(new_password) < 8:
                    profile_errors.append("New password must be at least 8 characters.")
                if not profile_errors:
                    del accounts[user.email]
                    user.name = name
                    user.email = email
                    user.username = email
                    if new_password:
                        user.password = generate_password_hash(new_password)
                    accounts[email] = user
                    session["user_email"] = email
            elif action == "priorities":
                errors = _save_priority_form(user, request.form)
                priority_values = _priority_form_data(user, request.form)
            else:
                errors.append("Unknown update action.")

        return render_template(
            "manage.html",
            user=user,
            priorities=priority_values or _priority_form_data(user),
            errors=errors,
            profile_errors=profile_errors,
            profile_values=profile_values,
            total_weight=user.hierarchy.total_weight,
            csrf_token=csrf_token(),
        )

    @app.post("/logout")
    def logout():
        if not validate_csrf():
            return "Invalid or expired form token. Reload and try again.", 400
        session.clear()
        return redirect(url_for("account"))

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
