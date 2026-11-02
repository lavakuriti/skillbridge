from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from justfastapi.core.security import hash_password
from justfastapi.modules.iam.repositories.user import UserRepository
from justfastapi.modules.iam.schemas.user import UserCreate


class EmailAlreadyExistsError(Exception):
    pass


class UserService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = UserRepository(session)

    def register(self, data: UserCreate):
        existing_user = self.repository.get_by_email(str(data.email))

        if existing_user:
            raise EmailAlreadyExistsError

        try:
            user = self.repository.create(
                email=str(data.email).lower(),
                password_hash=hash_password(data.password),
                first_name=data.first_name,
                last_name=data.last_name,
            )

            self.session.commit()
            self.session.refresh(user)

            return user

        except IntegrityError as exc:
            self.session.rollback()

            constraint_name = getattr(
                getattr(exc.orig, "diag", None),
                "constraint_name",
                None,
            )

            if constraint_name == "uq_users_email":
                raise EmailAlreadyExistsError from exc

            raise
