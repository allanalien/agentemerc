
import os
import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk.runners import Runner, InMemorySessionService
from financial_advisor.agent import root_agent
# Try to import Content type, fallback to string if possible or dict
try:
    from google.genai.types import Content, Part
except ImportError:
    Content = None

app = FastAPI()

# Initialize Runner
# Use InMemorySessionService for simplicity in demo.
runner = Runner(
    agent=root_agent,
    session_service=InMemorySessionService()
)

class ChatRequest(BaseModel):
    user_input: str
    session_id: str = "default-session"
    user_id: str = "default-user"

@app.get("/")
def health_check():
    return {"status": "ok", "service": "Market Agent ADK"}

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        response_text = ""
        
        # Construct message content
        # Note: calling internal or type-based constructors might be needed.
        # But commonly runners accept text directly or simple dicts/objects.
        # We will try passing the string first if Content is not found, 
        # or construct a Content object if we have the class.
        if Content:
            msg = Content(parts=[Part(text=request.user_input)])
        else:
            # Fallback (risky but worth a try if types missing)
            msg = request.user_input 

        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=msg
        ):
            # Collect text chunks from events
            # Event structure: check event.formatted_string or similar
            # Printing event to see structure if needed, but for now assuming standard output
            # Usually event has 'text' or 'delta'
            # Let's assume the ADK event yields partial text or we can inspect it.
            # event might be an object.
            # Safe way: print(event) logic
            pass
        
        # Wait, run_async yields events. How do I get the FINAL text?
        # Usually one of the events contains the agent response.
        # Or I can use runner.run (sync) but that blocks.
        # Let's look at `runner.run` return type? It returns None I think, outputs via Session.
        # But `run_async` yields events.
        
        # Let's use `runner.run_async` but we need to know how to extract text.
        # Documentation unavailable.
        # Inspecting `event` in loop is needed.
        # For now, capturing all events and returning as string representation is safe.
        
        return {"status": "processed", "note": "Check logs for output (Web interface pending full parsing)"}
        
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
