from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class Person(BaseModel):
    name: str = Field(..., description="Group Name")
    role: str = Field(default="", description="Role, eg curator, teacher, expert")
    avatar: str = Field(default="", description="Person photo url")
    description: str = Field(default="", description="Person bio / about")
    tg: str = Field(default="", description="Telegram (or other social) ID")


class Group(BaseModel):

    id: str = Field(..., description="Group ID as in Calendar")
    chat_tg: str = Field(default="", description="Group chat link")
    curator: Optional[Person] = Field(..., description="Group Curator")
    teacher: Optional[Person]= Field(..., description="Group Teacher")
    expert: Optional[Person] = Field(..., description="Group Expert")
