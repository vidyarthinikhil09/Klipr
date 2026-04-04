"""
Authentication dependencies for FastAPI routes.
"""
from fastapi import HTTPException, Header, Depends
from typing import Optional
from ..database import get_supabase


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Validate Supabase JWT and return user info.
    
    The frontend sends the Supabase access token in the Authorization header.
    We validate it using Supabase's auth.get_user() method.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    # Remove "Bearer " prefix if present
    token = authorization.replace("Bearer ", "")
    
    try:
        # Validate token with Supabase
        client = get_supabase()
        response = client.auth.get_user(token)
        
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "role": response.user.role
        }
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authentication failed: {str(e)}"
        )


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    """
    Same as get_current_user but returns None instead of raising exception.
    Useful for routes that work with or without authentication.
    """
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


class RequireYouTubeConnection:
    """
    Dependency that requires user to have connected their YouTube account.
    """
    
    async def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        from ..database import Database
        
        db = Database(user.get("id"))
        token = await db.get_youtube_token()
        
        if not token:
            raise HTTPException(
                status_code=403,
                detail="YouTube account not connected. Please connect your YouTube account first."
            )
        
        # Add token to user dict
        user["youtube_token"] = token
        return user


require_youtube = RequireYouTubeConnection()
