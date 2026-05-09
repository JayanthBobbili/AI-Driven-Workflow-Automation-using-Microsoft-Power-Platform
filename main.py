from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import re


app = FastAPI(title="Request Classifier API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Classification rules ──────────────────────────────────────────────────────
HIGH_PRIORITY_KEYWORDS = [
    "urgent", "asap", "immediately", "critical", "emergency", "deadline",
    "block", "blocker", "broken", "outage", "down", "crash", "fail",
    "approval needed", "needed now", "right away", "important", "priority"
]

MEDIUM_PRIORITY_KEYWORDS = [
    "soon", "when possible", "please review", "request", "update",
    "change", "modify", "help", "issue", "problem", "fix", "bug",
    "review", "check", "look into", "follow up", "clarify"
]

LOW_PRIORITY_KEYWORDS = [
    "whenever", "no rush", "fyi", "info", "question", "curious",
    "suggestion", "idea", "enhancement", "feature", "nice to have",
    "low priority", "optional", "future", "consider"
]

def classify_text(text: str) -> dict:
    """Rule-based + keyword scoring classifier."""
    lower = text.lower()

    high_score   = sum(1 for kw in HIGH_PRIORITY_KEYWORDS   if kw in lower)
    medium_score = sum(1 for kw in MEDIUM_PRIORITY_KEYWORDS if kw in lower)
    low_score    = sum(1 for kw in LOW_PRIORITY_KEYWORDS    if kw in lower)

    # Boost score for exclamation marks and ALL CAPS words
    if "!" in text:
        high_score += 1
    if re.search(r'\b[A-Z]{3,}\b', text):
        high_score += 1

    if high_score > 0:
        category   = "High Priority"
        confidence = min(0.95, 0.6 + high_score * 0.1)
        reason     = f"Detected urgency indicators: {high_score} high-priority keyword(s)"
    elif medium_score > low_score:
        category   = "Medium Priority"
        confidence = min(0.90, 0.55 + medium_score * 0.08)
        reason     = f"Detected {medium_score} medium-priority keyword(s)"
    elif low_score > 0:
        category   = "Low Priority"
        confidence = min(0.85, 0.55 + low_score * 0.08)
        reason     = f"Detected {low_score} low-priority keyword(s)"
    else:
        category   = "Medium Priority"
        confidence = 0.50
        reason     = "No strong keywords detected — defaulted to Medium Priority"

    return {
        "category":   category,
        "confidence": round(confidence, 2),
        "reason":     reason,
        "scores":     {"high": high_score, "medium": medium_score, "low": low_score}
    }


# ── Request / Response Models ─────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    request_id:   str
    user_name:    str
    request_text: str
    timestamp:    str | None = None

class ClassifyResponse(BaseModel):
    request_id:   str
    user_name:    str
    request_text: str
    ai_result:    str
    category:     str
    confidence:   float
    reason:       str
    status:       str
    processed_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Request Classifier API is running ✅", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    if not req.request_text or not req.request_text.strip():
        raise HTTPException(status_code=422, detail="request_text cannot be empty")

    result = classify_text(req.request_text)

    return ClassifyResponse(
        request_id   = req.request_id,
        user_name    = req.user_name,
        request_text = req.request_text,
        ai_result    = result["category"],
        category     = result["category"],
        confidence   = result["confidence"],
        reason       = result["reason"],
        status       = "Classified",
        processed_at = datetime.utcnow().isoformat() + "Z"
    )

@app.post("/classify/batch")
def classify_batch(requests: list[ClassifyRequest]):
    return [classify(r) for r in requests]