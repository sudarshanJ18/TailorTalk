from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import os
import json
from typing import List, Dict
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalendarManager:
    def __init__(self):
        self.service = self._get_calendar_service()
        self.timezone = pytz.timezone(settings.TIMEZONE)

    def _get_calendar_service(self):
        """Initialize Google Calendar service with credentials from ENV"""
        try:
            creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS_JSON"])
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Failed to initialize calendar service: {e}")
            return None

    def get_free_slots(self, date_str: str, duration: int = 60) -> List[str]:
        """Get available time slots for a given date"""
        if not self.service:
            return []

        try:
            # Parse the date
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Create start and end times for the day
            start_time = self.timezone.localize(
                datetime.combine(target_date, datetime.min.time().replace(hour=settings.BUSINESS_START_HOUR))
            )
            end_time = self.timezone.localize(
                datetime.combine(target_date, datetime.min.time().replace(hour=settings.BUSINESS_END_HOUR))
            )

            # Get existing events
            events_result = self.service.events().list(
                calendarId=settings.CALENDAR_ID,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            # Generate all possible slots
            all_slots = []
            current_time = start_time

            while current_time + timedelta(minutes=duration) <= end_time:
                all_slots.append(current_time)
                current_time += timedelta(minutes=30)  # 30-minute intervals

            # Filter out busy slots
            free_slots = []
            for slot in all_slots:
                slot_end = slot + timedelta(minutes=duration)
                is_free = True

                for event in events:
                    event_start = datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date')))
                    event_end = datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date')))

                    # Check for overlap
                    if not (slot_end <= event_start or slot >= event_end):
                        is_free = False
                        break

                if is_free:
                    free_slots.append(slot.strftime("%I:%M %p"))

            return free_slots

        except Exception as e:
            logger.error(f"Error getting free slots: {e}")
            return []

    def book_appointment(self, date_str: str, time_str: str, duration: int = 60,
                         title: str = "Appointment", description: str = "") -> Dict:
        """Book an appointment in Google Calendar"""
        if not self.service:
            return {"success": False, "error": "Calendar service not available"}

        try:
            # Parse date and time
            appointment_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %I:%M %p")
            start_time = self.timezone.localize(appointment_datetime)
            end_time = start_time + timedelta(minutes=duration)

            # Create event
            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': settings.TIMEZONE,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': settings.TIMEZONE,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }

            created_event = self.service.events().insert(
                calendarId=settings.CALENDAR_ID,
                body=event
            ).execute()

            return {
                "success": True,
                "event_id": created_event['id'],
                "event_link": created_event.get('htmlLink', ''),
                "message": f"Appointment booked successfully for {date_str} at {time_str}"
            }

        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {"success": False, "error": str(e)}


calendar_manager = CalendarManager()
