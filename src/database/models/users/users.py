from database.core import Base

import enum

import uuid

from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ENUM


class UserRoleEnum(str, enum.Enum):
    WORKER = "WORKER"
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[UserRoleEnum] = mapped_column(
        ENUM(UserRoleEnum, name="userroleenum", create_type=True),
        default=UserRoleEnum.CLIENT,
        nullable=False,
        server_default="CLIENT",
    )
