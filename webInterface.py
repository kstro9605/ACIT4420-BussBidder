from datetime import date, time
from hmac import compare_digest
from pathlib import Path
import secrets
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, redirect, render_template, request, session, url_for

from dataLoader import load_trips
from priority import PriorityType, Qualifier, QualifierOperator
from priorityHierarchy import Hierarchy
from tripsService import TripPlanner
from user import User
from constants import *

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
        results = planner.find_trips(selected_detail)
        return render_template(
            "details.html",
            fields=FORM_FIELDS,
            values={},
            errors=[],
            results=results
        )

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
            weighted_results = user.hierarchy.score(results)

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
        profile_values = {
            "name": user.name,
            "email": user.email,
            "theme": user.theme,
        }
        priority_values = None

        if request.method == "POST":
            if not validate_csrf():
                return "Invalid or expired form token. Reload and try again.", 400

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

        return render_template(
            "manage.html",
            user=user,
            priorities=priority_values or _priority_form_data(user),
            errors=errors,
            profile_errors=profile_errors,
            profile_values=profile_values,
            theme_options=THEME_OPTIONS,
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
