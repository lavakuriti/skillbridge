from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from justfastapi.common.dependencies import get_database_session
from justfastapi.modules.iam.schemas.user import UserCreate, UserResponse
from justfastapi.modules.iam.services.user import (
    EmailAlreadyExistsError,
    UserService,
)

router = APIRouter(prefix="/iam/users", tags=["IAM - Users"])


@router.get("", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
def get_users(
    session: Annotated[Session, Depends(get_database_session)],
):
    service = UserService(session)

    try:
        return service.get_users()
    except:
        print("error")
        raise


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    data: UserCreate,
    session: Annotated[Session, Depends(get_database_session)],
):
    service = UserService(session)

    try:
        return service.register_user(data)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        ) from exc
