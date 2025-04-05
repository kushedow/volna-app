from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


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
    starts: datetime = Field(default=None, description="Event link")
    ends: datetime = Field(default=None, description="Event link")


class Group(BaseModel):
    id: str = Field(..., description="Group ID as in Calendar")
    chat_tg: str = Field(default="", description="Group chat link")
    curator: Optional[Person] = Field(..., description="Group Curator")
    teacher: Optional[Person] = Field(..., description="Group Teacher")
    expert: Optional[Person] = Field(..., description="Group Expert")
    events: list[GroupEvent] = Field(default_factory=list, description="Group Events")
