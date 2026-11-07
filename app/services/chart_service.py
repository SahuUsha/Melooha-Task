
from datetime import datetime, timezone

import swisseph as swe


# Vedic astrology configuration
swe.set_sid_mode(swe.SIDM_LAHIRI)

ZODIAC_SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
}


def get_sign(longitude: float) -> str:
    """Return the zodiac sign for a sidereal longitude."""
    sign_index = int(longitude // 30)
    return ZODIAC_SIGNS[sign_index % 12]


def get_house(planet_longitude: float, ascendant_longitude: float) -> int:
    """Calculate Whole Sign house placement."""
    planet_sign = int(planet_longitude // 30)
    ascendant_sign = int(ascendant_longitude // 30)

    return ((planet_sign - ascendant_sign) % 12) + 1


def get_planet_position(
    julian_day: float,
    planet_id: int,
) -> dict:
    """Calculate a planet's sidereal position."""

    flags = (
        swe.FLG_SWIEPH
        | swe.FLG_SIDEREAL
        | swe.FLG_SPEED
    )

    result = swe.calc_ut(
        julian_day,
        planet_id,
        flags,
    )

    # Swiss Ephemeris returns (coordinates, returned_flags)
    coordinates = result[0]

    longitude = coordinates[0] % 360
    speed = coordinates[3]

    return {
        "longitude": round(longitude, 4),
        "sign": get_sign(longitude),
        "degree_in_sign": round(longitude % 30, 4),
        "retrograde": speed < 0,
    }



def calculate_birth_chart(
    birth_datetime_utc: datetime,
    latitude: float,
    longitude: float,
) -> dict:
    """
    Calculate a Vedic birth chart using:
    - Sidereal zodiac
    - Lahiri Ayanamsha
    - Whole Sign houses

    birth_datetime_utc must be timezone-aware and in UTC.
    """

    if birth_datetime_utc.tzinfo is None:
        raise ValueError("Birth datetime must include timezone information")

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    birth_datetime_utc = birth_datetime_utc.astimezone(timezone.utc)

    decimal_hour = (
        birth_datetime_utc.hour
        + birth_datetime_utc.minute / 60
        + birth_datetime_utc.second / 3600
        + birth_datetime_utc.microsecond / 3_600_000_000
    )

    julian_day = swe.julday(
        birth_datetime_utc.year,
        birth_datetime_utc.month,
        birth_datetime_utc.day,
        decimal_hour,
        swe.GREG_CAL,
    )

    # Calculate sidereal Ascendant
    houses, ascmc = swe.houses_ex(
        julian_day,
        latitude,
        longitude,
        b"W",
        swe.FLG_SIDEREAL,
    )

    ascendant_longitude = ascmc[0] % 360

    chart = {
        "calculation_system": "Vedic Sidereal",
        "ayanamsha": "Lahiri",
        "house_system": "Whole Sign",
        "birth_datetime_utc": birth_datetime_utc.isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "ascendant": {
            "longitude": round(ascendant_longitude, 4),
            "sign": get_sign(ascendant_longitude),
            "degree_in_sign": round(ascendant_longitude % 30, 4),
        },
        "planets": {},
    }

    # Calculate seven classical planets
    for planet_name, planet_id in PLANETS.items():
        position = get_planet_position(julian_day, planet_id)

        position["house"] = get_house(
            position["longitude"],
            ascendant_longitude,
        )

        chart["planets"][planet_name] = position

    # Calculate Rahu (True Node)
    rahu = get_planet_position(julian_day, swe.TRUE_NODE)

    rahu["house"] = get_house(
        rahu["longitude"],
        ascendant_longitude,
    )

    chart["planets"]["Rahu"] = rahu

    # Ketu is exactly opposite Rahu
    ketu_longitude = (rahu["longitude"] + 180) % 360

    chart["planets"]["Ketu"] = {
        "longitude": round(ketu_longitude, 4),
        "sign": get_sign(ketu_longitude),
        "degree_in_sign": round(ketu_longitude % 30, 4),
        "house": get_house(ketu_longitude, ascendant_longitude),
        "retrograde": rahu["retrograde"],
    }

    return chart
