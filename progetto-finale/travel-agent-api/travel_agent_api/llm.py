# llm.py - Scelta del modello di linguaggio in base alla configurazione nel file .env
#
# La guida usa sempre ChatOpenAI("gpt-4o"). Qui il modello e' configurabile:
#   LLM_PROVIDER="ollama"  -> modello locale tramite Ollama (gratuito, gira sul PC)
#   LLM_PROVIDER="openai"  -> OpenAI come nella guida (serve OPENAI_API_KEY)
import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(max_tokens: int = 1500):
    """
    Restituisce il modello di chat configurato nel file .env.

    Args:
        max_tokens (int): numero massimo di token generati. Evita risposte fuori controllo
            (un modello locale puo' entrare in loop e riempire tutto il contesto).
    """
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
        print(f"LLM: openai / {model_name}")
        return ChatOpenAI(model_name=model_name, max_tokens=max_tokens)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model_name = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        print(f"LLM: ollama / {model_name}")
        return ChatOllama(
            model=model_name,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            # Finestra di contesto: il default di Ollama (4096 token) e' troppo piccolo
            # per system prompt + cronologia + risultati dei tool. Con 8 GB di VRAM qwen3:8b
            # resta interamente sulla GPU fino a 8192 token: oltre, una parte va sulla CPU ed e' molto piu' lento.
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")),
            num_predict=max_tokens,
            temperature=0,
            # Disattiva il "ragionamento" dei modelli che lo supportano (es. qwen3): risposte piu' rapide
            reasoning=os.getenv("OLLAMA_REASONING", "false").lower() == "true",
        )

    raise ValueError(f"LLM_PROVIDER non supportato: {provider} (usa 'ollama' oppure 'openai')")
