from app.utils.astro_utils import (
    sign_index, get_planet_data, house_difference, are_conjunct,check_planet_dosham,    
    get_abs_pos, get_nakshatra_pada, get_chart_placements, get_house_placements,format_dasha_periods
)
from datetime import datetime, timedelta
from ..constants import (
    RASI_NAMES, PLANET_NAMES, YOGA_NAMES, THITHI_NAMES, DOSHAM_RULES
)


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
def get_active_dasha(dasha_periods, birth_datetime):
    """
    Determine the active Dasha period at the time of birth.
    """
    start_date = birth_datetime
    for dasha in dasha_periods:
        planet, years_fraction = dasha.split(": ")
        years_fraction = float(years_fraction.split()[0])

        # Convert to timedelta (years -> days)
        dasha_duration = timedelta(days=years_fraction * 365.25)

        if start_date <= birth_datetime < start_date + dasha_duration:
            # Found the active dasha at birth
            active_dasha = format_dasha_periods([dasha])[0]
            return active_dasha

        # Move to next Dasha period
        start_date += dasha_duration
    
    return None 


def is_sutha_jathagam(rasi_houses, navamsa_houses, planetary_positions, rasi_chart):
    # Start with 100% purity and introduce a weighted scoring system
    total_weight = 0
    weighted_score = 0

    # Helper function to calculate weighted contributions
    def add_weighted_score(score, weight):
        nonlocal total_weight, weighted_score
        total_weight += weight
        weighted_score += score * weight

    # 1. Malefic House Placements (Weight: 30%)
    # ----------------------------------------
    malefic_score = 100  # Start with full points for this category
    
    # Mars in bad houses (1,2,4,7,8,12) - Strong malefic effect
    sevvai_dosha_houses = [1, 2, 4, 7, 8, 12]
    for house in sevvai_dosha_houses:
        if "செவ்வாய்" in rasi_houses.get(house, []):
            malefic_score -= 15
    
    # Rahu/Ketu in 7th/8th (afflicts marriage/longevity)
    for house in [7, 8]:
        if any(dosha in rasi_houses.get(house, []) for dosha in ["ராகு", "கேது"]):
            malefic_score -= 10
    
    # Saturn in Kendras (1,4,7,10) - Delays and challenges
    for house in [1, 4, 7, 10]:
        if "சனி" in rasi_houses.get(house, []):
            malefic_score -= 12
    
    # Sun in bad houses (6,8,12) - Weak vitality
    for house in [6, 8, 12]:
        if "சூரியன்" in rasi_houses.get(house, []):
            malefic_score -= 8

    add_weighted_score(max(0, malefic_score), 30)

    # 2. Planetary Debilitations & Exaltations (Weight: 25%)
    # -----------------------------------------------------
    planetary_score = 100
    
    # Jupiter in Mithunam (Gemini) - Debilitated
    if "குரு" in rasi_chart.get("மிதுனம்", []):
        planetary_score -= 10
    
    # Venus in Makaram (Capricorn) - Debilitated but check for Neecha Bhanga Raj Yoga
    if "சுக்ரன்" in rasi_chart.get("மகரம்", []):
        if all(planet in rasi_houses.get(10, []) for planet in ["சூரியன்", "சந்திரன்"]):
            planetary_score += 5  # Mitigated by Raja Yoga
        else:
            planetary_score -= 10
    
    # Mercury combust (if within 14° of Sun)
    sun_pos = planetary_positions["சூரியன்"]
    mercury_pos = planetary_positions["புதன்"]
    if abs(sun_pos - mercury_pos) < 14 or abs(sun_pos - mercury_pos) > 346:
        planetary_score -= 8
    
    # Moon in 6/8/12 - Emotional instability
    for house in [6, 8, 12]:
        if "சந்திரன்" in rasi_houses.get(house, []):
            planetary_score -= 7

    add_weighted_score(max(0, planetary_score), 25)

    # 3. Navamsa Chart Analysis (Weight: 20%)
    # ---------------------------------------
    navamsa_score = 100
    
    # If Jupiter is debilitated in Navamsa (Makara/Capricorn)
    if "குரு" in navamsa_houses.get(10, []):  # 10th house = Capricorn
        navamsa_score -= 5
    
    # If Lagna is in a weak Navamsa (Scorpio, Aquarius)
    if "லக்னம்" in navamsa_houses.get(8, []) or "லக்னம்" in navamsa_houses.get(11, []):
        navamsa_score -= 5

    add_weighted_score(max(0, navamsa_score), 20)

    # 4. Yogas and Special Combinations (Weight: 15%)
    # ----------------------------------------------
    yoga_score = 100
    
    # Check for Kala Sarpa Yoga (Rahu-Ketu axis across chart)
    if "ராகு" in rasi_chart.get("மேஷம்", []) and "கேது" in rasi_chart.get("துலாம்", []):
        # Mixed impact, but mitigate if strong yogas are present
        if all(planet in rasi_houses.get(10, []) for planet in ["சூரியன்", "சந்திரன்"]):
            yoga_score -= 5  # Partial mitigation
        else:
            yoga_score -= 10
    
    # Check for Raja Yoga (Sun + Moon in 10th house)
    if all(planet in rasi_houses.get(10, []) for planet in ["சூரியன்", "சந்திரன்"]):
        yoga_score += 15  # Strong career potential

    add_weighted_score(max(0, yoga_score), 15)

    # 5. Dasha Timing (Weight: 10%)
    # -----------------------------
    dasha_score = 100
    
    # Current dasha planet
    current_dasha_planet = "சுக்ரன்"  # Example: Current dasha planet
    if current_dasha_planet in rasi_chart.get("தனுசு", []):  # Venus in Sagittarius
        dasha_score -= 10  # Neutral but not afflicted

    add_weighted_score(max(0, dasha_score), 10)

    # Final Calculation
    final_purity_score = (weighted_score / total_weight) if total_weight > 0 else 0
    return round(final_purity_score, 2)


