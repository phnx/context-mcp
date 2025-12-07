"""
dummy mcp tools for external operations
"""

import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


async def lookup_flights(origin: str, destination: str, date: str) -> dict:
    """
    Search for flights from origin to destination on a given date.
    """

    airlines = ["Air Asia", "Thai Airways", "Singapore Airlines", "Jetstar", "Scoot"]
    results_count = random.randint(2, 5)
    flights = []

    base_dep = datetime.fromisoformat(date + "T09:00:00")

    for i in range(results_count):
        dep = base_dep + timedelta(hours=i * 2)
        arr = dep + timedelta(hours=2)

        flights.append(
            {
                "flight_id": f"FLIGHT-{random.randint(1000,9999)}",
                "airline": random.choice(airlines),
                "from": origin,
                "to": destination,
                "departure_time": dep.isoformat(),
                "arrival_time": arr.isoformat(),
                "price": round(random.uniform(120, 500), 2),
            }
        )

    logger.debug("tool calling: lookup_flights")

    return {"flights": flights}


async def lookup_hotels(city: str, check_in: str, check_out: str) -> dict:
    """
    Search for hotel rooms from in a city between given dates.
    """

    hotels_list = [
        "Grand Palace Hotel",
        "Riverside Resort",
        "City Center Inn",
        "Blue Lagoon Suites",
        "Sunrise Hotel",
        "Green Leaf Apartments",
    ]

    results_count = random.randint(2, 5)
    hotels = []

    for _ in range(results_count):
        hotels.append(
            {
                "hotel_id": f"HOTEL-{random.randint(1000,9999)}",
                "name": random.choice(hotels_list),
                "city": city,
                "check_in": check_in,
                "check_out": check_out,
                "price_per_night": round(random.uniform(30, 200), 2),
            }
        )

    logger.debug("tool calling: lookup_hotels")

    return {"hotels": hotels}


async def book_a_flight(
    user_id: str,
    flight_id: str,
    airline: str,
    from_location: str,
    to_location: str,
    departure_time: str,
    arrival_time: str,
    price: float,
) -> dict:
    """
    Book a flight chosen from lookup_flights results.
    """

    logger.debug("tool calling: book_a_flight")

    return {
        "status": "success",
        "type": "flight_booking",
        "user_id": user_id,
        "flight": {
            "flight_id": flight_id,
            "airline": airline,
            "from": from_location,
            "to": to_location,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "price": price,
        },
        "message": "Flight booking completed.",
    }


async def book_a_hotel(
    user_id: str,
    hotel_id: str,
    name: str,
    city: str,
    check_in: str,
    check_out: str,
    price_per_night: float,
) -> dict:
    """
    Book a hotel chosen from lookup_hotels results.
    """

    logger.debug("tool calling: book_a_hotel")

    return {
        "status": "success",
        "type": "hotel_booking",
        "user_id": user_id,
        "hotel": {
            "hotel_id": hotel_id,
            "name": name,
            "city": city,
            "check_in": check_in,
            "check_out": check_out,
            "price_per_night": price_per_night,
        },
        "message": "Hotel booking completed.",
    }
