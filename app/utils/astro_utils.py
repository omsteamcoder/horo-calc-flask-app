from ..constants import RASI_NAMES, PLANET_NAMES, ZODIAC_SIGNS, DOSHAM_RULES

def get_navamsa_rasi(planet):
    """
    Calculate the Navamsa Rasi (sign) for a given planet using Kerykeion.
    """
    # Map sign string to index
    rasi_order = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    rasi_index = rasi_order.index(planet.sign)
    
    # Get degrees within the sign (0–30°)
    degrees_in_sign = planet.position  # Kerykeion gives 0–30° within the sign
    
    # Determine navamsa segment (each navamsa is 3°20' = 3.3333°)
    navamsa_index = int(degrees_in_sign // 3.3333)
    
    # Determine the base Navamsa Rasi start based on the Rasi element group
    # Fire signs start from Aries (0), Earth from Capricorn (9), Air from Libra (6), Water from Cancer (3)
    if rasi_index in [0, 4, 8]:      # Fire
        base = 0
    elif rasi_index in [1, 5, 9]:    # Earth
        base = 9
    elif rasi_index in [2, 6, 10]:   # Air
        base = 6
    elif rasi_index in [3, 7, 11]:   # Water
        base = 3

    # Calculate final Navamsa Rasi index (wrap around 12 signs)
    navamsa_rasi_index = (base + navamsa_index) % 12
    rasi_order = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    navamsa_rasi = RASI_NAMES[rasi_order[navamsa_rasi_index]]  # Get Tamil name

    return navamsa_rasi


def format_dasha_periods(dasha_periods):
    """
    Convert decimal years to 'years, months, days' format in Tamil.
    """
    formatted_dasha_periods = []
    
    for dasha in dasha_periods:
        planet, years_fraction = dasha.split(": ")
        years_fraction = float(years_fraction.split()[0])  # Extract numerical value

        # Convert decimal years to (years, months, days)
        years = int(years_fraction)
        remaining_months = (years_fraction - years) * 12
        months = int(remaining_months)
        days = round((remaining_months - months) * 30.4375)  # Approximate month length

        # Tamil translation for planets
        PLANET_TAMIL_NAMES = {
            "Sun": "சூரியன்",
            "Moon": "சந்திரன்",
            "Mars": "செவ்வாய்",
            "Rahu": "ராகு",
            "Jupiter": "குரு",
            "Saturn": "சனி",
            "Mercury": "புதன்",
            "Ketu": "கேது",
            "Venus": "சுக்ரன்"
        }

        # Format in Tamil
        formatted_dasha = f"{PLANET_TAMIL_NAMES[planet]} {years} வருடம், {months} மாதம், {days} நாள்"
        formatted_dasha_periods.append(formatted_dasha)

    return formatted_dasha_periods
    
def get_house_placements(native):
    """
    Calculate house placements for both Rasi and Navamsa.
    
    Also place the Lagna (Ascendant) into the first house.
    """
    rasi_order = ['Ari', 'Tau', 'Gem', 'Can', 'Leo', 'Vir', 'Lib', 'Sco', 'Sag', 'Cap', 'Aqu', 'Pis']
    tamil_rasi_names = [RASI_NAMES[r] for r in rasi_order]

    # Initialize empty houses for 12 houses
    rasi_houses = {i: [] for i in range(1, 13)}
    navamsa_houses = {i: [] for i in range(1, 13)}

    # Compute lagna index based on the ascendant's sign (for Rasi)
    lagna_index = rasi_order.index(native.ascendant.sign)
    # Also get Navamsa of the lagna
    navamsa_lagna_rasi = get_navamsa_rasi(native.ascendant)
    navamsa_lagna_index = tamil_rasi_names.index(navamsa_lagna_rasi)

    # Process standard planets
    for key in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'true_node', 'true_south_node']:
        planet = getattr(native, key)
        tamil_name = PLANET_NAMES[planet.name]

        # Rasi house: house number is determined relative to the Lagna
        planet_sign_index = rasi_order.index(planet.sign)
        house_num = (planet_sign_index - lagna_index) % 12 + 1
        rasi_houses[house_num].append(tamil_name)

        # Navamsa house: determined similarly but with Navamsa rasi
        navamsa_sign = get_navamsa_rasi(planet)
        navamsa_sign_index = tamil_rasi_names.index(navamsa_sign)
        navamsa_house_num = (navamsa_sign_index - navamsa_lagna_index) % 12 + 1
        navamsa_houses[navamsa_house_num].append(tamil_name)

    # Place the Ascendant (Lagna) in house number 1 for both charts.
    rasi_houses[1].append("லக்னம்")
    navamsa_houses[1].append("லக்னம்")

    return rasi_houses, navamsa_houses

