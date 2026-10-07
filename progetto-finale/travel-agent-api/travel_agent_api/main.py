# main.py - Punto di ingresso dell'applicazione FastAPI
import sys

# Su Windows la console usa cp1252: i print di tracing con emoji o caratteri speciali
# andrebbero in errore e farebbero fallire la richiesta. Forziamo UTF-8.
# line_buffering: ogni print compare subito nel log, anche quando l'output non e' un terminale.
sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

# Classe principale del framework: l'oggetto `app` registra route e middleware.
from fastapi import FastAPI

# Middleware CORS: decide quali domini (origin) possono chiamare questa API dal browser.
from fastapi.middleware.cors import CORSMiddleware

# Router con gli endpoint della chat, organizzato in un modulo separato.
from travel_agent_api.routes import chat_router

app = FastAPI(
    title="Travel Agent API",
    description="Assistente di viaggio intelligente basato su LangChain e LangGraph",
    version="0.1.0",
)

# Origin del client Laravel (php artisan serve gira sulla porta 8000)
origins = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,     # Domini permessi
    allow_credentials=True,    # Permette l'invio di credenziali
    allow_methods=["*"],       # Permette tutti i metodi HTTP
    allow_headers=["*"],       # Permette tutti gli headers
)

app.include_router(
    chat_router.router,  # Il router definito in chat_router.py
    tags=["Chat"],       # Tag per la documentazione Swagger
    prefix="/chat",      # Prefisso per tutte le route del router
)


@app.get("/", tags=["Health"])
def health_check():
    """Endpoint di controllo: verifica che il server sia attivo."""
    # Tracing
    print("*" * 80)
    print("health_check")
    print("*" * 80)
    return {"status": "ok", "docs": "/docs"}
