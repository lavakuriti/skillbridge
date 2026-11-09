from sqlalchemy.orm import Session
from sqlalchemy import select, func
from justfastapi.modules.iam.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self, email: str, first_name: str, last_name: str, password_hash: str
    ) -> User:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=password_hash,
        )
        self.session.add(user)
        self.session.flush()
        return user

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(func.lower(email) == email.lower())
        return self.session.scalar(statement)

    def getUsers(self, params: dict[str, object]) -> list[User]:
        statement = select(User)
        return list(self.session.scalars(statement).all())

    def update_user(
        self, id: int, email: str, first_name: str, last_name: str, password_hash: str
    ) -> User | None:
        try:
            user = self.session.get(User, id)
            if user:
                user.last_name = last_name
                user.first_name = first_name
                user.email = email
                user.password_hash = password_hash
                self.session.commit()
                self.session.refresh(user)
                return user
        except:
            raise
