
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
    app_name="financial_advisor",
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

        # Ensure session exists
        try:
            # Attempt to get session; might return None or raise error
            session = await runner.session_service.get_session(request.session_id)
        except Exception:
            session = None
        
        if not session:
             print(f"Creating new session: {request.session_id}")
             await runner.session_service.create_session(
                 session_id=request.session_id,
                 user_id=request.user_id,
                 app_name="financial_advisor"
             )

        async for event in runner.run_async(
            user_id=request.user_id,
            session_id=request.session_id,
            new_message=msg
        ):
            # Print event for debugging (optional, can be removed)
            # print(event)
            
            # Extract text content from the event
            # event.content is likely of type google.genai.types.Content or similar schema
            if hasattr(event, "content") and event.content:
                 # Check if content has 'parts' or 'text'
                 # Based on ADK/GenAI types:
                 if hasattr(event.content, "parts"):
                     for part in event.content.parts:
                         if hasattr(part, "text") and part.text:
                             response_text += part.text
                 elif hasattr(event.content, "text") and event.content.text:
                      response_text += event.content.text
            
            # Some events might be purely textual in 'formatted_string' or similar if tools are skipped
            # But the above covers standard model responses.

        return {
            "status": "processed", 
            "response": response_text.strip() if response_text else "No text response generated."
        }
        
    except Exception as e:
        print(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
