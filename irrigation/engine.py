"""Irrigation recommendation engine (simplified FAO-56 water balance).

Pipeline
  1. ET0  - reference evapotranspiration (Hargreaves)
  2. ETc  - crop water use = Kc x ET0
  3. TAW  - total available water in the root zone
  4. Dr   - current root-zone depletion from measured soil moisture
  5. RAW  - readily available water = p x TAW (stress threshold)
  6. Decide, then convert the needed depth to litres and pump hours.
"""
import math
from datetime import date

from .data import CROPS, METHODS, SOILS


def extraterrestrial_radiation(lat_deg, doy):
    """Ra in mm/day (FAO-56 eq. 21, converted with 0.408)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    x = max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta)))
    ws = math.acos(x)
    ra_mj = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(delta)
        + math.cos(phi) * math.cos(delta) * math.sin(ws)
    )
    return ra_mj * 0.408


def hargreaves_et0(tmax, tmin, lat_deg, doy):
    """ET0 (mm/day) = 0.0023 (Tmean + 17.8) sqrt(Tmax - Tmin) Ra."""
    tmean = (tmax + tmin) / 2
    ra = extraterrestrial_radiation(lat_deg, doy)
    return max(0.0, 0.0023 * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * ra)


def humidity_adjustment(humidity):
    """Hargreaves ignores humidity, so trim demand slightly above 60% RH."""
    return 1 - max(0.0, humidity - 60) / 200


def effective_rain(forecast_mm):
    """Ignore showers under 5 mm; count 80% of larger events."""
    return 0.8 * forecast_mm if forecast_mm >= 5 else 0.0


def recommend(d, doy=None):
    """Return a recommendation dict from validated inputs `d`."""
    crop, soil, eff = CROPS[d["crop"]], SOILS[d["soil"]], METHODS[d["method"]]
    doy = doy or date.today().timetuple().tm_yday

    et0 = hargreaves_et0(d["tmax"], d["tmin"], d["lat"], doy) * humidity_adjustment(d["humidity"])
    kc = crop["kc"][d["stage"]]
    etc = et0 * kc
    rain_eff = effective_rain(d["rain"])

    taw = soil["awc"] * crop["root_m"]
    raw = crop["p"] * taw
    remaining = (d["moisture"] - soil["wp"]) / (soil["fc"] - soil["wp"])
    remaining = max(0.0, min(1.0, remaining))
    depletion = (1 - remaining) * taw

    projected = max(0.0, depletion + etc - rain_eff)     # depletion after today and rain
    irrigate = projected >= raw
    rain_saves_trip = (not irrigate) and (depletion + etc >= raw)
    days_left = max(0.0, (raw - depletion) / etc) if etc > 0 else 99.0

    net = min(projected, taw) if irrigate else 0.0
    gross = net / eff
    litres = gross * d["area"]                            # 1 mm over 1 m2 = 1 L
    hours = litres / d["flow"]

    if irrigate and remaining < 0.25:
        level, message = "urgent", "Soil is dry. Irrigate today."
    elif irrigate:
        level, message = "irrigate", "Irrigate within the next day."
    elif rain_saves_trip:
        level, message = "skip", "Forecast rain covers crop needs. Skip irrigation."
    else:
        level, message = "ok", f"Soil moisture is fine. Check again in {max(1, int(days_left))} day(s)."

    return {
        "level": level, "message": message,
        "et0": round(et0, 2), "kc": kc, "etc": round(etc, 2),
        "rain_effective": round(rain_eff, 1),
        "taw": round(taw, 1), "raw": round(raw, 1), "depletion": round(depletion, 1),
        "moisture_pct": round(remaining * 100), "trigger_pct": round((1 - crop["p"]) * 100),
        "net_mm": round(net, 1), "gross_mm": round(gross, 1),
        "litres": round(litres), "hours": round(hours, 1),
        "days_left": round(days_left, 1), "efficiency": round(eff * 100),
    }
