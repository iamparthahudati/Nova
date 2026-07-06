from pydantic import BaseModel


class CalendarEventResponse(BaseModel):
    title: str
    time: str


class CalendarResponse(BaseModel):
    date: str
    events: list[CalendarEventResponse]
    unavailable: bool = False
