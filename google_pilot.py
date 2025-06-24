import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    creds = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "../credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    # Feature 1: List all calendars
    print("Fetching all calendars:")
    calendar_list = service.calendarList().list().execute().get("items", [])
    for calendar in calendar_list:
        print(calendar["summary"], calendar["id"])

    """ # Feature 2: Create a new calendar
    new_calendar = {
        "summary": "New Python Calendar",
        "timeZone": "America/Los_Angeles",
    }
    created_calendar = service.calendars().insert(body=new_calendar).execute()
    print(f"Created calendar: {created_calendar['id']}") """

    # Feature 3: Insert an event
    event = {
        "summary": "Python Meeting",
        "location": "800 Howard St., San Francisco, CA 94103",
        "description": "A meeting to discuss Python projects.",
        "start": {
            "date": "2025-06-22",
            "timeZone": "America/New_York",
        },
        "end": {
            "date": "2025-06-22",
            "timeZone": "America/New_York",
        },
    }
    created_event = (
        service.events()
        .insert(calendarId="lschoch@gmail.com", body=event)
        .execute()
    )
    print(f"Created event: {created_event['id']}")

    """ # Feature 4: Update an event
    updated_event = created_event
    updated_event["description"] = (
        "An updated meeting to discuss Python projects."
    )
    updated_event = (
        service.events()
        .update(
            calendarId=created_calendar["id"],
            eventId=created_event["id"],
            body=updated_event,
        )
        .execute()
    )
    print(f"Updated event: {updated_event['id']}") """

    """ # Feature 5: Delete an event
    service.events().delete(
        calendarId=created_calendar["id"], eventId=updated_event["id"]
    ).execute()
    print(f"Deleted event: {updated_event['id']}") """


if __name__ == "__main__":
    main()
