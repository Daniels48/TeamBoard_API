from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.boards.schema import BoardResponse, BoardCreate, BoardFullResponse
from app.boards.service import BoardService
from app.cards.schema import BoardLayoutUpdate
from app.db.database import get_db
from app.db.models import User


router_board = APIRouter(prefix="/boards", tags=["boards"])

@router_board.get("/{board_id}",response_model=BoardResponse)
async def get_board(board_id: UUID,db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await BoardService.get_board(db=db, public_id=board_id, user=user)


@router_board.post("",response_model=BoardResponse,)
async def create_board(data: BoardCreate,db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user)):
    return await BoardService.create_board(db=db, user=user, data=data)


@router_board.get("",response_model=list[BoardResponse])
async def get_available_boards(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    return await BoardService.get_available_boards(db=db, user=user)

@router_board.get("/{board_id}/full",response_model=BoardFullResponse)
async def get_board_full(board_id: UUID,db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await BoardService.get_full_board(db=db, public_id=board_id, user=user)

@router_board.patch("/{board_id}/layout")
async def update_layout(
    board_id: UUID,
    data: BoardLayoutUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return await BoardService.update_layout(db=db, board_public_id=board_id, user=user, data=data)

