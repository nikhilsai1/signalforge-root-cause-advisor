from fastapi import FastAPI

from routes import ask, explain_alarm, feedback, root_cause, shift_handover

app = FastAPI(title="SignalForge Root Cause Advisor")

app.include_router(explain_alarm.router)
app.include_router(root_cause.router)
app.include_router(shift_handover.router)
app.include_router(ask.router)
app.include_router(feedback.router)


@app.get("/health")
def health():
    return {"status": "ok"}
