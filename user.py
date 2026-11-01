from dataclasses import dataclass
from datetime import date, time

from priorityHierarchy import Hierarchy


@dataclass(frozen=True)
class Booking:
    booking_id: str
    trip_id: str
    trip_company: str
    trip_destination: str
    trip_date: date
    departure_time: time
    ticket_count: int
    passenger_names: tuple[str, ...]
    total: float
    booked_by_name: str | None
    booked_by_email: str | None


class User():
    hierarchy: Hierarchy

    def __init__(
        self, username, password, email, name, theme="green-light", is_admin=False
    ):
        self.username = username
        self.password = password
        self.name = name
        self.email = email
        self.theme = theme
        self.is_admin = is_admin
        self.booked_trips: list[Booking] = []

    def set_hierarchy(self, hierarchy):
        self.hierarchy = hierarchy
