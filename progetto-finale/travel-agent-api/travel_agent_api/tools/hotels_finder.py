# hotels_finder.py - Tool per la ricerca hotel tramite SerpApi (Google Hotels)
import os
from enum import IntEnum
from typing import Optional

from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from serpapi import GoogleSearch

load_dotenv()


class HotelClassEnum(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


class HotelsInput(BaseModel):
    q: str = Field(description="Location of the hotel.")
    check_in_date: str = Field(description="The check-in date (YYYY-MM-DD) e.g. 2024-12-13.")
    check_out_date: str = Field(description="The check-out date (YYYY-MM-DD) e.g. 2024-12-19.")
    adults: Optional[int] = Field(1, description="The number of adults. Defaults to 1.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")
    hotel_class: Optional[HotelClassEnum] = Field(2, description="The hotel class available from 2 to 5. Defaults to 2.")


# Numero massimo di hotel restituiti all'agente
MAX_HOTELS = 5


def summarize_hotel(hotel: dict) -> dict:
    """Tiene solo i campi utili all'agente: la risposta completa di SerpApi e' molto lunga."""
    images = hotel.get("images") or [{}]
    return {
        "nome": hotel.get("name"),
        "descrizione": hotel.get("description"),
        "classe": hotel.get("hotel_class"),
        "prezzo_per_notte": hotel.get("rate_per_night", {}).get("lowest"),
        "prezzo_totale": hotel.get("total_rate", {}).get("lowest"),
        "check_in": hotel.get("check_in_time"),
        "check_out": hotel.get("check_out_time"),
        "valutazione": hotel.get("overall_rating"),
        "recensioni": hotel.get("reviews"),
        "servizi": hotel.get("amenities", [])[:8],
        "foto": images[0].get("thumbnail"),
        "link": hotel.get("link"),
    }


# Lo schema e' "piatto" (niente wrapper `params`): i modelli locali piu' piccoli
# passano gli argomenti direttamente e falliscono con uno schema annidato.
@tool(args_schema=HotelsInput)
def hotels_finder(**kwargs):
    """
    This tool uses the SerpApi Google Hotels API to retrieve hotels info.

    Parameters:
        q (str): Location of the hotel.
        check_in_date (str): The check-in date (YYYY-MM-DD) e.g. 2024-12-13.
        check_out_date (str): The check-out date (YYYY-MM-DD) e.g. 2024-12-19.
        adults (int): The number of adults. Defaults to 1.
        children (int): The number of children. Defaults to 0.
        hotel_class (int): The hotel class available from 2 to 5. Defaults to 2.

    Returns:
        list: A list containing the hotels info. If the API call fails, it returns the error message as a string.
    """
    params = HotelsInput(**kwargs)

    # Tracing
    print("*" * 80)
    print("hotels_finder")
    print("parametri:", params)
    print("*" * 80)

    search_params = {
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "engine": "google_hotels",
        "hl": "it",
        "gl": "it",
        "currency": "EUR",
        "q": params.q,
        "check_in_date": params.check_in_date,
        "check_out_date": params.check_out_date,
        "adults": params.adults,
        "children": params.children,
        "hotel_class": int(params.hotel_class),
        "num": 5,
    }

    try:
        search = GoogleSearch(search_params)
        data = search.get_dict()
        # Se SerpApi restituisce un errore non c'e' la chiave "properties": lo riportiamo all'agente
        if "properties" in data:
            results = [summarize_hotel(hotel) for hotel in data["properties"][:MAX_HOTELS]]
        else:
            results = data.get("error", "Nessun hotel trovato.")
    except Exception as e:
        print("Errore hotels_finder:", e)
        results = str(e)

    return results
