from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/api/goals", tags=["Goals"])

@router.post("",
             response_model=GoalResponse,
             status_code = status.HTTP_201_CREATED,
             )
async def create_goal(
        data:GoalCreate,
        db: AsyncSession = Depends(get_database),
):
    goal = Goal(**data.model_dump())
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal

@router.get("",response_model=list[GoalResponse])
async def get_goals(
        skip: int = Query(default=0, ge=0),
        limit: int  = Query(default=20, ge=1, le=100),
        db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(Goal)
        .order_by(Goal.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.get("/{goal_id}",response_model=GoalResponse)
async def get_goal(
        goal_id: int,
        db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="目标不存在")

    return goal

@router.patch("/{goal_id}",response_model=GoalResponse)
async def update_goal(
        goal_id: int,
        data: GoalUpdate,
        db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if goal is None:
        raise HTTPException(status_code=404,detail="目标不存在")

    update_goal = data.model_dump(exclude_unset=True)

    for field, value in update_goal.items():
        setattr(goal, field, value)

    await db.commit()
    await db.refresh(goal)
    return goal

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
        goal_id:int,
        db: AsyncSession = Depends(get_database),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if goal is None:
        raise HTTPException(status_code = 404, detail="目标不存在")

    await db.delete(goal)
    await db.commit()