from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    available_slots: Optional[List[str]] = None
    booking_confirmed: Optional[bool] = None

class BookingRequest(BaseModel):
    date: str
    time: str
    duration: Optional[int] = 60
    title: Optional[str] = "Appointment"
    description: Optional[str] = ""

class AvailabilityRequest(BaseModel):
    date: str
    duration: Optional[int] = 60