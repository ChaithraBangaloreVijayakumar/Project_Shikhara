"""
Project Shikhara — FastAPI application entry point.
Run with: uvicorn backend.main:app --reload
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel

from database import get_db
from models import CityItem, StateItem
from routers import temples

app = FastAPI(
    title="Project Shikhara API",
    description="Hindu temple directory for Germany",
    version="1.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(temples.router)


# ── Cities & States ───────────────────────────────────────────────────────────

@app.get("/cities", response_model=list[CityItem])
def get_cities(conn=Depends(get_db)):
    """Get all cities that have at least one temple, with temple count."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT city, COUNT(*) AS temple_count
            FROM temples
            WHERE city IS NOT NULL
            GROUP BY city
            ORDER BY city
        """)
        return cur.fetchall()


@app.get("/states", response_model=list[StateItem])
def get_states(conn=Depends(get_db)):
    """Get all states that have at least one temple, with temple count."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT l.state, COUNT(*) AS temple_count
            FROM temples t
            JOIN location l ON t.postal_code = l.postal_code
            GROUP BY l.state
            ORDER BY l.state
        """)
        return cur.fetchall()


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Ask the AI chatbot a question about Hindu temples in Germany."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from chatbot.agent import ask
    answer = ask(request.question)
    return ChatResponse(answer=answer)


@app.post("/chat/stream")
def chat_stream(request: ChatRequest):
    """Streaming version of the chat endpoint."""
    from fastapi.responses import StreamingResponse
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from chatbot.agent import ask_stream
    return StreamingResponse(ask_stream(request.question), media_type="text/plain")


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}