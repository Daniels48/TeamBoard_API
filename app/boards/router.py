from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.auth.dependencies import verify_session, get_current_user
from app.auth.sсhemas import SessionCacheData
from app.boards.schema import BoardResponse, BoardCreate
from app.boards.service import BoardService
from app.cards.schema import BoardLayoutUpdate
from app.core.redis_service import SessionCache
from app.db.database import get_db
from app.db.models import User

router_board = APIRouter(prefix="/boards", tags=["boards"])


@router_board.get("/check", response_model=SessionCacheData)
async def get_user_data(payload = Depends(verify_session)):
    session = await SessionCache.get(payload.sid_str)
    return SessionCacheData.model_validate_json(session)


@router_board.post("",response_model=BoardResponse,)
async def create_board(
    data: BoardCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await BoardService.create_board(
        db=db,
        user=user,
        data=data,
    )


@router_board.get("",response_model=list[BoardResponse])
async def get_boards(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    return await BoardService.get_my_boards(db=db,user=user,)


@router_board.get("/{board_id}",response_model=BoardResponse)
async def get_board(
    board_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await BoardService.get_board(
        db=db,
        public_id=board_id,
        user=user,
    )

@router_board.patch("/{board_id}/layout")
async def update_layout(
    board_id: UUID,
    data: BoardLayoutUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await BoardService.update_layout(
        db=db,
        board_public_id=board_id,
        user=user,
        data=data,
    )

