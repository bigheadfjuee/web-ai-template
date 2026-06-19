from fastapi import APIRouter, Depends

from ..auth import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
