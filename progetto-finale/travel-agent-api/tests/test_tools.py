# Test della logica dei tool: non chiamano SerpApi ne' il modello di linguaggio
from travel_agent_api.tools.chain_travel_plan import chain_travel_plan
from travel_agent_api.tools.flights_finder import flights_finder, format_duration, summarize_flights
from travel_agent_api.tools.hotels_finder import hotels_finder, summarize_hotel


def make_flight(price, airline, number, departure, arrival, duration):
    return {
        "price": price,
        "total_duration": duration,
        "flights": [{
            "airline": airline,
            "flight_number": number,
            "departure_airport": {"id": "FCO", "time": departure},
            "arrival_airport": {"id": "CDG", "time": arrival},
            "duration": duration,
        }],
    }


def test_format_duration():
    assert format_duration(135) == "2h 15m"
    assert format_duration(60) == "1h 00m"
    assert format_duration(None) == "n.d."


def test_summarize_flights_ordina_per_prezzo():
    data = {
        "best_flights": [make_flight(404, "Air France", "AF 1505", "2026-11-12 16:00", "2026-11-12 18:10", 130)],
        "other_flights": [make_flight(341, "ITA", "AZ 332", "2026-11-12 21:25", "2026-11-12 23:40", 135)],
        "search_metadata": {"google_flights_url": "https://www.google.com/travel/flights?x"},
    }

    result = summarize_flights(data)

    assert result["miglior_opzione_andata"]["compagnia"] == "ITA"
    assert result["miglior_opzione_andata"]["prezzo_andata_e_ritorno"] == "€341"
    assert result["miglior_opzione_andata"]["durata"] == "2h 15m"
    assert result["altre_opzioni_andata"][0]["voli"] == "AF 1505"
    assert result["link_google_flights"] == "https://www.google.com/travel/flights?x"


def test_summarize_flights_senza_risultati():
    assert summarize_flights({}) == "Nessun volo trovato per questi aeroporti e queste date."


def test_summarize_hotel_tiene_solo_i_campi_utili():
    hotel = {
        "name": "Hotel Test",
        "rate_per_night": {"lowest": "89 €", "extracted_lowest": 89},
        "total_rate": {"lowest": "446 €"},
        "overall_rating": 4.1,
        "amenities": [f"servizio {i}" for i in range(20)],
        "images": [{"thumbnail": "https://foto"}],
        "gps_coordinates": {"latitude": 41.9},  # campo scartato
    }

    result = summarize_hotel(hotel)

    assert result["nome"] == "Hotel Test"
    assert result["prezzo_per_notte"] == "89 €"
    assert result["foto"] == "https://foto"
    assert len(result["servizi"]) == 8
    assert "gps_coordinates" not in result


def test_summarize_hotel_senza_foto():
    assert summarize_hotel({"name": "Senza foto"})["foto"] is None


def test_schemi_dei_tool_sono_piatti():
    # I modelli locali passano gli argomenti direttamente: niente wrapper "params"
    for tool in (flights_finder, hotels_finder, chain_travel_plan):
        properties = tool.tool_call_schema.model_json_schema()["properties"]
        assert "params" not in properties

    assert "departure_airport" in flights_finder.tool_call_schema.model_json_schema()["properties"]
    assert "check_in_date" in hotels_finder.tool_call_schema.model_json_schema()["properties"]
