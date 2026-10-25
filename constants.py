VALID_COMPANIES = {"SolRuta", "Camino Express", "CostaLink", "VerdeBus", "NocheVia"}
VALID_DESTINATIONS = {"Barcelona", "Valencia", "Seville", "Bilbao", "Granada", "Malaga", "Zaragoza", "Alicante", "Cordoba", "Toledo", "Cadiz", "San Sebastian", "Santiago de Compostela", "Salamanca", "Murcia"}
DEFAULT_THEME = "green-light"
THEME_OPTIONS = (
    ("blue-light", "Blue - light"),
    ("blue-dark", "Blue - dark"),
    ("red-light", "Red - light"),
    ("red-dark", "Red - dark"),
    ("green-light", "Green - light"),
    ("green-dark", "Green - dark"),
    ("orange-light", "Orange - light"),
    ("orange-dark", "Orange - dark"),
    ("pink-light", "Pink - light"),
    ("pink-dark", "Pink - dark"),
    ("purple-light", "Purple - light"),
    ("purple-dark", "Purple - dark"),
)
VALID_THEMES = {theme for theme, _label in THEME_OPTIONS}

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
