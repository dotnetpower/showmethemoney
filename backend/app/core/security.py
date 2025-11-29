"""Placeholder security hooks for authentication/authorization."""

from fastapi import Depends, HTTPException, status


def get_current_user(token: str | None = None):
    """Basic token check that can be replaced with a full auth provider later."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return {"token": token}
