
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from timezonefinder import TimezoneFinder


geolocator = Nominatim(
    user_agent="melooha_astrology_app"
)

timezone_finder = TimezoneFinder()


def get_coordinates(place: str) -> dict:
    try:
        location = geolocator.geocode(
            place,
            exactly_one=True,
            timeout=10,
        )

        if location is None:
            raise ValueError(
                "Could not find this birth location. "
                "Please enter a valid city, state and country."
            )

        latitude = location.latitude
        longitude = location.longitude

        timezone_name = timezone_finder.timezone_at(
            lat=latitude,
            lng=longitude,
        )

        if not timezone_name:
            raise ValueError(
                "Could not detect the timezone for this birthplace."
            )

        return {
            "latitude": latitude,
            "longitude": longitude,
            "resolved_address": location.address,
            "timezone_name": timezone_name,
        }

    except (GeocoderTimedOut, GeocoderServiceError) as error:
        raise ValueError(
            "Location service is temporarily unavailable. "
            "Please try again."
        ) from error
