from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    Integer,
    DateTime,
    func,
    Enum as SAEnum, Boolean, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import  Mapped, mapped_column, relationship

from app.core.database.models.Base import Base


class Role(str, PyEnum):
    ADMIN = "ADMIN"
    RH = "RH"
    PROJECT_MANAGER = "PROJECT_MANAGER"

class PendingUsersStatus(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DECLINED  = "DECLINED"

class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        index=True
    )
    username: Mapped[str] = mapped_column(String(50), unique=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password: Mapped[str] = mapped_column(Text)
    role: Mapped[Role] = mapped_column(SAEnum(Role), default=Role.ADMIN)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Relationships
    projects: Mapped[List["UserProject"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

class PendingUser(Base):
    __tablename__ = "pending_users"
    
    id:Mapped[UUID] = mapped_column(primary_key=True, default=uuid4, index=True)
    email:Mapped[str] = mapped_column(String(255), unique=True, index=True)
    user:Mapped[dict[str, Any]] = mapped_column(JSONB)
    status:Mapped[PendingUsersStatus] = mapped_column(SAEnum(PendingUsersStatus), default=PendingUsersStatus.PENDING)
    created_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    approved_at:Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    identifier: Mapped[Optional[str]] = mapped_column(Text, unique=False, nullable=True)
    created_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_on: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    members: Mapped[List["Member"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    user_projects: Mapped[List["UserProject"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class UserProject(Base):
    """Many-to-many between users and projects + role in project"""
    __tablename__ = "user_project"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="projects")
    project: Mapped["Project"] = relationship(back_populates="user_projects")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column("dep_id", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("dep_name", String(100), nullable=False)

    employees: Mapped[List["Employee"]] = relationship(
        back_populates="department"
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column("emp_id", primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column("emp_full_name", String(150), nullable=False)
    email: Mapped[str] = mapped_column("emp_email", String(255), unique=True, nullable=False)
    hire_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    department_id: Mapped[Optional[int]] = mapped_column(
        "dep_id", ForeignKey("departments.dep_id"), nullable=True
    )

    department: Mapped[Optional["Department"]] = relationship(back_populates="employees")

    attendances: Mapped[List["Attendance"]] = relationship(
        back_populates="employee"
    )
    attendance_events: Mapped[List["EmployeeAttendanceEvent"]] = relationship(
        back_populates="employee"
    )
    members: Mapped[List["Member"]] = relationship(
        back_populates="employee"
    )


class Member(Base):
    """Which employees are assigned to which projects"""
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    emp_id: Mapped[int] = mapped_column(ForeignKey("employees.emp_id", ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))

    employee: Mapped["Employee"] = relationship(back_populates="members")
    project: Mapped["Project"] = relationship(back_populates="members")


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    attendance_records: Mapped[List["EmployeeAttendanceEvent"]] = relationship(
        back_populates="event"
    )


class EmployeeAttendanceEvent(Base):
    """Link between employee + attendance event (leave, mission, training, etc.)"""
    __tablename__ = "employee_attendance_event"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    emp_id: Mapped[int] = mapped_column(ForeignKey("employees.emp_id", ondelete="CASCADE"))
    event_id: Mapped[int] = mapped_column(ForeignKey("attendance_events.id", ondelete="RESTRICT"))

    apply_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    employee: Mapped["Employee"] = relationship(back_populates="attendance_events")
    event: Mapped["AttendanceEvent"] = relationship(back_populates="attendance_records")


class Attendance(Base):
    """Daily attendance record (check-in / check-out)"""
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, unique=True)
    emp_id: Mapped[int] = mapped_column(ForeignKey("employees.emp_id", ondelete="CASCADE"))
    check_in: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    att_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    week_day: Mapped[int] = mapped_column(Integer)  # 0 = Monday, 6 = Sunday

    employee: Mapped["Employee"] = relationship(back_populates="attendances")