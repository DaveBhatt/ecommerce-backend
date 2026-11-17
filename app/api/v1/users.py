from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas import UserResponse
from app.api.responses import COMMON_ERROR_RESPONSES, problem_response

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        **COMMON_ERROR_RESPONSES,
        401: problem_response("Authentication required."),
    },
)

@router.get("/me", response_model=UserResponse,)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user