# agent_service.py - Agente ReAct che orchestra i tool di viaggio
from datetime import datetime

from dotenv import load_dotenv
from travel_agent_api.llm import get_llm
from langgraph.prebuilt import create_react_agent

# Tools
from travel_agent_api.tools.chain_historical_expert import chain_historical_expert
from travel_agent_api.tools.chain_travel_plan import chain_travel_plan
from travel_agent_api.tools.flights_finder import flights_finder
from travel_agent_api.tools.hotels_finder import hotels_finder

load_dotenv()

FLIGHTS_OUTPUT = """
format: markdown
    ## ✈️ Miglior Opzione

    ### Andata:
    - Compagnia aerea: Ryanair (FR 1234)
    - Partenza: FCO 2024-12-13 10:00
    - Arrivo: CDG 2024-12-13 11:30
    - Durata del volo: 1h 30m
    - Scali: 0
    - Prezzo andata e ritorno: €150

    ### Ritorno:
    Il volo di ritorno del 2024-12-19 si sceglie su Google Flights: [Vedi i voli su Google Flights](link)

    #### Altre opzioni disponibili:

    - Ryanair (FR 5678) - Partenza FCO 2024-12-13 18:00, Arrivo CDG 19:30 - 1h 30m - 0 scali - €180

    ...
"""

HOTELS_OUTPUT = """
format: markdown
    #### 🏨 Nome dell'hotel

    Inserisci la foto dell'hotel se disponibile.

    *Descrizione:* Camere e suite eleganti, a volte con vista sulla città, in hotel esclusivo con piscina panoramica e spa.
    *Prezzo per notte:* €296 (prima delle tasse e spese: €260)
    *Prezzo totale:* €2,660 (prima delle tasse e spese: €2,336)
    *Check-in:* 15:00, Check-out: 12:00
    *Valutazione complessiva:* 4.5 su 5
    *Servizi Inclusi:* Spa, Piscina, Parcheggio gratuito
    *Sito:* link all'hotel se disponibile

    #### 🏨 Nome dell'hotel

    Inserisci la foto dell'hotel se disponibile.

    *Descrizione:* Hotel in stile Liberty con alloggi arredati in maniera artistica, ristorante elegante, bar e spa.
    *Prezzo per notte:* €380 (prima delle tasse e spese: €333)
    *Prezzo totale:* €3,418 (prima delle tasse e spese: €3,000)
    *Check-in:* 15:00, Check-out: 12:00
    *Valutazione complessiva:* 4.5 su 5
    *Servizi Inclusi:* Spa, Piscina, Parcheggio gratuito
"""

TRAVEL_PLAN_OUTPUT = """
format: markdown
    ### Itinerario:

    ### Giorno 1 - 2024-12-13:

    *Mattina:* Descrizione dell'attivita' da svolgere la mattina

    *Pomeriggio:* Descrizione dell'attivita' da svolgere il pomeriggio

    *Sera:* Descrizione dell'attivita' da svolgere la sera

    ### Giorno 2 - 2024-12-14:

    *Mattina:* Descrizione dell'attivita' da svolgere la mattina

    *Pomeriggio:* Descrizione dell'attivita' da svolgere il pomeriggio

    *Sera:* Descrizione dell'attivita' da svolgere la sera

    ...
"""


# Lunghezza massima dei risultati dei tool dei turni precedenti
MAX_OLD_TOOL_RESULT_CHARS = 500


def compact_history(messages: list) -> list:
    """
    Accorcia i risultati dei tool dei turni precedenti all'ultima domanda dell'utente.

    Il client rimanda ad ogni richiesta l'intera conversazione, compresi i risultati
    dei tool (liste di hotel, voli, testi storici). Le informazioni utili sono gia'
    nelle risposte dell'agente: tenerli interi riempirebbe la finestra di contesto
    del modello (8192 token con Ollama) e farebbe "dimenticare" il system prompt.
    """
    last_human = max(
        (i for i, m in enumerate(messages) if m.get("type") == "human" or m.get("role") == "user"),
        default=-1,
    )
    compacted = []
    for i, message in enumerate(messages):
        is_tool = message.get("type") == "tool" or message.get("role") == "tool"
        content = str(message.get("content", ""))
        if i < last_human and is_tool and len(content) > MAX_OLD_TOOL_RESULT_CHARS:
            message = {**message, "content": content[:MAX_OLD_TOOL_RESULT_CHARS] + " ... [risultato abbreviato]"}
        compacted.append(message)
    return compacted


class Agent:
    def __init__(self):
        self.current_datetime = datetime.now()
        self.model = get_llm()
        self.tools = [
            chain_historical_expert,
            flights_finder,
            hotels_finder,
            chain_travel_plan,
        ]
        # Agente ReAct: il modello ragiona, decide quale tool chiamare, legge il risultato e risponde
        self.agent_executor = create_react_agent(self.model, self.tools)

        # Tracing
        print("*" * 80)
        print("Agent inizializzato - tool disponibili:", [t.name for t in self.tools])
        print("*" * 80)

    def run(self, messages: list):
        SYSTEM_PROMPT = f"""
            Sei un travel planner. Il tuo compito e' organizzare il viaggio per l'utente.
            Aggiungi delle emojis per rendere il tuo output piu' interessante.
            La data di oggi e' {self.current_datetime}

            Regole importanti:
            - Rispondi sempre in italiano.
            - Per voli e hotel usa SOLO i dati restituiti dai tool flights_finder e hotels_finder.
              Non inventare mai compagnie, orari, prezzi, nomi di hotel o link.
            - Se un tool restituisce un errore o nessun risultato, dillo chiaramente all'utente
              e chiedi eventuali dati mancanti: non mostrare risultati inventati.
            - Per i voli chiama flights_finder UNA SOLA VOLTA per richiesta: una ricerca copre gia'
              andata e ritorno. Non fare una seconda ricerca per il ritorno.
            - Se mancano informazioni necessarie (date, aeroporti, numero di persone), chiedile all'utente
              prima di chiamare il tool.
            - Gli esempi qui sotto mostrano SOLO il formato della risposta: i loro dati sono fittizi
              e non vanno mai riportati all'utente.

            Usa le seguenti istruzioni per creare un output:

            Esempio Output Voli:

            {FLIGHTS_OUTPUT}

            Esempio Output Hotel:

            {HOTELS_OUTPUT}

            Esempio di Output Viaggio:

            {TRAVEL_PLAN_OUTPUT}
        """

        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}] + compact_history(messages)
        response = self.agent_executor.invoke({"messages": conversation_history})

        # Tracing: quali tool ha deciso di usare l'agente in questo turno
        # (solo i messaggi nuovi, non quelli della cronologia ricevuta dal client)
        new_messages = response["messages"][len(conversation_history):]
        print("*" * 80)
        print("Agent.run - nuovi messaggi:", len(new_messages))
        for message in new_messages:
            for tool_call in getattr(message, "tool_calls", None) or []:
                print("tool chiamato:", tool_call["name"], tool_call["args"])
        print("*" * 80)

        # Il primo messaggio e' il system prompt: non lo restituiamo al client
        return response["messages"][1:]
