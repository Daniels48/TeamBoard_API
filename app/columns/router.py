from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.columns.schema import BoardColumnResponse, BoardColumnCreate
from app.columns.service import BoardColumnService
from app.db.database import get_db
from app.db.models import User


router_board_column = APIRouter(tags=["board_columns"])


@router_board_column.post("/boards/{board_id}/columns",response_model=BoardColumnResponse)
async def create_column(board_id: UUID,data: BoardColumnCreate,db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user)):
    return await BoardColumnService.create_column(db=db, board_public_id=board_id, user=user, data=data)

@router_board_column.get("/boards/{board_id}/columns",response_model=list[BoardColumnResponse])
async def get_columns(board_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    return await BoardColumnService.get_columns(db=db,board_public_id=board_id,user=user)