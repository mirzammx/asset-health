from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. "comp-02"
    name: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    site: Mapped[str] = mapped_column(String)
    area: Mapped[str] = mapped_column(String)
    sensors: Mapped[list["Sensor"]] = relationship(back_populates="asset", order_by="Sensor.id")


class Sensor(Base):
    __tablename__ = "sensors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"))
    tag: Mapped[str] = mapped_column(String, unique=True)  # historian tag
    kind: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)
    baseline_mean: Mapped[float] = mapped_column(Float)
    alarm_limit: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    asset: Mapped[Asset] = relationship(back_populates="sensors")


class HealthSnapshot(Base):
    __tablename__ = "health_snapshots"
    __table_args__ = (UniqueConstraint("asset_id", "ts"),)  # makes re-running the processor idempotent
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime, index=True)  # naive UTC
    health_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String)
    details: Mapped[list] = mapped_column(JSON)  # per-sensor: tag, kind, level, score
