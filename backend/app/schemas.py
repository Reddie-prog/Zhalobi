from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str]
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon: str
    auto_escalation_hours: int

    class Config:
        from_attributes = True


class ComplaintCreate(BaseModel):
    category_id: int
    title: str
    description: str
    address: str
    priority: str = "medium"


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    comment: Optional[str] = None


class ComplaintEventResponse(BaseModel):
    id: int
    event_type: str
    old_status: Optional[str]
    new_status: Optional[str]
    comment: Optional[str]
    created_at: datetime
    creator: Optional[UserResponse]

    class Config:
        from_attributes = True


class ComplaintResponse(BaseModel):
    """Used for list views — no events to avoid lazy-load issues."""
    id: int
    ticket_number: str
    title: str
    description: str
    address: str
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime
    escalated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    user: UserResponse
    category: CategoryResponse

    class Config:
        from_attributes = True


class ComplaintDetailResponse(ComplaintResponse):
    """Used for single-complaint views — includes event timeline."""
    events: List[ComplaintEventResponse] = []


class NotificationResponse(BaseModel):
    id: int
    message: str
    is_read: bool
    notification_type: str
    created_at: datetime
    complaint_id: Optional[int]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_complaints: int
    new_complaints: int
    in_progress_complaints: int
    escalated_complaints: int
    resolved_complaints: int
    closed_complaints: int
    auto_processed_count: int
    resolution_rate: float
