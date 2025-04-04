from pydantic import BaseModel, Field


class FAQ(BaseModel):
    question: str
    answer: str
