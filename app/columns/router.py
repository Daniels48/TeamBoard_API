from uuid import UUID

from fastapi import APIRouter

from app.columns.schema import BoardColumnResponse, BoardColumnCreate, BoardColumnUpdate
from app.columns.service import BoardColumnService
from app.core.dependencies import CurrentUser, DBSession


router_board_column = APIRouter(tags=["board_columns"])


@router_board_column.post("/boards/{board_id}/columns",response_model=BoardColumnResponse)
async def create_column(board_id: UUID, data: BoardColumnCreate, db: DBSession, user: CurrentUser):
    return await BoardColumnService.create_column(db=db, board_public_id=board_id, user=user, data=data)

@router_board_column.get("/boards/{board_id}/columns",response_model=list[BoardColumnResponse])
async def get_columns(board_id: UUID, db: DBSession, user: CurrentUser):
    return await BoardColumnService.get_columns(db=db,board_public_id=board_id,user=user)

@router_board_column.patch("/boards/{board_id}/columns/{column_id}",response_model=BoardColumnResponse)
async def update_column(board_id: UUID, column_id: UUID, data: BoardColumnUpdate, db: DBSession, user: CurrentUser):
    return await BoardColumnService.update_column(db=db,board_public_id=board_id,column_public_id=column_id,user=user,data=data)

@router_board_column.delete("/boards/{board_id}/columns/{column_id}")
async def delete_column(board_id: UUID,column_id: UUID, db: DBSession, user: CurrentUser):
    await BoardColumnService.delete_column(db=db,board_public_id=board_id,column_public_id=column_id,user=user)
    return {"message": "Column deleted"}