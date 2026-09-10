from typing import Optional
from pydantic import BaseModel


class AlarmItem(BaseModel):
    tag: str
    timestamp: str
    priority: Optional[str] = None
    message: Optional[str] = None
    description: Optional[str] = None
    equipment: Optional[str] = None


class SensorReading(BaseModel):
    tag: str
    timestamp: str
    value: float


class AskRequest(BaseModel):
    question: str


class RagAnswer(BaseModel):
    answer: str
    citations: list[str]
    no_match: bool


class ExplainAlarmRequest(BaseModel):
    alarm_tag: str
    question: Optional[str] = None


class RootCauseRequest(BaseModel):
    alarms: list[AlarmItem]
    sensor_baseline: Optional[list[SensorReading]] = None
    sensor_batch: Optional[list[SensorReading]] = None


class AnomalyResult(BaseModel):
    tag: str
    value: float
    score: float
    is_anomaly: bool


class RootCauseResponse(BaseModel):
    is_flood: bool
    root_alarm: Optional[AlarmItem]
    suppressed_count: int
    cause: RagAnswer
    anomaly_confirmation: list[AnomalyResult] = []


class FeedbackRequest(BaseModel):
    alarm_tag: str
    note: str


class FeedbackResponse(BaseModel):
    status: str


class ShiftHandoverRequest(BaseModel):
    alarms: list[AlarmItem]
    notes: list[str] = []


class ShiftHandoverResponse(BaseModel):
    summary: str
