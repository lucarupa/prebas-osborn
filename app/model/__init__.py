
import enum

from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, UniqueConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base

class TypeAgency(str, enum.Enum):
    agency = "agency"
    freelancer = "freelancer"

class AssetStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    archived = "archived"


def _uuid():
    return str(uuid4())

class Agency(Base):
    __tablename__ = "agencies"

    id          = Column(String(36), primary_key=True, default=_uuid)
    name        = Column(String(255), nullable=False)
    agency_type = Column(Enum(TypeAgency), default=TypeAgency.agency)  # 'agency' | 'freelancer'
    created_at  = Column(DateTime, server_default=func.now(), nullable=False)

    projects = relationship("Project", back_populates="agency", cascade="all, delete-orphan")
    users    = relationship("User", back_populates="agency", cascade="all, delete-orphan")
    assets   = relationship("Asset", back_populates="agency", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id          = Column(String(36), primary_key=True, default=_uuid)
    name        = Column(String(255), nullable=False)
    description = Column(Text)
    agency_id   = Column(String(36), ForeignKey("agencies.id"), nullable=False)
    status      = Column(String(50), default="active")
    created_at  = Column(DateTime, server_default=func.now(), nullable=False)

    agency = relationship("Agency", back_populates="projects")
    assets = relationship("Asset", back_populates="project", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id         = Column(String(36), primary_key=True, default=_uuid)
    name       = Column(String(255), nullable=False)
    email      = Column(String(255), nullable=False, unique=True)
    role       = Column(String(50), nullable=False)  # 'designer' | 'reviewer' | 'client' | 'admin'
    agency_id  = Column(String(36), ForeignKey("agencies.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    agency           = relationship("Agency", back_populates="users")
    assets_created   = relationship("Asset", back_populates="creator", cascade="all, delete-orphan")
    versions_created = relationship("AssetVersion", back_populates="creator", cascade="all, delete-orphan")
    approvals_given  = relationship("Approval", back_populates="reviewer", cascade="all, delete-orphan")
    comments         = relationship("Comment", back_populates="author", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id              = Column(String(36), primary_key=True, default=_uuid)
    title           = Column(String(255), nullable=False)
    description     = Column(Text)
    asset_type      = Column(String(50), nullable=False)  # 'image' | 'video' | 'pdf'
    project_id      = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    agency_id       = Column(String(36), ForeignKey("agencies.id"), nullable=False, index=True)
    created_by      = Column(String(36), ForeignKey("users.id"), nullable=False)
    status          = Column(Enum(AssetStatus), default=AssetStatus.pending_review)
    current_version = Column(Integer, default=1)
    created_at      = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    project  = relationship("Project", back_populates="assets")
    agency   = relationship("Agency", back_populates="assets")
    creator  = relationship("User", back_populates="assets_created")
    versions = relationship("AssetVersion", back_populates="asset", order_by="AssetVersion.version_number", cascade="all, delete-orphan")


class AssetVersion(Base):
    __tablename__ = "asset_versions"

    id              = Column(String(36), primary_key=True, default=_uuid)
    asset_id        = Column(String(36), ForeignKey("assets.id"), nullable=False, index=True)
    version_number  = Column(Integer, nullable=False)
    file_url        = Column(String(500), nullable=False)
    file_name       = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer)
    notes           = Column(Text)
    created_by      = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at      = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("asset_id", "version_number", name="uq_asset_version"),
    )

    asset     = relationship("Asset", back_populates="versions")
    creator   = relationship("User", back_populates="versions_created")
    approvals = relationship("Approval", back_populates="asset_version", cascade="all, delete-orphan")
    comments  = relationship("Comment", back_populates="asset_version", cascade="all, delete-orphan")


class Approval(Base):
    __tablename__ = "approvals"

    id               = Column(String(36), primary_key=True, default=_uuid)
    asset_version_id = Column(String(36), ForeignKey("asset_versions.id"), nullable=False, index=True)
    reviewed_by      = Column(String(36), ForeignKey("users.id"), nullable=False)
    decision         = Column(String(50), nullable=False)  # 'approved' | 'rejected'
    comment          = Column(Text)
    created_at       = Column(DateTime, server_default=func.now(), nullable=False)

    asset_version = relationship("AssetVersion", back_populates="approvals")
    reviewer      = relationship("User", back_populates="approvals_given")


class Comment(Base):
    __tablename__ = "comments"

    id               = Column(String(36), primary_key=True, default=_uuid)
    asset_version_id = Column(String(36), ForeignKey("asset_versions.id"), nullable=False, index=True)
    author_id        = Column(String(36), ForeignKey("users.id"), nullable=False)
    body             = Column(Text, nullable=False)
    created_at       = Column(DateTime, server_default=func.now(), nullable=False)

    asset_version = relationship("AssetVersion", back_populates="comments")
    author        = relationship("User", back_populates="comments")
