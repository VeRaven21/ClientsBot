from database.core import Base

import uuid

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    # is_admin: Mapped[bool] = mapped_column(Bool, default=False)
    tg_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    tg_id: Mapped[int] = mapped_column(nullable=False, unique=True)
