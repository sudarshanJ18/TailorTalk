from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from booking_agent import booking_agent
from schemas import ChatRequest, ChatResponse, BookingRequest, AvailabilityRequest
from calendar_utils import calendar_manager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TailorTalk API",
    description="Appointment Booking Assistant API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TailorTalk API is running! 🚀"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2024-12-11T10:00:00Z"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for natural language interactions"""
    try:
        logger.info(f"Received chat request: {request.message}")
        result = booking_agent.process_message(request.message)
        
        return ChatResponse(
            response=result["response"],
            available_slots=result.get("available_slots"),
            booking_confirmed=result.get("booking_confirmed")
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/book")
async def book_appointment(request: BookingRequest):
    """Direct booking endpoint"""
    try:
        result = calendar_manager.book_appointment(
            request.date,
            request.time,
            request.duration,
            request.title,
            request.description
        )
        
        if result["success"]:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Booking endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/availability")
async def check_availability(request: AvailabilityRequest):
    """Check availability for a specific date"""
    try:
        slots = calendar_manager.get_free_slots(request.date, request.duration)
        return {"date": request.date, "available_slots": slots}
        
    except Exception as e:
        logger.error(f"Availability endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)