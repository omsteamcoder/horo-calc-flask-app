from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import traceback
from kerykeion import AstrologicalSubject
from datetime import datetime, timedelta
from ..utils.astro_calculations import (
     get_abs_pos, calculate_tithi, calculate_karana,
    calculate_yoga, get_dasha_periods, get_active_dasha, get_chart_placements,
    get_house_placements, is_sutha_jathagam, calculate_ayanamsa,
    precise_deg_to_dms, get_nakshatra_pada
)
from ..constants import RASI_NAMES, PLANET_NAMES,THITHI_NAMES
from ..utils.location_utils import get_location_details
horoscope_bp = Blueprint('horoscope', __name__)



# Horoscope API Endpoint
@horoscope_bp.route('/horoscope', methods=['POST'])
@cross_origin()
def horoscope():
    try:
        # Extract input
        data = request.json
        name = data.get("name")
        place = data.get("place")
        birth_date = data.get("date")
        birth_time = data.get("time")

        # Convert date and time
        birth_datetime = datetime.strptime(f"{birth_date} {birth_time}", "%d-%m-%Y %I:%M %p")

        # Get location details
        location_data = get_location_details(place)
        if not location_data:
            return jsonify({"error": "Invalid place"}), 400

        # Retry logic for AstrologicalSubject to avoid house cusp errors
        max_attempts = 3
        attempt = 0
        success = False
        native = None
        while attempt < max_attempts and not success:
            try:
                native = AstrologicalSubject(
                    name=name,
                    year=birth_datetime.year, month=birth_datetime.month, day=birth_datetime.day,
                    hour=birth_datetime.hour, minute=birth_datetime.minute,
                    lng=location_data['longitude'], lat=location_data['latitude'],
                    tz_str=location_data['timezone'], zodiac_type="Sidereal", sidereal_mode="LAHIRI"
                )
                success = True
            except ValueError as ve:
                if "Error in house calculation" in str(ve):
                    birth_datetime += timedelta(minutes=1)
                    print(f"Retrying horoscope generation, attempt {attempt + 1}...{birth_datetime}")
                    attempt += 1
                else:
                    raise ve

        if not success:
            raise ValueError("Failed to generate horoscope due to house calculation error.")

        # Get the absolute positions of the Sun and Moon
        sun_pos = get_abs_pos(native.sun)
        moon_pos = get_abs_pos(native.moon)

        # Calculate Tithi, Karana, and Yoga
        tithi = calculate_tithi(sun_pos, moon_pos)
        karana = calculate_karana(sun_pos, moon_pos)
        yoga = calculate_yoga(sun_pos, moon_pos)
        dasha_periods = get_dasha_periods(moon_pos)
        rasi_chart, navamsa_chart = get_chart_placements(native)
        rasi_houses, navamsa_houses = get_house_placements(native)

        # Prepare response
        response = {
            "பெயர்": name,
            "பிறந்த நாள்": birth_date,
            "பிறந்த நேரம்": birth_time,
            "பிறந்த இடம்": location_data['place_name'],
            "நெட்டாங்கு": f"{location_data['longitude']}E",
            "அகலாங்கு": f"{location_data['latitude']}N",
            "ராசி": RASI_NAMES[native.moon.sign],
            "விண்மீன்": f"{get_nakshatra_pada(get_abs_pos(native.moon))[0]}",
            "உதய லக்னம்": RASI_NAMES[native.first_house.sign],
            "நிராயன ஸ்புடங்கள்": [],
            "திதி": tithi,
            "கரணம்": karana,
            "யோகம்": yoga,
            "தசை இருப்பு": get_active_dasha(dasha_periods, birth_datetime)
        }

        # Extract planetary positions (for combustion/debilitation checks)
        planetary_positions = {
            "சூரியன்": get_abs_pos(native.sun),
            "சந்திரன்": get_abs_pos(native.moon),
            "புதன்": get_abs_pos(native.mercury),
            "சுக்ரன்": get_abs_pos(native.venus),
            "செவ்வாய்": get_abs_pos(native.mars),
            "குரு": get_abs_pos(native.jupiter),
            "சனி": get_abs_pos(native.saturn),
            "ராகு": get_abs_pos(native.true_node),
            "கேது": get_abs_pos(native.true_south_node)
        }

        # Calculate Sutha Jathagam score
        purity_score = is_sutha_jathagam(rasi_houses, navamsa_houses, planetary_positions, rasi_chart)
        response["சுத்த ஜாதகம்"] = f"{purity_score}% சுத்தம்"
        response["ராசி வீடுகள்"] = rasi_chart
        response["நவாம்ச வீடுகள்"] = navamsa_chart
        response["அயனாம்சம்"] = f"{calculate_ayanamsa(birth_datetime)}° (Lahiri approximation)"

        # Populate planetary positions for standard planets
        for planet in ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'true_node', 'true_south_node']:
            p = getattr(native, planet)
            abs_pos = get_abs_pos(p)
            nakshatra, pada = get_nakshatra_pada(abs_pos)
            response["நிராயன ஸ்புடங்கள்"].append({
                "planet": PLANET_NAMES[p.name],
                "position": precise_deg_to_dms(abs_pos),
                "rasi": RASI_NAMES[p.sign],
                "nakshatra": nakshatra,
                "pada": pada
            })

        # Add Lagna (Ascendant)
        lagna_obj = native.first_house
        lagna_abs_pos = get_abs_pos(lagna_obj)
        lagna_nak, lagna_pada = get_nakshatra_pada(lagna_abs_pos)
        response["நிராயன ஸ்புடங்கள்"].append({
            "planet": "லக்னம்",
            "position": precise_deg_to_dms(lagna_abs_pos),
            "rasi": RASI_NAMES[lagna_obj.sign],
            "nakshatra": lagna_nak,
            "pada": lagna_pada
        })

        return jsonify(response)

    except Exception as e:
        tb = traceback.format_exc()
        print("ERROR TRACEBACK:\n", tb)
        return jsonify({
            "error": str(e),
            "traceback": tb
        }), 500
