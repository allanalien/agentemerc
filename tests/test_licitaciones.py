
import pytest
import textwrap
import os
from google.adk.runners import InMemoryRunner
from google.genai.types import UserContent, Part
import dotenv

# Load env vars before importing agent to avoid any potential init issues
dotenv.load_dotenv()

from financial_advisor.agent import root_agent

@pytest.mark.asyncio
async def test_licitaciones_flow():
    """Runs the tender agent on a sample input and checks for Spanish response."""
    
    # Input simulating a construction company in Mexico
    user_input = textwrap.dedent(
        """
        Hola, soy una empresa llamada 'Constructora del Centro'.
        Nos dedicamos a la construcción de escuelas y pavimentación.
        Estamos en Puebla.
        Nuestra capacidad financiera es media (hasta 10 millones).
        Busca licitaciones para nosotros.
    """
    ).strip()

    runner = InMemoryRunner(agent=root_agent)
    session = await runner.session_service.create_session(
        app_name=runner.app_name, user_id="test_user_puebla"
    )
    content = UserContent(parts=[Part(text=user_input)])
    
    final_response = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content,
    ):
        print(event)
        # Collect the final model response
        if hasattr(event, 'content') and event.content and event.content.parts:
             for part in event.content.parts:
                 if part.text:
                     final_response += part.text

    print(f"Turn 1 Response: {final_response}")

    # Check initial response asks for more info or gives opportunities
    assert "licitación" in final_response.lower() or "oportunidad" in final_response.lower()

    # Turn 2: Provide Risk and Investment Period
    user_input_2 = "Mi enfoque de riesgo es moderado y buscamos proyectos a corto plazo."
    content_2 = UserContent(parts=[Part(text=user_input_2)])
    
    final_response_2 = ""
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content_2,
    ):
        print(event)
        if hasattr(event, 'content') and event.content and event.content.parts:
             for part in event.content.parts:
                 if part.text:
                     final_response_2 += part.text

    print(f"Turn 2 Response: {final_response_2}")

    # Final assertions on the complete plan
    assert "plan" in final_response_2.lower() or "estrategia" in final_response_2.lower()
    assert "riesgo" in final_response_2.lower()

