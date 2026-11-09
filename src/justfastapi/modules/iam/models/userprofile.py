from datetime import datetime
from typing import List
from sqlalchemy import (
    BigInteger,
    DECIMAL,
    Boolean,
    DateTime,
    Identity,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from justfastapi.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", name="user_profile_user_id_fkey"),
        primary_key=True,
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[List["Address"]] = relationship(
        back_populates="user_profiles",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    __table_args__ = (Index("idx_user_profiles_user_id", "user_id"),)


class Address(Base):
    __tablename__ = "address"
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE", name="address_user_id_fkey"),
        primary_key=True,
    )
    address_line_1: Mapped[str] = mapped_column(String(225), nullable=False)
    address_line_2: Mapped[str] = mapped_column(String(225))
    city: Mapped[str] = mapped_column(String(225), nullable=False)
    state_province: Mapped[str] = mapped_column(String(100))
    postal_code: Mapped[str] = mapped_column(String(20))
    latitude: Mapped[int] = mapped_column(DECIMAL(9, 6))
    longitude: Mapped[int] = mapped_column(DECIMAL(9, 6))
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    is_commercial: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    __table_args__ = (Index("idx_address_user_id", "user_id"),)
