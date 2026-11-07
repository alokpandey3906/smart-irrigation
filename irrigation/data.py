"""Reference tables used by the engine.

Values are simplified from FAO Irrigation and Drainage Paper No. 56
(Allen et al., 1998). Replace them with local agronomy data for real use.

kc      : crop coefficient for each growth stage
root_m  : effective root depth in metres
p       : fraction of total available water that may be used before stress
"""

STAGES = ("initial", "development", "mid", "late")

CROPS = {
    "Wheat":     {"kc": {"initial": 0.40, "development": 0.80, "mid": 1.15, "late": 0.40}, "root_m": 1.0, "p": 0.55},
    "Rice":      {"kc": {"initial": 1.05, "development": 1.10, "mid": 1.20, "late": 0.90}, "root_m": 0.5, "p": 0.20},
    "Maize":     {"kc": {"initial": 0.40, "development": 0.80, "mid": 1.20, "late": 0.60}, "root_m": 1.0, "p": 0.55},
    "Tomato":    {"kc": {"initial": 0.60, "development": 0.90, "mid": 1.15, "late": 0.80}, "root_m": 0.7, "p": 0.40},
    "Potato":    {"kc": {"initial": 0.50, "development": 0.80, "mid": 1.15, "late": 0.75}, "root_m": 0.5, "p": 0.35},
    "Sugarcane": {"kc": {"initial": 0.40, "development": 0.85, "mid": 1.25, "late": 0.75}, "root_m": 1.2, "p": 0.65},
}

# awc: available water capacity (mm of water per metre of soil)
# fc / wp: field capacity / wilting point (% by volume)
SOILS = {
    "Sandy": {"awc": 80,  "fc": 15, "wp": 7},
    "Loam":  {"awc": 150, "fc": 28, "wp": 13},
    "Clay":  {"awc": 180, "fc": 38, "wp": 20},
}

# Application efficiency of each irrigation method.
METHODS = {"Drip": 0.90, "Sprinkler": 0.75, "Flood": 0.55}
