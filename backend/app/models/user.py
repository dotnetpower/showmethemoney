"""User domain models."""

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str = Field(..., description="User identifier")
    name: str
    email: str
    favorite_etfs: list[str] = Field(default_factory=list)
