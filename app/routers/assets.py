from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.deps import get_db
from app.model import Agency, Project, User, Asset, AssetVersion, Approval
from app.schemas import (
    CreateAssetRequest, CreateAssetResponse, CreateAssetData,
    AssetOut, AssetVersionOut,
    GetAssetResponse, AssetDetailData, ApprovalOut,
    CreateVersionRequest, CreateVersionResponse, CreateVersionData,
)

router = APIRouter(prefix="/assets", tags=["assets"])


# ---------------------------------------------------------------------------
# POST /assets — create asset + first version
# ---------------------------------------------------------------------------

@router.post("", status_code=201)
async def create_asset(payload: CreateAssetRequest, db: AsyncSession = Depends(get_db)):
    # Validate agency exists
    agency = await db.get(Agency, payload.agency_id)
    if not agency:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Agency with id '{payload.agency_id}' not found.",
                "details": [],
            },
        )

    # Validate project exists
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Project with id '{payload.project_id}' not found.",
                "details": [],
            },
        )
    # Validate user exists
    user = await db.get(User, payload.created_by)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"User with id '{payload.created_by}' not found.",
                "details": [],
            },
        )

    # Validate project belongs to the given agency
    if project.agency_id != payload.agency_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "The project does not belong to the specified agency.",
                "details": [],
            },
        )

    # Create asset
    asset = Asset(
        title=payload.title,
        description=payload.description,
        asset_type=payload.asset_type,
        project_id=payload.project_id,
        agency_id=payload.agency_id,
        created_by=payload.created_by,
        status="pending_review",
        current_version=1,
    )
    db.add(asset)
    await db.flush()  # get asset.id before creating version

    # Create first version
    version = AssetVersion(
        asset_id=asset.id,
        version_number=1,
        file_url=payload.file_url,
        file_name=payload.file_name,
        file_size_bytes=payload.file_size_bytes,
        notes=payload.version_notes,
        created_by=payload.created_by,
    )
    db.add(version)
    await db.commit()
    await db.refresh(asset)
    await db.refresh(version)

    return CreateAssetResponse(
        data=CreateAssetData(
            asset=AssetOut.model_validate(asset),
            version=AssetVersionOut.model_validate(version),
        )
    )

# ---------------------------------------------------------------------------
# POST /assets/{asset_id}/versions — upload a new version (CU-02)
# ---------------------------------------------------------------------------

@router.post("/{asset_id}/versions", status_code=201, response_model=CreateVersionResponse)
async def create_version(asset_id: str, payload: CreateVersionRequest, db: AsyncSession = Depends(get_db)):
    # Validate asset exists
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Asset with id '{asset_id}' not found.",
                "details": [],
            },
        )

    # Validate asset is in an editable state
    if asset.status not in ("pending_review", "rejected"):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "INVALID_STATE",
                "message": f"Cannot add a version to an asset with status '{asset.status}'. "
                           "Asset must be in 'pending_review' or 'rejected'.",
                "details": [],
            },
        )

    # Validate user exists and has designer role
    user = await db.get(User, payload.created_by)
    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"User with id '{payload.created_by}' not found.",
                "details": [],
            },
        )
    if user.role != "designer":
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FORBIDDEN",
                "message": "Only users with role 'designer' can upload new versions.",
                "details": [],
            },
        )

    # Calculate next version number
    result = await db.execute(
        select(func.max(AssetVersion.version_number)).where(AssetVersion.asset_id == asset_id)
    )
    max_version = result.scalar() or 0
    next_version = max_version + 1

    # Create new version
    version = AssetVersion(
        asset_id=asset_id,
        version_number=next_version,
        file_url=payload.file_url,
        file_name=payload.file_name,
        file_size_bytes=payload.file_size_bytes,
        notes=payload.notes,
        created_by=payload.created_by,
    )
    db.add(version)

    # Update asset: bump current_version, reset status to pending_review
    asset.current_version = next_version
    asset.status = "pending_review"

    await db.commit()
    await db.refresh(asset)
    await db.refresh(version)

    return CreateVersionResponse(
        data=CreateVersionData(
            asset=AssetOut.model_validate(asset),
            version=AssetVersionOut.model_validate(version),
        )
    )


# ---------------------------------------------------------------------------
# GET /assets/{id} — retrieve asset with versions and approvals
# ---------------------------------------------------------------------------

@router.get("/{asset_id}", response_model=GetAssetResponse, status_code=200)
async def get_asset(asset_id: str, db: AsyncSession = Depends(get_db)):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "NOT_FOUND",
                "message": f"Asset with id '{asset_id}' not found.",
                "details": [],
            },
        )

    versions_result = await db.execute(
        select(AssetVersion).where(AssetVersion.asset_id == asset_id).order_by(AssetVersion.version_number)
    )

    versions = versions_result.scalars().all()

    approvals = []
    if versions:
        versions_id = [v.id for v in versions]
        approvals_result = await db.execute(
            select(Approval).where(Approval.asset_version_id.in_(versions_id)).order_by(Approval.created_at)
        )
        approvals = approvals_result.scalars().all()

    return GetAssetResponse(
        data=AssetDetailData(
            asset=AssetOut.model_validate(asset),
            versions=[AssetVersionOut.model_validate(v) for v in versions],
            approvals=[ApprovalOut.model_validate(a) for a in approvals],
        )
    )