from sqlalchemy import func, select
from sqlalchemy.orm import Session

from justfastapi.modules.iam.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
        )

        self.session.add(user)
        self.session.flush()

        return user

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(User.email) == email.lower())

        return self.session.scalar(statement)
