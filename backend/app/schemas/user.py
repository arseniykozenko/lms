from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator, field_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    second_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.STUDENT

    @model_validator(mode="after")
    def validate_names(self):
        local_part = str(self.email).split("@", maxsplit=1)[0].strip() if self.email else ""
        self.first_name = (self.first_name or local_part or "User").strip()
        self.second_name = (self.second_name or "").strip()
        if not self.first_name:
            self.first_name = "User"
        return self

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: UserRole) -> UserRole:
        if value == UserRole.ADMIN:
            raise ValueError("Admin role cannot be assigned during public registration")
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str | None = None
    second_name: str | None = None
    email: EmailStr
    profile_photo_url: str | None = None
    role: UserRole
    is_active: bool
    blocked_until: datetime | None = None
    blocked_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    second_name: str | None = Field(default=None, min_length=1, max_length=120)
    profile_photo_url: str | None = Field(default=None, max_length=500)


class AdminUserListItem(UserRead):
    pass


class AdminUserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserBlockUpdate(BaseModel):
    blocked_until: datetime | None = None
    blocked_reason: str | None = Field(default=None, max_length=2000)


class TeacherLookupItem(BaseModel):
    id: UUID
    first_name: str | None = None
    second_name: str | None = None
    email: EmailStr
    role: UserRole
