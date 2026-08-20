from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(30), default="city")

class Site(Base):
    __tablename__ = "sites"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    site_type: Mapped[str] = mapped_column(String(100), nullable=False)
    population: Mapped[int] = mapped_column(Integer, default=0)
    mode: Mapped[str] = mapped_column(String(30), default="normal")
    rate: Mapped[int] = mapped_column(Integer, default=20)
    contact_name: Mapped[str] = mapped_column(String(150), default="")
    contact_phone: Mapped[str] = mapped_column(String(100), default="")
    pin: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    generator_on: Mapped[bool] = mapped_column(Boolean, default=False)
    pump_on: Mapped[bool] = mapped_column(Boolean, default=False)
    sewer_ok: Mapped[bool] = mapped_column(Boolean, default=True)
    map_x: Mapped[int] = mapped_column(Integer, default=50)
    map_y: Mapped[int] = mapped_column(Integer, default=50)
    bladders: Mapped[list["Bladder"]] = relationship(back_populates="site", cascade="all, delete-orphan")

class Bladder(Base):
    __tablename__ = "bladders"
    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    fill: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="standby")
    disposal_method: Mapped[str | None] = mapped_column(String(100), nullable=True)
    disposal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    disposed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    site: Mapped[Site] = relationship(back_populates="bladders")

class Transfer(Base):
    __tablename__ = "transfers"
    id: Mapped[int] = mapped_column(primary_key=True)
    from_site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), nullable=False)
    to_site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class VacuumVendor(Base):
    __tablename__ = "vacuum_vendors"
    id: Mapped[int] = mapped_column(primary_key=True)
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[str] = mapped_column(String(200), nullable=False)
    response_time: Mapped[str] = mapped_column(String(100), nullable=False)
    contracted: Mapped[bool] = mapped_column(Boolean, default=False)
    available: Mapped[bool] = mapped_column(Boolean, default=True)

class ManualSection(Base):
    __tablename__ = "manual_sections"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    icon: Mapped[str] = mapped_column(String(20), default="")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(200), default="")
    diagram_note: Mapped[str] = mapped_column(String(250), default="")
    steps: Mapped[list["ManualStep"]] = relationship(back_populates="section", cascade="all, delete-orphan", order_by="ManualStep.step_no")

class ManualStep(Base):
    __tablename__ = "manual_steps"
    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("manual_sections.id", ondelete="CASCADE"))
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[ManualSection] = relationship(back_populates="steps")
