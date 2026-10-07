# flights_finder.py - Tool per la ricerca voli tramite SerpApi (Google Flights)
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from serpapi import GoogleSearch

load_dotenv()


class FlightsInput(BaseModel):
    departure_airport: str = Field(description="The departure airport code (IATA).")
    arrival_airport: str = Field(description="The arrival airport code (IATA).")
    outbound_date: str = Field(description="The outbound date (YYYY-MM-DD) e.g. 2024-12-13.")
    return_date: str = Field(description="The return date (YYYY-MM-DD) e.g. 2024-12-19.")
    adults: Optional[int] = Field(1, description="The number of adults. Defaults to 1.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")


# Numero massimo di voli restituiti all'agente
MAX_FLIGHTS = 5


def summarize_flights(data: dict) -> dict:
    """
    Riduce la risposta di SerpApi ai soli campi utili all'agente.
    La risposta completa (loghi, emissioni, token, metadati...) puo' superare
    decine di migliaia di token e non entrerebbe nel contesto di un modello locale.
    """
    flights = data.get("best_flights", []) + data.get("other_flights", [])
    # Ordiniamo per prezzo: cosi' la "miglior opzione" non dipende da un calcolo del modello
    flights = sorted(flights, key=lambda flight: flight.get("price") or float("inf"))

    options = []
    for flight in flights[:MAX_FLIGHTS]:
        legs = flight.get("flights", [])
        options.append({
            "compagnia": ", ".join(dict.fromkeys(leg.get("airline") for leg in legs)),
            "voli": ", ".join(leg.get("flight_number", "") for leg in legs),
            "partenza": f'{legs[0]["departure_airport"].get("id")} {legs[0]["departure_airport"].get("time")}',
            "arrivo": f'{legs[-1]["arrival_airport"].get("id")} {legs[-1]["arrival_airport"].get("time")}',
            "durata": format_duration(flight.get("total_duration")),
            "scali": len(flight.get("layovers", [])),
            "prezzo_andata_e_ritorno": f'€{flight.get("price")}',
        })

    if not options:
        return "Nessun volo trovato per questi aeroporti e queste date."

    return {
        "miglior_opzione_andata": options[0],
        "altre_opzioni_andata": options[1:],
        "nota": "Il prezzo e' per andata e ritorno. SerpApi restituisce solo i voli di andata: "
                "il volo di ritorno si sceglie dal link di Google Flights.",
        "link_google_flights": data.get("search_metadata", {}).get("google_flights_url"),
    }


def format_duration(minutes) -> str:
    """Converte i minuti in un formato leggibile, es. 135 -> '2h 15m'."""
    if not minutes:
        return "n.d."
    return f"{minutes // 60}h {minutes % 60:02d}m"


# Lo schema e' "piatto" (niente wrapper `params`): i modelli locali piu' piccoli
# passano gli argomenti direttamente e falliscono con uno schema annidato.
@tool(args_schema=FlightsInput)
def flights_finder(**kwargs):
    """
    This tool uses the SerpApi Google Flights API to retrieve flights info.
    A single call searches a round trip (outbound + return): call it only once per request.

    Parameters:
        departure_airport (str): The departure airport code (IATA).
        arrival_airport (str): The arrival airport code (IATA).
        outbound_date (str): The outbound date (YYYY-MM-DD) e.g. 2024-12-13.
        return_date (str): The return date (YYYY-MM-DD) e.g. 2024-12-19.
        adults (int): The number of adults. Defaults to 1.
        children (int): The number of children. Defaults to 0.

    Returns:
        dict: A dictionary containing the flights info. If the API call fails, it returns the error message as a string.
    """
    params = FlightsInput(**kwargs)

    # Tracing
    print("*" * 80)
    print("flights_finder")
    print("parametri:", params)
    print("*" * 80)

    try:
        search_params = {
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "engine": "google_flights",
            "hl": "it",
            "gl": "it",
            "currency": "EUR",
            "stops": "1",
            "departure_id": params.departure_airport,
            "arrival_id": params.arrival_airport,
            "outbound_date": params.outbound_date,
            "return_date": params.return_date,
            "adults": params.adults,
            "children": params.children,
        }

        search = GoogleSearch(search_params)
        data = search.get_dict()
        if "error" in data:
            return data["error"]
        return summarize_flights(data)
    except Exception as e:
        print("Errore flights_finder:", e)
        return str(e)
