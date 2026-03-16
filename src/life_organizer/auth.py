"""API key authentication dependency."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from life_organizer.config import Settings, get_settings

_api_key_header = APIKeyHeader(name="X-API-Key")


async def verify_api_key(
    api_key: str = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    """Validate the API key from the X-API-Key header.

    Args:
        api_key: The API key from the request header.
        settings: Application settings.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key
