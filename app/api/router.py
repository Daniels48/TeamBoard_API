from fastapi import APIRouter

from app.auth.router import auth_router
from app.boards.router import router_board
from app.columns.router import router_board_column
from app.cards.router import router_card
from app.members.router import router_board_members
from app.users.router import router_users


api_router = APIRouter()


api_router.include_router(auth_router)
api_router.include_router(router_users)
api_router.include_router(router_board)
api_router.include_router(router_board_column)
api_router.include_router(router_card)
api_router.include_router(router_board_members)