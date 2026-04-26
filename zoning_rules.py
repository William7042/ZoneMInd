
#taken from Zoning Resolution
ZONING_RULES = {
    "R1":  {"max_far": 0.50},
    "R2":  {"max_far": 0.50},
    "R2X": {"max_far": 0.85},
    "R3":  {"max_far": 0.50},
    "R4":  {"max_far": 0.75},
    "R4B": {"max_far": 0.90},
    "R5":  {"max_far": 1.25},
    "R5B": {"max_far": 1.35},
    "R5D": {"max_far": 2.00},
    "R6":  {"max_far": 2.20},
    "R6A": {"max_far": 3.00},
    "R6B": {"max_far": 2.00},
    "R7":  {"max_far": 3.44},
    "R7A": {"max_far": 4.00},
    "R7B": {"max_far": 3.00},
    "R7D": {"max_far": 4.20},
    "R7X": {"max_far": 5.00},
    "R8":  {"max_far": 6.02},
    "R8A": {"max_far": 6.02},
    "R8B": {"max_far": 4.00},
    "R9":  {"max_far": 7.52},
    "R9A": {"max_far": 7.52},
    "R9D": {"max_far": 9.00},
    "R10": {"max_far": 10.00},
}

def get_far(zone_code):
    # strip suffixes like R6-1, R7-2 etc
    # try exact match first, then base zone
    if zone_code in ZONING_RULES:
        return ZONING_RULES[zone_code]["max_far"]
    base = zone_code.split("-")[0]
    if base in ZONING_RULES:
        return ZONING_RULES[base]["max_far"]
    return None