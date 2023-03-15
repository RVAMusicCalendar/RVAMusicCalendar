import string

from data import VenueInfo
from datetime import datetime, time


class Event:
    def __init__(self, venue_info: VenueInfo, event_datetime: datetime, door_time: time, event_name: str, image_url: str, description: str, event_url: str):
        self.description = description
        self.door_time = door_time
        self.image_url = image_url
        self.event_name = event_name
        self.event_datetime = event_datetime
        self.venue_info = venue_info
        self.url = event_url

    def __str__(self):
        return f"{self.event_name}, on {self.event_datetime}, with the doors opening {self.door_time} at {self.venue_info.venue_name}"

    def __repr__(self):
        return str(self)

    @property
    def full_description(self):
        return f'''
        <b>Doors open at {self.door_time.strftime("%I:%M %p")}</b> 
        <br>
        {self.description}
        <br>
        {self.url}
        '''
