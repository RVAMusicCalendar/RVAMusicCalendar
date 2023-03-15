import string

from data import VenueInfo
from datetime import datetime, time


class Event:
    def __init__(self, venueInfo: VenueInfo, eventDateTime: datetime, eventDoorOpenTime: time, eventName: str, eventImageURL: str, description: str, eventUrl: str):
        self.description = description
        self.eventDoorOpenTime = eventDoorOpenTime
        self.eventImageURL = eventImageURL
        self.eventName = eventName
        self.eventDateTime = eventDateTime
        self.venueInfo = venueInfo
        self.eventUrl = eventUrl

    def __str__(self):
        return f"{self.eventName}, on {self.eventDateTime}, with the doors opening {self.eventDoorOpenTime} at {self.venueInfo.venueName}"

    def __repr__(self):
        return str(self)
