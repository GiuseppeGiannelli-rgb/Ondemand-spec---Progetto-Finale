# Test degli endpoint FastAPI: l'agente viene sostituito con una versione finta
from fastapi.testclient import TestClient

from travel_agent_api.main import app
from travel_agent_api.routes import chat_router

client = TestClient(app)


class FakeAgent:
    def run(self, messages):
        return messages + [{"type": "ai", "content": "Risposta di prova"}]


class BrokenAgent:
    def run(self, messages):
        raise RuntimeError("modello non raggiungibile")


def test_health_check():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_restituisce_la_conversazione_aggiornata(monkeypatch):
    monkeypatch.setattr(chat_router, "Agent", FakeAgent)

    response = client.post("/chat/travel-agent", json={"messages": [{"type": "human", "content": "Ciao"}]})

    assert response.status_code == 200
    assert response.json()[-1] == {"type": "ai", "content": "Risposta di prova"}


def test_chat_con_lista_vuota():
    response = client.post("/chat/travel-agent", json={"messages": []})

    assert response.status_code == 400


def test_chat_errore_dell_agente(monkeypatch):
    monkeypatch.setattr(chat_router, "Agent", BrokenAgent)

    response = client.post("/chat/travel-agent", json={"messages": [{"type": "human", "content": "Ciao"}]})

    assert response.status_code == 500
    assert "modello non raggiungibile" in response.json()["detail"]
