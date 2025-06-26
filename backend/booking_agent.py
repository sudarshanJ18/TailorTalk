from langgraph.graph import StateGraph
from typing import TypedDict, List, Optional
import re
from datetime import datetime, timedelta
from calendar_utils import calendar_manager
import logging

logger = logging.getLogger(__name__)

class ChatState(TypedDict):
    input: str
    intent: str
    extracted_date: Optional[str]
    extracted_time: Optional[str]
    free_slots: List[str]
    output: str
    booking_confirmed: bool
    needs_clarification: bool

class BookingAgent:
    def __init__(self):
        self.graph = self._build_graph()
    
    def detect_intent(self, state: ChatState) -> ChatState:
        """Detect user intent from input"""
        user_input = state["input"].lower()
        
        booking_keywords = ["book", "schedule", "appointment", "meeting", "reserve", "slot"]
        availability_keywords = ["available", "free", "slots", "when", "check"]
        cancel_keywords = ["cancel", "reschedule", "change"]
        
        if any(keyword in user_input for keyword in booking_keywords):
            intent = "book_appointment"
        elif any(keyword in user_input for keyword in availability_keywords):
            intent = "check_availability"
        elif any(keyword in user_input for keyword in cancel_keywords):
            intent = "modify_appointment"
        else:
            intent = "general_inquiry"
        
        logger.info(f"Detected intent: {intent} from input: {user_input}")
        
        return {
            **state,
            "intent": intent,
            "needs_clarification": False
        }
    
    def extract_datetime(self, state: ChatState) -> ChatState:
        """Extract date and time from user input"""
        user_input = state["input"]
        
        # Extract date patterns
        date_patterns = [
            r'\b(\d{4}-\d{2}-\d{2})\b',  # YYYY-MM-DD
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',  # MM/DD/YYYY
            r'\b(today|tomorrow)\b',
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        ]
        
        # Extract time patterns
        time_patterns = [
            r'\b(\d{1,2}:\d{2}\s*(?:am|pm))\b',
            r'\b(\d{1,2}\s*(?:am|pm))\b',
            r'\b(\d{1,2}:\d{2})\b'
        ]
        
        extracted_date = None
        extracted_time = None
        
        for pattern in date_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                date_str = match.group(1)
                if date_str == "today":
                    extracted_date = datetime.now().strftime("%Y-%m-%d")
                elif date_str == "tomorrow":
                    extracted_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    try:
                        if "/" in date_str:
                            parsed_date = datetime.strptime(date_str, "%m/%d/%Y")
                        else:
                            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                        extracted_date = parsed_date.strftime("%Y-%m-%d")
                    except:
                        continue
                break
        
        for pattern in time_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                extracted_time = match.group(1)
                break
        
        return {
            **state,
            "extracted_date": extracted_date,
            "extracted_time": extracted_time
        }
    
    def check_availability(self, state: ChatState) -> ChatState:
        """Check available slots for the extracted date"""
        if not state["extracted_date"]:
            return {
                **state,
                "needs_clarification": True,
                "output": "I'd be happy to check availability! Could you please specify the date? (e.g., 'today', 'tomorrow', or 'YYYY-MM-DD')"
            }
        
        try:
            free_slots = calendar_manager.get_free_slots(state["extracted_date"])
            
            if not free_slots:
                return {
                    **state,
                    "free_slots": [],
                    "output": f"Sorry, no available slots found for {state['extracted_date']}. Would you like to try a different date?"
                }
            
            slots_text = ", ".join(free_slots[:5])  # Show first 5 slots
            return {
                **state,
                "free_slots": free_slots,
                "output": f"Available slots for {state['extracted_date']}: {slots_text}"
            }
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {
                **state,
                "output": "Sorry, I'm having trouble checking availability right now. Please try again later."
            }
    
    def confirm_booking(self, state: ChatState) -> ChatState:
        """Confirm and book the appointment"""
        if not state["extracted_date"] or not state["extracted_time"]:
            return {
                **state,
                "needs_clarification": True,
                "output": "To book your appointment, I need both the date and time. Please provide both (e.g., 'Book for tomorrow at 2 PM')"
            }
        
        try:
            result = calendar_manager.book_appointment(
                state["extracted_date"],
                state["extracted_time"],
                title="TailorTalk Appointment"
            )
            
            if result["success"]:
                return {
                    **state,
                    "booking_confirmed": True,
                    "output": f"✅ {result['message']}! You'll receive email and popup reminders."
                }
            else:
                return {
                    **state,
                    "output": f"❌ Booking failed: {result['error']}. Please try a different time slot."
                }
                
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            return {
                **state,
                "output": "Sorry, I encountered an error while booking. Please try again."
            }
    
    def handle_general_inquiry(self, state: ChatState) -> ChatState:
        """Handle general inquiries and greetings"""
        user_input = state["input"].lower()
        
        if any(greeting in user_input for greeting in ["hello", "hi", "hey", "good morning", "good afternoon"]):
            return {
                **state,
                "output": "Hello! I'm your appointment booking assistant. I can help you:\n• Check available time slots\n• Book appointments\n• Reschedule existing appointments\n\nWhat would you like to do today?"
            }
        
        return {
            **state,
            "output": "I'm here to help you with appointment bookings. You can ask me to:\n• 'Check availability for tomorrow'\n• 'Book an appointment for 2 PM today'\n• 'What slots are available on 2024-12-15?'\n\nHow can I assist you?"
        }
    
    def _build_graph(self):
        """Build the LangGraph workflow"""
        builder = StateGraph(ChatState)
        
        # Add nodes
        builder.add_node("detect_intent", self.detect_intent)
        builder.add_node("extract_datetime", self.extract_datetime)
        builder.add_node("check_availability", self.check_availability)
        builder.add_node("confirm_booking", self.confirm_booking)
        builder.add_node("handle_general", self.handle_general_inquiry)
        
        # Set entry point
        builder.set_entry_point("detect_intent")
        
        # Add conditional edges
        def route_after_intent(state: ChatState):
            intent = state["intent"]
            if intent in ["book_appointment", "check_availability"]:
                return "extract_datetime"
            else:
                return "handle_general"
        
        def route_after_extraction(state: ChatState):
            intent = state["intent"]
            if intent == "check_availability":
                return "check_availability"
            elif intent == "book_appointment":
                return "confirm_booking"
            else:
                return "handle_general"
        
        builder.add_conditional_edges("detect_intent", route_after_intent)
        builder.add_conditional_edges("extract_datetime", route_after_extraction)
        
        # Set finish points
        builder.set_finish_point("check_availability")
        builder.set_finish_point("confirm_booking")
        builder.set_finish_point("handle_general")
        
        return builder.compile()
    
    def process_message(self, message: str) -> dict:
        """Process a user message and return response"""
        initial_state = {
            "input": message,
            "intent": "",
            "extracted_date": None,
            "extracted_time": None,
            "free_slots": [],
            "output": "",
            "booking_confirmed": False,
            "needs_clarification": False
        }
        
        try:
            result = self.graph.invoke(initial_state)
            return {
                "response": result["output"],
                "available_slots": result.get("free_slots", []),
                "booking_confirmed": result.get("booking_confirmed", False)
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "response": "I apologize, but I encountered an error processing your request. Please try again.",
                "available_slots": [],
                "booking_confirmed": False
            }

# Global instance
booking_agent = BookingAgent()