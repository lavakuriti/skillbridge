import enum
from datetime import datetime, date
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Date,
    Enum,
    ForeignKey,
    Identity,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from justfastapi.core.database import Base

# ============================================================
# ENUMS
# ============================================================


class RoleScope(str, enum.Enum):
    PLATFORM = "platform"
    ORGANIZATION = "organization"


class UserTokenType(str, enum.Enum):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    INVITATION = "invitation"


def enum_column(enum_class: type[enum.Enum], name: str):
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda values: [item.value for item in values],
        length=32,
    )


# ============================================================
# MIXINS
# ============================================================


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================
# ORGANIZATION
# ============================================================


class Organization(TimestampMixin, Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    # Relationships

    user_organizations: Mapped[list["UserOrganization"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    roles: Mapped[list["Role"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ============================================================
# USER
# ============================================================


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )

    password_hash: Mapped[str | None] = mapped_column(Text)

    full_name: Mapped[str | None] = mapped_column(
        String(255),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    # Relationships

    user_organizations: Mapped[list["UserOrganization"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="UserOrganization.user_id",
    )

    user_platform_roles: Mapped[list["UserPlatformRole"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="UserPlatformRole.user_id",
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user_tokens: Mapped[list["UserToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ============================================================
# ROLE
# ============================================================


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(Text)

    scope: Mapped[RoleScope] = mapped_column(
        enum_column(RoleScope, "role_scope"),
        nullable=False,
    )

    # NULL = system role; non-NULL = organization-owned custom role
    organization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )

    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )

    # Relationships

    organization: Mapped["Organization | None"] = relationship(
        back_populates="roles",
    )

    user_organizations: Mapped[list["UserOrganization"]] = relationship(
        back_populates="role",
        passive_deletes=True,
    )

    user_platform_roles: Mapped[list["UserPlatformRole"]] = relationship(
        back_populates="role",
        passive_deletes=True,
    )

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_roles_organization_name",
        ),
        CheckConstraint(
            "scope <> 'platform' OR organization_id IS NULL",
            name="ck_platform_role_without_organization",
        ),
        CheckConstraint(
            "organization_id IS NULL OR is_system = false",
            name="ck_custom_role_not_system",
        ),
    )


# ============================================================
# USER ORGANIZATION MEMBERSHIP
# ============================================================


class UserOrganization(Base):
    __tablename__ = "user_organizations"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )

    assigned_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships

    user: Mapped["User"] = relationship(
        back_populates="user_organizations",
        foreign_keys=[user_id],
    )

    organization: Mapped["Organization"] = relationship(
        back_populates="user_organizations",
    )

    role: Mapped["Role"] = relationship(
        back_populates="user_organizations",
    )
    organization_profile: Mapped["OrganizationUserProfile | None"] = relationship(
        back_populates="user_organization",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )


# ============================================================
# PLATFORM ROLE ASSIGNMENT
# ============================================================


class UserPlatformRole(Base):
    __tablename__ = "user_platform_roles"

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    assigned_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships

    user: Mapped["User"] = relationship(
        back_populates="user_platform_roles",
        foreign_keys=[user_id],
    )

    role: Mapped["Role"] = relationship(
        back_populates="user_platform_roles",
    )


# ============================================================
# PERMISSION
# ============================================================


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(Text)

    scope: Mapped[RoleScope] = mapped_column(
        enum_column(RoleScope, "permission_scope"),
        nullable=False,
    )

    # Relationships

    role_permissions: Mapped[list["RolePermission"]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# ============================================================
# ROLE PERMISSION
# ============================================================


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )

    permission_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships

    role: Mapped["Role"] = relationship(
        back_populates="role_permissions",
    )

    permission: Mapped["Permission"] = relationship(
        back_populates="role_permissions",
    )


# ============================================================
# REFRESH TOKENS
# ============================================================


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    family_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    replaced_by_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
    )

    user_agent: Mapped[str | None] = mapped_column(
        String(512),
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships

    user: Mapped["User"] = relationship(
        back_populates="refresh_tokens",
    )


# ============================================================
# USER TOKENS
# ============================================================


class UserToken(Base):
    __tablename__ = "user_tokens"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    type: Mapped[UserTokenType] = mapped_column(
        enum_column(UserTokenType, "user_token_type"),
        nullable=False,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships

    user: Mapped["User"] = relationship(
        back_populates="user_tokens",
    )


# ============================================================
# AUDIT LOG
# ============================================================


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    organization_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("organizations.id", ondelete="SET NULL"),
    )

    actor_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    resource_type: Mapped[str | None] = mapped_column(
        String(100),
    )

    resource_id: Mapped[str | None] = mapped_column(
        String(64),
    )

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)

    last_name: Mapped[str] = mapped_column(String(100), nullable=False)

    display_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)

    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    bio: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="user_profile")
    addresses: Mapped[list["UserAddress"]] = relationship(
        back_populates="user_profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    contacts: Mapped[list["UserContact"]] = relationship(
        back_populates="user_profile",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class UserContact(Base):
    __tablename__ = "user_contacts"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    user_profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    contact_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    user_profile: Mapped["UserProfile"] = relationship(
        back_populates="contacts",
    )


class UserAddress(Base):
    __tablename__ = "user_addresses"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    user_profile_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )

    address_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    address_line_1: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    address_line_2: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    landmark: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    city: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    country: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    postal_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    user_profile: Mapped["UserProfile"] = relationship(
        back_populates="addresses",
    )

    


        __tablename__ = "user_contacts"

        id: Mapped[int] = mapped_column(
            BigInteger,
            Identity(always=True),
            primary_key=True,
        )

        user_profile_id: Mapped[int] = mapped_column(
            BigInteger,
            ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        )

        contact_type: Mapped[str] = mapped_column(
            String(30),
            nullable=False,
        )

        value: Mapped[str] = mapped_column(
            String(255),
            nullable=False,
        )

        is_primary: Mapped[bool] = mapped_column(
            Boolean,
            nullable=False,
            default=False,
        )

        is_verified: Mapped[bool] = mapped_column(
            Boolean,
            nullable=False,
            default=False,
        )

        user_profile: Mapped["UserProfile"] = relationship(
            back_populates="contacts",
        )


class OrganizationUserProfile(Base):
    __tablename__ = "organization_user_profiles"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    user_organization_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user_organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    employee_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    department_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    designation_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("designations.id", ondelete="SET NULL"),
        nullable=True,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    joining_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reporting_manager_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("user_organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    work_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user_organization: Mapped["UserOrganization"] = relationship(
        back_populates="organization_profile",
    )
