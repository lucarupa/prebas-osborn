from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared / base schemas
# ---------------------------------------------------------------------------

class AgencyOut(BaseModel):
    id: str
    name: str
    type: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    agency_id: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    agency_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Asset schemas
# ---------------------------------------------------------------------------

class AssetOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    asset_type: str
    project_id: str
    agency_id: str
    created_by: str
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetVersionOut(BaseModel):
    id: str
    asset_id: str
    version_number: int
    file_url: str
    file_name: str
    file_size_bytes: Optional[int] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalOut(BaseModel):
    id: str
    asset_version_id: str
    reviewed_by: str
    decision: str
    comment: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CommentOut(BaseModel):
    id: str
    asset_version_id: str
    author_id: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

ALLOWED_ASSET_TYPES = {"image", "video", "pdf"}


class CreateAssetRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: str = Field(..., description="image | video | pdf")
    project_id: str = Field(..., min_length=1)
    agency_id: str = Field(..., min_length=1)
    created_by: str = Field(..., min_length=1)
    file_url: str = Field(..., min_length=1, max_length=500)
    file_name: str = Field(..., min_length=1, max_length=255)
    file_size_bytes: Optional[int] = Field(None, ge=0)
    version_notes: Optional[str] = None

    @field_validator("asset_type")
    @classmethod
    def validate_asset_type(cls, v: str) -> str:
        if v not in ALLOWED_ASSET_TYPES:
            raise ValueError(f"asset_type must be one of {sorted(ALLOWED_ASSET_TYPES)}")
        return v


# ---------------------------------------------------------------------------
# Response envelopes
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: List[Any] = []


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


class CreateAssetData(BaseModel):
    asset: AssetOut
    version: AssetVersionOut


class CreateAssetResponse(BaseModel):
    success: bool = True
    data: CreateAssetData


class AssetDetailData(BaseModel):
    asset: AssetOut
    versions: List[AssetVersionOut]
    approvals: List[ApprovalOut]


class GetAssetResponse(BaseModel):
    success: bool = True
    data: AssetDetailData
