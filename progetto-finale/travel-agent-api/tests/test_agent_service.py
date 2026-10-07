# Test della gestione della cronologia della conversazione
from travel_agent_api.services.agent_service import MAX_OLD_TOOL_RESULT_CHARS, compact_history


def test_accorcia_i_risultati_dei_tool_dei_turni_precedenti():
    long_result = "x" * 5000
    messages = [
        {"type": "human", "content": "Cerco un hotel a Roma"},
        {"type": "ai", "content": "", "tool_calls": [{"name": "hotels_finder", "args": {}, "id": "1"}]},
        {"type": "tool", "content": long_result, "tool_call_id": "1"},
        {"type": "ai", "content": "Ecco gli hotel"},
        {"type": "human", "content": "Raccontami del quartiere"},
    ]

    result = compact_history(messages)

    assert len(result[2]["content"]) < len(long_result)
    assert result[2]["content"].startswith("x" * MAX_OLD_TOOL_RESULT_CHARS)
    assert result[2]["content"].endswith("[risultato abbreviato]")
    # La struttura resta valida: il collegamento tra chiamata e risultato del tool non cambia
    assert result[2]["tool_call_id"] == "1"
    # Il messaggio originale ricevuto dal client non viene modificato
    assert messages[2]["content"] == long_result


def test_non_tocca_i_messaggi_corti_ne_quelli_dopo_l_ultima_domanda():
    messages = [
        {"role": "user", "content": "Ciao"},
        {"role": "tool", "content": "breve", "tool_call_id": "1"},
        {"role": "user", "content": "Altra domanda"},
        {"role": "tool", "content": "y" * 5000, "tool_call_id": "2"},
    ]

    result = compact_history(messages)

    assert result[1]["content"] == "breve"
    assert result[3]["content"] == "y" * 5000


def test_conversazione_vuota():
    assert compact_history([]) == []
