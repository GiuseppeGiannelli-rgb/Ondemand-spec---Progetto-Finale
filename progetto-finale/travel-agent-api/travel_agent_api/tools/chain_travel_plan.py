# chain_travel_plan.py - Tool che genera un itinerario giorno per giorno con un LLM
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from travel_agent_api.llm import get_llm


class TravelPlanInput(BaseModel):
    start_date: str = Field(description="The start date of the trip (YYYY-MM-DD) e.g. 2024-12-13.")
    end_date: str = Field(description="The end date of the trip (YYYY-MM-DD) e.g. 2024-12-19.")
    destination: str = Field(description="The destination of the trip.")
    adults: Optional[int] = Field(1, description="The number of adults. Defaults to 1.")
    children: Optional[int] = Field(0, description="The number of children. Defaults to 0.")
    travel_style: Optional[str] = Field("culture", description="The style of travel. e.g. adventure, relax, culture, backpacking, luxury, family-friendly.")
    budget: Optional[int] = Field(None, description="The total budget for the trip.")
    activities: Optional[str] = Field("sightseeing", description="The preferred activities. e.g. culture, nature, food, shopping.")
    food_restriction: Optional[str] = Field("none", description="Any food restrictions. e.g. vegetarian, gluten-free. Defaults to none.")


class TravelDayOutput(BaseModel):
    morning: str = Field(description="The activities for the morning.")
    afternoon: str = Field(description="The activities for the afternoon.")
    evening: str = Field(description="The activities for the evening.")


class TravelPlanOutput(BaseModel):
    travel_plan: list[TravelDayOutput]


# Lo schema e' "piatto" (niente wrapper `params`): i modelli locali piu' piccoli
# passano gli argomenti direttamente e falliscono con uno schema annidato.
@tool(args_schema=TravelPlanInput)
def chain_travel_plan(**kwargs) -> TravelPlanOutput:
    """
    Generates a comprehensive travel plan based on user input parameters.

    Parameters:
        params (TravelPlanInput): The input parameters for the travel plan
        including dates, destination, number of travelers, travel style, budget,
        preferred activities, and any food restrictions.

    Returns:
        TravelPlanOutput: The generated travel plan content.
    """
    params = TravelPlanInput(**kwargs)

    # Tracing
    print("*" * 80)
    print("chain_travel_plan")
    print("parametri:", params)
    print("*" * 80)

    model = get_llm(max_tokens=3000)

    system_prompt = f"""
        You are a travel expert.
        Your mission is to provide in-depth content on the topic to create a travel plan.
        The start date of the trip is {params.start_date}.
        The end date of the trip is {params.end_date}.
        The destination of the trip is {params.destination}.
        The number of adults is {params.adults}.
        The number of children is {params.children}.
        The style of travel is {params.travel_style}.
        The total budget for the trip is {params.budget}.
        The preferred activities are {params.activities}.
        Any food restrictions are {params.food_restriction}
        Create one entry for each day of the trip, from the start date to the end date.
        Write the travel plan in Italian.
        Use emojis to make your answers more engaging and friendly.
        Always strive to be approachable and helpful, offering the
        most accurate and useful information possible to users.
    """

    # with_structured_output vincola la risposta allo schema TravelPlanOutput.
    # Con PydanticOutputParser (come nella guida) il modello locale a volte sbagliava
    # una chiave del JSON (es. "after,noon") e il parsing falliva.
    structured_model = model.with_structured_output(TravelPlanOutput)

    prompt = ChatPromptTemplate([
        ("system", "{system_prompt}"),
        ("human", "Create the travel plan."),
    ])

    chain = prompt | structured_model
    result = chain.invoke({"system_prompt": system_prompt})

    # Tracing
    print("*" * 80)
    print("chain_travel_plan - giorni generati:", len(result.travel_plan))
    print("*" * 80)

    return result
