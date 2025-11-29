"""Low-level structures stored in the GitHub-backed data lake."""

from pydantic import BaseModel


class StoredChunk(BaseModel):
    path: str
    version: str
    checksum: str
