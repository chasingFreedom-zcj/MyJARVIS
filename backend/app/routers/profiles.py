from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database
from app.models.profile import UserProfile
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
)

router = APIRouter(prefix="/profiles", tags=["个人档案"])


@router.post(
    "",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    profile_data: ProfileCreate,
    db: AsyncSession = Depends(get_database),
):
    profile = UserProfile(**profile_data.model_dump())

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return profile


@router.get("", response_model=list[ProfileResponse])
async def get_profiles(
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(UserProfile).order_by(UserProfile.id)
    )
    return result.scalars().all()


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人档案不存在",
        )

    return profile


@router.patch("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人档案不存在",
        )

    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    return profile


@router.delete("/{profile_id}")
async def delete_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="个人档案不存在",
        )

    await db.delete(profile)
    await db.commit()

    return {"message": "个人档案删除成功"}
