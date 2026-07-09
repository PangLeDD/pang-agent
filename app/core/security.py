from typing import Annotated

from fastapi import Header, HTTPException, status

DEV_AUTH_TOKEN = "8d3f4bd6a70a4cb89c49f6a1b0f0d5d2"


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    # ponytail: dev-only global token; replace with real JWT/RBAC when users exist.
    if authorization != f"Bearer {DEV_AUTH_TOKEN}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": "dev-user", "username": "dev"}
