
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut


geolocator = Nominatim(
    user_agent="melooha_astrology_app"
)


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

        return {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "resolved_address": location.address,
        }

    except (GeocoderTimedOut, GeocoderServiceError) as error:
        raise ValueError(
            "Location service is temporarily unavailable. "
            "Please try again."
        ) from error