def calculate_ayanamsa(birth_datetime):
    """
    Calculate the Lahiri Ayanamsa using a simplified linear formula.
    
    This is a rough approximation: 
    - For reference, we use 2000-01-01 as the reference date.
    - At the reference date, assume Lahiri Ayanamsa is about 24.05° (i.e. 24°03')
    - The rate of change is set approximately 0.013968° per tropical year.
    
    Note: For a production-level application, use a specialized library or more precise algorithm.
    """
    reference_datetime = datetime(2000, 1, 1)
    reference_ayanamsa = 24.05  # in degrees
    # Calculate the difference in years
    years_diff = (birth_datetime - reference_datetime).days / 365.25
    ayanamsa = reference_ayanamsa + (years_diff * 0.013968)
    return round(ayanamsa, 4)
def precise_deg_to_dms(degree: float) -> str:
    """Ultra-precise degree conversion"""
    degree = round(degree, 6)
    deg = int(degree)
    minutes_full = (degree - deg) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60)
    
    # Handle 60 seconds rollover
    if seconds >= 60:
        seconds -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        deg += 1
    
    return f"{deg}:{minutes:02d}:{seconds:02d}"



def get_dasha_periods(moon_position):
    """
    Calculate the Dasha periods for the native based on the moon's nakshatra.
    """
    # The Dasha lengths in years for each planet
    DASHA_PERIODS = {
        "Sun": 6,
        "Moon": 10,
        "Mars": 7,
        "Rahu": 18,
        "Jupiter": 16,
        "Saturn": 19,
        "Mercury": 17,
        "Ketu": 7,
        "Venus": 20
    }

    # Nakshatra to Planet mapping based on the Moon's position
    nakshatra_planet_mapping = [
        ("அஸ்வினி", "Ketu"),
        ("பரணி", "Venus"),
        ("கிருத்திகை", "Sun"),
        ("ரோகிணி", "Moon"),
        ("மிருகசீரிஷம்", "Mars"),
        ("திருவாதிரை", "Rahu"),
        ("புனர்பூசம்", "Jupiter"),
        ("பூசம்", "Saturn"),
        ("ஆயில்யம்", "Mercury"),
        ("மகம்", "Ketu"),
        ("பூரம்", "Venus"),
        ("உத்திரம்", "Sun"),
        ("அஸ்தம்", "Moon"),
        ("சித்திரை", "Mars"),
        ("ஸ்வாதி", "Rahu"),
        ("விசாகம்", "Jupiter"),
        ("அனுஷம்", "Saturn"),
        ("கேட்டை", "Mercury"),
        ("மூலம்", "Ketu"),
        ("பூராடம்", "Venus"),
        ("உத்திராடம்", "Sun"),
        ("திருவோணம்", "Moon"),
        ("அவிட்டம்", "Mars"),
        ("சதயம்", "Rahu"),
        ("பூரட்டாதி", "Jupiter"),
        ("உத்திரட்டாதி", "Saturn"),
        ("ரேவதி", "Mercury")
    ]

    # Get Nakshatra and Planet based on the moon position
    nakshatra_index = int((moon_position % 360) // 13.3333)
    nakshatra, dasha_planet = nakshatra_planet_mapping[nakshatra_index]

    # Get the Dasha period of the planet based on the Nakshatra
    dasha_period = DASHA_PERIODS[dasha_planet]

    # Determine the position within the Nakshatra
    nakshatra_position = moon_position % 13.3333
    dasha_percentage = nakshatra_position / 13.3333

    # Calculate the starting Dasha period in years
    starting_dasha_years = dasha_period * dasha_percentage

    # Calculate the remaining Dasha period for the planet
    remaining_dasha_years = dasha_period - starting_dasha_years

    # Generate Dasha sequence
    dasha_sequence = [f"{dasha_planet}: {remaining_dasha_years:.2f} years"]

    # Add subsequent Dashas
    planets = list(DASHA_PERIODS.keys())
    planet_index = planets.index(dasha_planet)

    for i in range(1, 9):  # For the next 8 planets
        next_planet = planets[(planet_index + i) % len(planets)]
        dasha_sequence.append(f"{next_planet}: {DASHA_PERIODS[next_planet]} years")

    return dasha_sequence


def calculate_yoga(sun_position, moon_position):
    yoga_angle = (sun_position + moon_position) % 360  # Sum of Sun and Moon positions
    yoga_index = int(yoga_angle // 13.3333)  # Each yoga spans 13°20'
    return YOGA_NAMES[yoga_index]
    
def calculate_karana(sun_position, moon_position):
    karana_cycle = ["பவம்", "பாலவம்", "கெளலவம்", "தைதுலம்", "கரசை", "வணிசை", "பத்தரை (விஷ்டி)"]
    special_karanas = {
        0: "பவம்",     # first half of first tithi
        29.5:  "சதுஷ்பாதம்",
        30.0: "நாகவம்",
        30.5: "கிம்ஸ்துக்னம்"
    }

    # Calculate Tithi and half
    tithi_angle = (moon_position - sun_position) % 360
    tithi = tithi_angle / 12  # each tithi is 12 degrees
    tithi_index = int(tithi)
    is_second_half = tithi % 1 >= 0.5

    tithi_half = tithi_index + 0.5 if is_second_half else tithi_index

    # Special fixed karanas
    if tithi_half in special_karanas:
        return special_karanas[tithi_half]

    # Remaining 56 karanas rotate over 1st to 28th Tithis (2 per Tithi)
    karana_number = int(tithi_half)
    return karana_cycle[(karana_number - 1) % len(karana_cycle)]


def calculate_tithi(sun_position, moon_position):
    """
    Calculate Tithi and determine whether it is Sukla Paksha (Waxing) or Krishna Paksha (Waning)
    """
    tithi_angle = (moon_position - sun_position) % 360  # Difference between Moon and Sun
    tithi_index = int(tithi_angle // 12)  # 360° divided into 30 Tithis

    if tithi_angle < 180:
        paksha = "சுக்லபஷம் (வளர்பிறை)"  # Waxing phase
    else:
        paksha = "கிருஷ்ணபஷம் (தேய்பிறை)"  # Waning phase

    tithi_name = THITHI_NAMES[tithi_index]
    return f"{tithi_name}, {paksha}"


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


