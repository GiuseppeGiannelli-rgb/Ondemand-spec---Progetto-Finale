# chat_router.py - Route per la chat con l'agente di viaggio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from travel_agent_api.services.agent_service import Agent

# Creazione di un nuovo router FastAPI
router = APIRouter()


# Definizione del modello di dati per la richiesta di chat
class ChatCompletionRequest(BaseModel):
    # Lista dei messaggi che compongono la conversazione.
    # Ogni messaggio e' un dict con "role" (o "type", come lo invia il client Laravel) e "content".
    messages: list

    # Esempio mostrato nella schermata di test in /docs
    model_config = {
        "json_schema_extra": {
            "example": {
                "messages": [
                    {
                        "role": "user",
                        "content": "Vorrei organizzare un viaggio a Roma",
                    }
                ]
            }
        }
    }


@router.post("/travel-agent")  # Endpoint POST per il travel agent
def chat_completion(request: ChatCompletionRequest):
    """
    Endpoint per la gestione delle richieste di chat.
    Processa i messaggi ricevuti e restituisce una risposta dall'agente di viaggio.

    Args:
        request (ChatCompletionRequest): La richiesta contenente i messaggi della conversazione

    Returns:
        list: La conversazione aggiornata con la risposta dell'agente di viaggio

    Raises:
        HTTPException: In caso di errori durante l'elaborazione della richiesta
    """
    # Tracing
    print("*" * 80)
    print("chat_completion")
    print("messaggi ricevuti:", len(request.messages))
    if request.messages:
        print("ultimo messaggio:", request.messages[-1].get("content"))
    print("*" * 80)

    if not request.messages:
        raise HTTPException(status_code=400, detail="La lista dei messaggi e' vuota")

    try:
        # Creazione di una nuova istanza dell'agente
        agent = Agent()
        # Elaborazione dei messaggi e generazione della risposta
        response = agent.run(messages=request.messages)
    except Exception as e:
        print("Errore durante l'esecuzione dell'agente:", repr(e))
        raise HTTPException(status_code=500, detail=f"Errore dell'agente: {e}")

    # Tracing
    print("*" * 80)
    print("chat_completion - messaggi restituiti:", len(response))
    print("*" * 80)

    # Restituzione della risposta
    return response