def get_chart_placements(native):
    """
    Prepare the chart placements for Rasi and Navamsa charts.
    Include the Lagna along with other planets.
    """
    rasi_chart = {rasi: [] for rasi in RASI_NAMES.values()}
    navamsa_chart = {rasi: [] for rasi in RASI_NAMES.values()}

    for planet_key in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'true_node', 'true_south_node']:
        planet = getattr(native, planet_key)
        tamil_name = PLANET_NAMES[planet.name]

        # Rasi placement: based on the planet's sign
        rasi = RASI_NAMES[planet.sign]
        rasi_chart[rasi].append(tamil_name)

        # Navamsa placement: via helper function
        navamsa_rasi = get_navamsa_rasi(planet)
        navamsa_chart[navamsa_rasi].append(tamil_name)

    # Also add the Lagna (ascendant)
    lagna_obj = native.first_house
    rasi_lagna = RASI_NAMES[lagna_obj.sign]
    navamsa_lagna = get_navamsa_rasi(lagna_obj)
    rasi_chart[rasi_lagna].append("லக்னம்")
    navamsa_chart[navamsa_lagna].append("லக்னம்")

    return rasi_chart, navamsa_chart


# Helper functions
def get_nakshatra_pada(position):
    NAKSHATRA_LIST = [
        (0.0, 13.3333, "அஸ்வினி"), (13.3333, 26.6666, "பரணி"),
        (26.6666, 40.0, "கிருத்திகை"), (40.0, 53.3333, "ரோகிணி"),
        (53.3333, 66.6666, "மிருகசீரிஷம்"), (66.6666, 80.0, "திருவாதிரை"),
        (80.0, 93.3333, "புனர்பூசம்"), (93.3333, 106.6666, "பூசம்"),
        (106.6666, 120.0, "ஆயில்யம்"), (120.0, 133.3333, "மகம்"),
        (133.3333, 146.6666, "பூரம்"), (146.6666, 160.0, "உத்திரம்"),
        (160.0, 173.3333, "அஸ்தம்"), (173.3333, 186.6666, "சித்திரை"),
        (186.6666, 200.0, "ஸ்வாதி"), (200.0, 213.3333, "விசாகம்"),
        (213.3333, 226.6666, "அனுஷம்"), (226.6666, 240.0, "கேட்டை"),
        (240.0, 253.3333, "மூலம்"), (253.3333, 266.6666, "பூராடம்"),
        (266.6666, 280.0, "உத்திராடம்"), (280.0, 293.3333, "திருவோணம்"),
        (293.3333, 306.6666, "அவிட்டம்"), (306.6666, 320.0, "சதயம்"),
        (320.0, 333.3333, "பூரட்டாதி"), (333.3333, 346.6666, "உத்திரட்டாதி"),
        (346.6666, 360.0, "ரேவதி")
    ]
    for start, end, nakshatra in NAKSHATRA_LIST:
        if start <= position < end:
            return nakshatra, min(int((position - start) // 3.3333) + 1, 4)

# Calculate absolute positions with sign adjustment
def get_abs_pos(planet):
    sign_index = list(RASI_NAMES.keys()).index(planet.sign)
    return planet.position + (30 * sign_index)

def sign_index(sign):
    return ZODIAC_SIGNS.index(sign)

def house_difference(from_idx, to_idx):
    return ((to_idx - from_idx) % 12) + 1

def get_planet_data(data, planet_name):
    for p in data.get("நிராயன ஸ்புடங்கள்", []):
        if p["planet"] == planet_name:
            deg = sum(float(x) * 60 ** (-i) for i, x in enumerate(p["position"].split(":")))
            return p["rasi"], deg
    return None, None

def are_conjunct(rasi1, deg1, rasi2, deg2, orb=8.0):
    if rasi1 != rasi2:
        return False
    return fabs(deg1 - deg2) <= orb

def check_planet_dosham(planet, rule_houses, refs, data):
    p_rasi, _ = get_planet_data(data, planet)
    if not p_rasi:
        return False
    p_idx = sign_index(p_rasi)
    for ref_idx in refs:
        h = house_difference(ref_idx, p_idx)
        if h in rule_houses:
            return True
    return False

def calculate_doshams(data):
    results = {}

    lagna_sign = data["உதய லக்னம்"]
    lagna_idx = sign_index(lagna_sign)

    moon_sign, moon_deg = get_planet_data(data, "சந்திரன்")
    moon_idx = sign_index(moon_sign)

    venus_sign, venus_deg = get_planet_data(data, "சுக்ரன்")
    venus_idx = sign_index(venus_sign)

    # 1. Chevvai Dosham
    results["Chevvai Dosham"] = check_planet_dosham(
        DOSHAM_RULES["Chevvai"]["planet"], DOSHAM_RULES["Chevvai"]["houses"],
        refs=[lagna_idx, moon_idx, venus_idx], data=data
    )

    # 2. Rahu Dosham
    results["Rahu Dosham"] = check_planet_dosham(
        DOSHAM_RULES["Rahu"]["planet"], DOSHAM_RULES["Rahu"]["houses"],
        refs=[lagna_idx, moon_idx], data=data
    )

    # 3. Ketu Dosham
    results["Ketu Dosham"] = check_planet_dosham(
        DOSHAM_RULES["Ketu"]["planet"], DOSHAM_RULES["Ketu"]["houses"],
        refs=[lagna_idx, moon_idx], data=data
    )

    # 4. Kala Sarpa Dosham
    traditional = ["சூரியன்", "சந்திரன்", "செவ்வாய்", "புதன்", "குரு", "சுக்ரன்", "சனி"]
    rahu_idx = sign_index(get_planet_data(data, "ராகு")[0])
    ketu_idx = sign_index(get_planet_data(data, "கேது")[0])
    segment = []
    i = (rahu_idx + 1) % 12
    while i != ketu_idx:
        segment.append(i)
        i = (i + 1) % 12
    results["Kala Sarpa Dosham"] = all(
        sign_index(get_planet_data(data, pl)[0]) in segment for pl in traditional
    )

    # 5. Naga Dosham
    ketu_idx = sign_index(get_planet_data(data, "கேது")[0])
    ketu_h = house_difference(lagna_idx, ketu_idx)
    results["Naga Dosham"] = ketu_h in {1, 5, 7, 8}

    # 6. Kalathra Dosham
    mars_idx = sign_index(get_planet_data(data, "செவ்வாய்")[0])
    rahu_idx = sign_index(get_planet_data(data, "ராகு")[0])
    sat_idx = sign_index(get_planet_data(data, "சனி")[0])
    results["Kalathra Dosham"] = any(
        house_difference(lagna_idx, i) == 7 for i in [mars_idx, rahu_idx, sat_idx]
    )

    # 7. Pithru Dosham
    sun_sign, sun_deg = get_planet_data(data, "சூரியன்")
    sun_idx = sign_index(sun_sign)
    h_sun = house_difference(lagna_idx, sun_idx)
    sun_conj_rahu = are_conjunct(sun_sign, sun_deg, *get_planet_data(data, "ராகு"))
    sun_conj_ketu = are_conjunct(sun_sign, sun_deg, *get_planet_data(data, "கேது"))
    results["Pithru Dosham"] = h_sun in {6, 8, 12} or sun_conj_rahu or sun_conj_ketu

    # 8. Suriyan-Chevvai Dosham
    results["Suriyan-Chevvai Dosham"] = are_conjunct(
        *get_planet_data(data, "சூரியன்"), *get_planet_data(data, "செவ்வாய்")
    )

    # 9. Chandran-Ketu Dosham
    ketu_sign, ketu_deg = get_planet_data(data, "கேது")
    moon_conj_ketu = are_conjunct(moon_sign, moon_deg, ketu_sign, ketu_deg)
    h_mk = house_difference(moon_idx, sign_index(ketu_sign))
    h_km = house_difference(sign_index(ketu_sign), moon_idx)
    results["Chandran-Ketu Dosham"] = (
        moon_conj_ketu or h_mk in {6, 8, 12} or h_km in {6, 8, 12}
    )

    return results
    