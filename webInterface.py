import csv
import json
import secrets
from datetime import time
from pathlib import Path
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, request, session, url_for

from dataLoader import load_trips
from priority import PriorityType, Qualifier, QualifierOperator
from priorityHierarchy import Hierarchy, OverWeightPrioritiesError, InvalidPriorityBundleException
from tripsService import TripPlanner
from user import Booking, User
from constants import DEFAULT_THEME, FORM_FIELDS, THEME_OPTIONS, VALID_DESTINATIONS, VALID_THEMES

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
        requires_qualifier = priority_type.field_name in (
            "departure_time",
            "arrival_time",
        )
        if has_submitted_data:
            priority_is_selected = priority_type.name in selected_names
        else:
            priority_is_selected = saved is not None

        qualifier = saved.qualifier if saved else None

        if priority_type.field_name in ("departure_time", "arrival_time"):
            operator_options = (
                (QualifierOperator.EARLIER_THAN,)
                if priority_type.name.endswith("BEFORE")
                else (QualifierOperator.LATER_THAN,)
            )
        else:
            operator_options = (QualifierOperator.LESS_THAN, QualifierOperator.MORE_THAN)
        if requires_qualifier:
            qualifier_enabled = True
        elif has_submitted_data:
            qualifier_enabled = (
                submitted.get(f"qualifier_enabled_{priority_type.name}") == "on"
            )
        else:
            qualifier_enabled = qualifier is not None

        entries.append(
            {
                "type": priority_type,
                "selected": priority_is_selected,
                "weight": submitted.get(
                    f"weight_{priority_type.name}",
                    str(saved.weight if saved else 0),
                ),
                "qualifier_enabled": qualifier_enabled,
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
        requires_qualifier = priority_type.field_name in (
            "departure_time",
            "arrival_time",
        )
        if priority_type is not PriorityType.FLEXIBLE and (
            requires_qualifier
            or form.get(f"qualifier_enabled_{name}") == "on"
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
    try:
        hierarchy.create_priorities(priorities)
    except OverWeightPrioritiesError as error:
        errors.append(f"Error creating priorities: {error}")
        return errors
    except InvalidPriorityBundleException as error:
        errors.append(f"Error creating priorities: {error}")
        return errors
    user.set_hierarchy(hierarchy)
    return []

def create_app(planner, loaded_count):
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(32)
    accounts = {}
    app.extensions["user_accounts"] = accounts
    booked_trips = []
    app.extensions["booked_trips"] = booked_trips

    #This is just to access all bookings and isn't a 
    #secure way to handle admin accounts. 
    # In a real application, 
    # you'd want to implement a more secure authentication 
    # and authorization system.
    admin_password = "HugeSecurityRisk"
    admin = User(
        username="bb_admin",
        password=generate_password_hash(admin_password),
        email="admin@bb_admin.com",
        name="Bookings administrator",
        is_admin=True,
    )
    admin.set_hierarchy(Hierarchy())
    accounts[admin.email] = admin


    def current_user():
        email = session.get("user_email")
        return accounts.get(email) if email else None

    @app.context_processor
    def inject_user_theme():
        user = current_user()
        return {"user_theme": user.theme if user else DEFAULT_THEME}

    @app.get("/")
    def landing_page():
        return render_template(
            "index.html",
            values={},
            errors=[],
        )

    @app.get("/details")
    def show_details():
        selected_detail = request.args.get("detail_view")
        selected_trip = planner.find_trips(selected_detail)[0]
        priority_minded = request.args.get("priority_minded") == "true"
        priority_score = None
        has_priorities = False

        if priority_minded:
            user = current_user()
            if user is not None:
                has_priorities = bool(user.hierarchy.priorities)
                all_trips = planner.find_trips()
               
                priority_score = next(
                    (
                        score
                        for score, trip in user.hierarchy.score(all_trips)
                        if trip.trip_id == selected_detail
                    ),
                    None,
                )

        return render_template(
            "details.html",
            trip=selected_trip,
            priority_minded=priority_minded,
            priority_score=priority_score,
            has_priorities=has_priorities,
        )

    @app.route("/booking", methods=["GET", "POST"])
    def booking():
        selected_trip = (
            request.form.get("booking_view")
            if request.method == "POST"
            else request.args.get("booking_view")
        )
        trips = planner.find_trips(selected_trip)
        if len(trips) != 1:
            return render_template(
                "booking.html",
                booking_view=selected_trip,
                errors=["Attempting to book for a non existing trip"],
                results=[],
                booking_confirmation=None,
            ), 404

        trip = trips[0]
        errors = []
        booking_confirmation = None
        if request.method == "POST":
            try:
                number_to_book = int(request.form.get("tickets_to_book", ""))
            except ValueError:
                number_to_book = 0

            passenger_names = [
                name.strip() for name in request.form.getlist("passenger_names")
            ]
            if number_to_book < 1:
                errors.append("Enter a valid number of tickets.")
            elif number_to_book > trip.seats_available:
                errors.append("There are not enough seats available for this booking.")
            if len(passenger_names) != number_to_book or any(
                not name for name in passenger_names
            ):
                errors.append("Enter a name for every ticket.")

            if not errors:
                trip.seats_available -= number_to_book
                user = current_user()
                booking = Booking(
                    booking_id=f"BOOKING_{len(booked_trips) + 1}_{trip.trip_id}",
                    trip_id=trip.trip_id,
                    trip_company=trip.trip_company,
                    trip_destination=trip.trip_destination,
                    trip_date=trip.trip_date,
                    departure_time=trip.departure_time,
                    ticket_count=number_to_book,
                    passenger_names=tuple(passenger_names),
                    total=trip.trip_price * number_to_book,
                    booked_by_name=user.name if user else None,
                    booked_by_email=user.email if user else None,
                )
                booked_trips.append(booking)
                planner.store_booking_in_file(booking)  
                if user is not None:
                    user.booked_trips.append(booking)
                booking_confirmation = {
                    "ticket_count": booking.ticket_count,
                    "passenger_names": booking.passenger_names,
                    "total": booking.total,
                    "booking_id": booking.booking_id,
                }

        return render_template(
            "booking.html",
            booking_view=selected_trip,
            errors=errors,
            trip=trip,
            booking_confirmation=booking_confirmation,
        ), 400 if errors else 200

    @app.get("/search")
    def search_trips():
        values = request.args.to_dict(flat=False)
        weighted_search = request.args.get("search_mode") == "weighted"
        if not values:
            return render_template(
                "search.html",
                fields=FORM_FIELDS,
                values={},
                errors=[],
                results=None,
                loaded_count=loaded_count,
                weighted_search=weighted_search,
            )

        query, errors = planner.parse_search(values)
        results = planner.find_trips(**query) if not errors else None

        if weighted_search:
            user = current_user()
            weighted_results = user.hierarchy.score(results)
            return (
                render_template(
                    "search.html",
                    fields=FORM_FIELDS,
                    values={
                        name: entries if name in ("company", "destination") else entries[-1]
                        for name, entries in values.items()
                    },
                    errors=errors,
                    results=weighted_results,
                    loaded_count=loaded_count,
                    weighted_search=weighted_search,
                ),
                400 if errors else 200,
            )

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
                weighted_search=weighted_search,
            ),
            400 if errors else 200,
        )

    @app.get("/admin/bookings")
    def system_bookings():
        user = current_user()
        if user is None:
            return redirect(url_for("account"))
        if not user.is_admin:
            return "Forbidden", 403
        return render_template("system_bookings.html", bookings=booked_trips)

    @app.get("/specialized-search")
    def user_search():
        user = current_user()
        if user is None:
            return redirect(url_for("account"))

        results = None
        errors = []
        submitted = request.args.get("search") == "1"
        values = request.args.to_dict()

        weighted_results = None
        if submitted:
            raw_values = request.args.to_dict(flat=False)
            query, errors = planner.parse_search(raw_values)
            results = planner.find_trips(**query) if not errors else None
            weighted_results = user.hierarchy.score(results)[:6]

        return render_template(
            "user_search.html",
            user=user,
            destinations=sorted(VALID_DESTINATIONS),
            values=values,
            errors=errors,
            results=weighted_results,
            has_priorities=bool(user.hierarchy.priorities),
        ), 400 if errors else 200

    @app.route("/account", methods=["GET", "POST"])
    def account():
        errors = []
        form_values = {}

        if request.method == "POST":
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
        )

    @app.route("/manage", methods=["GET", "POST"])
    def manage_user():
        user = current_user()
        if user is None:
            return redirect(url_for("account"))

        errors = []
        profile_errors = []
        profile_values = {
            "name": user.name,
            "email": user.email,
            "theme": user.theme,
        }
        priority_values = None

        if request.method == "POST":

            action = request.form.get("action")
            if action == "profile":
                name = request.form.get("name", "").strip()
                email = request.form.get("email", "").strip().lower()
                new_password = request.form.get("new_password", "")
                theme = request.form.get("theme", DEFAULT_THEME)
                profile_values = {"name": name, "email": email, "theme": theme}
                if not name:
                    profile_errors.append("Enter your name.")
                if "@" not in email or any(character.isspace() for character in email):
                    profile_errors.append("Enter a valid email address.")
                if theme not in VALID_THEMES:
                    profile_errors.append("Choose a valid page theme.")
                if email != user.email and email in accounts:
                    profile_errors.append("An account with that email already exists.")
                if new_password and len(new_password) < 8:
                    profile_errors.append("New password must be at least 8 characters.")
                if not profile_errors:
                    del accounts[user.email]
                    user.name = name
                    user.email = email
                    user.username = email
                    user.theme = theme
                    if new_password:
                        user.password = generate_password_hash(new_password)
                    accounts[email] = user
                    session["user_email"] = email
            elif action == "priorities":
                errors = _save_priority_form(user, request.form)
                priority_values = _priority_form_data(user, request.form)
            else:
                errors.append("Unknown update action.")

        with (Path.cwd() / "registered_users.csv").open(
            "w", newline="", encoding="utf-8"
        ) as users_file:
            writer = csv.DictWriter(
                users_file,
                fieldnames=("name", "email", "theme", "priorities", "booking_ids"),
            )
            writer.writeheader()
            for registered_user in accounts.values():
                if registered_user.is_admin:
                    continue
                priorities = [
                    {
                        "type": priority.priority_type.name,
                        "weight": priority.weight,
                        "qualifier": (
                            {
                                "operator": priority.qualifier.operator.name,
                                "value": (
                                    priority.qualifier.value.isoformat()
                                    if hasattr(priority.qualifier.value, "isoformat")
                                    else priority.qualifier.value
                                ),
                            }
                            if priority.qualifier
                            else None
                        ),
                    }
                    for priority in registered_user.hierarchy.priorities.values()
                ]
                writer.writerow(
                    {
                        "name": registered_user.name,
                        "email": registered_user.email,
                        "theme": registered_user.theme,
                        "priorities": json.dumps(priorities, ensure_ascii=False),
                        "booking_ids": json.dumps(
                            [
                                booking.booking_id
                                for booking in registered_user.booked_trips
                            ]
                        ),
                    }
                )

        return render_template(
            "manage.html",
            user=user,
            priorities=priority_values or _priority_form_data(user),
            errors=errors,
            profile_errors=profile_errors,
            profile_values=profile_values,
            theme_options=THEME_OPTIONS,
            total_weight=user.hierarchy.total_weight,
            booked_trips=user.booked_trips,
            is_admin=user.is_admin,
        )

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("account"))
    
    return app

def run_web_interface(host="127.0.0.1", port=8000):
    csv_path = Path(__file__).resolve().parent / "data" / "trips.csv"
    trips, errors = load_trips(csv_path)
    print(f"Loaded {len(trips)} valid trip(s) from {csv_path}.")
    if errors:
        with open("error.output", "a", encoding="utf-8") as error_file:
            message = f"Skipped {len(errors)} invalid trip row(s):"
            print(message)
            print(message, file=error_file)
            for error in errors:
                message = f"  {error}"
                print(message)
                print(message, file=error_file)

    planner = TripPlanner()
    planner.add_trips(trips)

    app = create_app(planner, len(trips))
    
    app.run(host=host, port=port, threaded=True, use_reloader=False)
