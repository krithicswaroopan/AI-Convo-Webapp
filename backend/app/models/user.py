"""User management data models."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """Base user model with common fields."""
    
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    is_active: bool = Field(default=True, description="Whether user account is active")


class UserCreate(UserBase):
    """Model for creating a new user."""
    
    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """Model for updating user information."""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, min_length=8, description="New password")
    is_active: Optional[bool] = Field(None, description="Whether user account is active")


class User(UserBase):
    """Complete user model."""
    
    id: str = Field(..., description="Unique user ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """User response model (excludes sensitive data)."""
    
    id: str = Field(..., description="Unique user ID")
    email: EmailStr = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation time")
    last_login: Optional[datetime] = Field(None, description="Last login time")


class UserLogin(BaseModel):
    """Model for user login."""
    
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Authentication token model."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token payload data."""
    
    user_id: Optional[str] = Field(None, description="User ID from token")
    email: Optional[str] = Field(None, description="User email from token") 