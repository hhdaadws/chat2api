from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from db.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tokens = relationship("Token", back_populates="owner", cascade="all, delete-orphan")


class Token(Base):
    """ChatGPT tokens storage"""
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # None means global token
    token_value = Column(Text, nullable=False, unique=True)
    token_type = Column(String(20), default="access")  # access or refresh
    is_error = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    account_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="tokens")


class Config(Base):
    """Configuration storage - replaces environment variables"""
    __tablename__ = "configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    config_type = Column(String(20), default="string")  # string, int, bool, json
    category = Column(String(50), nullable=True)  # security, request, functionality, gateway
    is_secret = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RefreshMap(Base):
    """Refresh token mapping"""
    __tablename__ = "refresh_maps"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(500), unique=True, index=True, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SeedMap(Base):
    """Seed token mapping for gateway mode"""
    __tablename__ = "seed_maps"

    id = Column(Integer, primary_key=True, index=True)
    seed_token = Column(String(100), unique=True, index=True, nullable=False)
    access_token = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConversationMap(Base):
    """Conversation mapping for gateway mode"""
    __tablename__ = "conversation_maps"

    id = Column(Integer, primary_key=True, index=True)
    seed_token = Column(String(100), index=True, nullable=False)
    conversation_id = Column(String(100), nullable=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FPMap(Base):
    """Browser fingerprint mapping"""
    __tablename__ = "fp_maps"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    fingerprint_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WSSMap(Base):
    """WebSocket mapping"""
    __tablename__ = "wss_maps"

    id = Column(Integer, primary_key=True, index=True)
    access_token = Column(String(500), unique=True, index=True, nullable=False)
    wss_url = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
