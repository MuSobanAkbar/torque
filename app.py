from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from explain import generate_explanation
from extract import extract_jobs
from quote import build_quote

app = FastAPI(title="torque")
app.mount("/static", StaticFiles(directory="static"), name="static")


class QuoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    notes: str = Field(..., min_length=1, max_length=2000)


@app.get("/")
def index() -> FileResponse:
    return FileResponse("static/index.html")


@app.post("/quote")
def create_quote(payload: QuoteRequest) -> dict:
    try:
        extracted = extract_jobs(payload.notes)
        quote = build_quote(extracted.items)
        explanation, used_fallback = generate_explanation(quote)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Pipeline error: {type(exc).__name__}") from exc

    return {
        "quote": quote,
        "explanation": explanation,
        "used_fallback": used_fallback,
    }