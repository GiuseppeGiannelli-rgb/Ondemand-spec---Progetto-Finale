# chain_historical_expert.py - Tool che risponde a domande storiche/culturali con un LLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from travel_agent_api.llm import get_llm


@tool
def chain_historical_expert(input_text: str) -> str:
    """
    Questo tool utilizza un modello di intelligenza artificiale per fornire contenuti
    approfonditi su un argomento storico specifico.

    Args:
        input_text (str): Il testo dell'argomento per il quale si vuole ottenere il contenuto.

    Returns:
        str: Il contenuto generato dal modello.
    """
    # Tracing
    print("*" * 80)
    print("chain_historical_expert")
    print("argomento:", input_text)
    print("*" * 80)

    model = get_llm(max_tokens=800)

    system_prompt = """
        You are an historical expert.
        Your mission is to provide in-depth content on the topic,
        answer questions, and act as an assistant.
        Answer in Italian, in at most 250 words.
        Use emojis to make your answers more engaging and friendly.
        Always strive to be approachable and helpful, offering the
        most accurate and useful information possible to users.
    """

    prompt = ChatPromptTemplate([
        ("system", "{system_prompt}"),
        ("user", "{input}"),
    ])

    chain = prompt | model
    result = chain.invoke({
        "input": input_text,
        "system_prompt": system_prompt,
    })

    # Il modello restituisce un AIMessage: all'agente serve solo il testo
    return result.content
