"""Input validation. Returns clean values or a list of readable errors."""
from .data import CROPS, METHODS, SOILS, STAGES

# field: (label, minimum, maximum)
NUMERIC_RULES = {
    "moisture": ("Soil moisture (%)", 0, 60),
    "tmax": ("Max temperature (°C)", -10, 55),
    "tmin": ("Min temperature (°C)", -20, 45),
    "humidity": ("Humidity (%)", 0, 100),
    "rain": ("Rain forecast (mm)", 0, 500),
    "lat": ("Latitude (°N)", -60, 60),
    "area": ("Field area (m²)", 1, 10_000_000),
    "flow": ("Pump flow (L/h)", 1, 1_000_000),
}

CHOICES = {
    "crop": ("Crop", CROPS),
    "stage": ("Growth stage", STAGES),
    "soil": ("Soil type", SOILS),
    "method": ("Method", METHODS),
}


def validate(form):
    """Return (clean_dict, errors). clean_dict is empty when errors exist."""
    clean, errors = {}, []

    for key, (label, options) in CHOICES.items():
        value = form.get(key)
        if value not in options:
            errors.append(f"{label}: choose one of the listed options.")
        else:
            clean[key] = value

    for key, (label, low, high) in NUMERIC_RULES.items():
        raw = form.get(key)
        try:
            number = float(raw)
        except (TypeError, ValueError):
            errors.append(f"{label}: enter a number.")
            continue
        if number != number or number in (float("inf"), float("-inf")):
            errors.append(f"{label}: enter a finite number.")
        elif not low <= number <= high:
            errors.append(f"{label}: must be between {low} and {high}.")
        else:
            clean[key] = number

    if "tmax" in clean and "tmin" in clean and clean["tmax"] < clean["tmin"]:
        errors.append("Max temperature must not be lower than min temperature.")

    return ({} if errors else clean), errors
