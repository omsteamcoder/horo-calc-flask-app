from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_location_details(place_name):
    geolocator = Nominatim(user_agent="astro_script")
    tf = TimezoneFinder()
    
    location = geolocator.geocode(place_name,language='en')
    if not location:
        return None

    return {
        'latitude': location.latitude,
        'longitude': location.longitude,
        'timezone': tf.timezone_at(lng=location.longitude, lat=location.latitude),
        'place_name': location.address.split(',')[0]
    }
