from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DBSession
from app.modules.boards.schema import BoardBaseResponse, BoardCreate, BoardFullResponse, BoardResponse, BoardUpdate
from app.modules.boards.service import BoardService
from app.modules.cards.schema import BoardLayoutUpdate

router_board = APIRouter(prefix="/boards", tags=["boards"])


@router_board.post("", response_model=BoardBaseResponse)
async def create_board(data: BoardCreate, db: DBSession, user: CurrentUser):
    return await BoardService.create_board(db=db, user=user, data=data)


@router_board.get("/{board_id}", response_model=BoardFullResponse)
async def get_board(board_id: UUID, db: DBSession, user: CurrentUser):
    return await BoardService.get_board(db=db, public_id=board_id, user=user)


@router_board.get("", response_model=list[BoardResponse])
async def get_boards(db: DBSession, user: CurrentUser):
    return await BoardService.get_accessible_boards(db=db, user=user)


@router_board.patch("/{board_id}", response_model=BoardBaseResponse)
async def update_board(board_id: UUID, data: BoardUpdate, db: DBSession, user: CurrentUser):
    return await BoardService.update_board(db=db, public_id=board_id, user=user, data=data)


@router_board.delete("/{board_id}")
async def delete_board(board_id: UUID, db: DBSession, user: CurrentUser):
    return await BoardService.delete_board(db=db, public_id=board_id, user=user)


@router_board.patch("/{board_id}/layout")
async def update_layout(board_id: UUID, data: BoardLayoutUpdate, db: DBSession, user: CurrentUser):
    return await BoardService.update_layout(db=db, board_public_id=board_id, user=user, data=data)
