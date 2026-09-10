from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from routes import ask, explain_alarm, feedback, root_cause, shift_handover

app = FastAPI(title="SignalForge Root Cause Advisor")

app.include_router(explain_alarm.router)
app.include_router(root_cause.router)
app.include_router(shift_handover.router)
app.include_router(ask.router)
app.include_router(feedback.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Last-resort safety net: an unhandled error anywhere should never show
    # an operator a raw stack trace mid-demo. Individual services already
    # degrade gracefully (see services/rag.py); this only catches whatever
    # slips past that.
    return JSONResponse(
        status_code=503,
        content={"detail": "Service temporarily unavailable. Please retry."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
