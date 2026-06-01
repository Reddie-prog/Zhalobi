from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20))
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="user", foreign_keys="Complaint.user_id")
    notifications = relationship("Notification", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    auto_escalation_hours = Column(Integer, default=72)
    icon = Column(String(10), default="🏠")

    complaints = relationship("Complaint", back_populates="category")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    address = Column(String(500), nullable=False)
    contact_phone = Column(String(20), nullable=True)
    lat = Column(String(20), nullable=True)
    lng = Column(String(20), nullable=True)
    status = Column(String(50), default="new")
    priority = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    escalated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", back_populates="complaints", foreign_keys=[user_id])
    category = relationship("Category", back_populates="complaints")
    events = relationship("ComplaintEvent", back_populates="complaint", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="complaint")
    assigned_user = relationship("User", foreign_keys=[assigned_to])


class ComplaintEvent(Base):
    __tablename__ = "complaint_events"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    comment = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="events")
    creator = relationship("User", foreign_keys=[created_by])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    notification_type = Column(String(50), default="info")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    complaint = relationship("Complaint", back_populates="notifications")
