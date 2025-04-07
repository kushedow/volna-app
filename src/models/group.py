from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    name: str = Field(..., description="Group Name")
    role: str = Field(default="", description="Role, eg curator, teacher, expert")
    avatar: str = Field(default="", description="Person photo url")
    description: str = Field(default="", description="Person bio / about")
    tg: str = Field(default="", description="Telegram (or other social) ID")


class GroupEvent(BaseModel):
    title: str = Field(..., description="Event Name")
    description: str = Field(default="", description="Event description")
    link: str = Field(default="", description="Event link")
    record: str = Field(default="", description="Record link")
    starts: datetime = Field(default=None, description="Event link")
    ends: datetime = Field(default=None, description="Event link")


class Group(BaseModel):
    id: str = Field(..., description="Group ID as in Calendar")
    chat_tg: str = Field(default="", description="Group chat link")
    curator: Optional[Person] = Field(..., description="Group Curator")
    teacher: Optional[Person] = Field(..., description="Group Teacher")
    expert: Optional[Person] = Field(..., description="Group Expert")
    events: list[GroupEvent] = Field(default_factory=list, description="Group Events")

    @property
    def events_upcoming_3(self):

        now = datetime.now(timezone.utc)
        three_hours_ago = now - timedelta(hours=3)
        upcoming = []

        for event in self.events:
            if event.starts > three_hours_ago:
                upcoming.append(event)
                if len(upcoming) >= 3:
                    break
        return upcoming
