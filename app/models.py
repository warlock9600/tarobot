from datetime import date, datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

GenderEnum = Enum("male", "female", name="gender")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    gender: Mapped[Optional[str]] = mapped_column(GenderEnum)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_spontaneous_offer_date: Mapped[Optional[date]] = mapped_column(Date)
    last_spontaneous_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    readings: Mapped[list["Reading"]] = relationship(back_populates="user")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    arcana: Mapped[str] = mapped_column(String(100), nullable=False)
    prediction: Mapped[str] = mapped_column(Text, nullable=False)
    is_spontaneous: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="readings")
