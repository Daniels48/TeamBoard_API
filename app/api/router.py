from fastapi import APIRouter

from app.modules.auth.router import auth_router
from app.modules.boards.router import router_board
from app.modules.cards.router import router_card
from app.modules.columns.router import router_board_column
from app.modules.members.router import router_board_members
from app.modules.users.router import router_users

api_router = APIRouter()


api_router.include_router(auth_router)
api_router.include_router(router_users)
api_router.include_router(router_board)
api_router.include_router(router_board_column)
api_router.include_router(router_card)
api_router.include_router(router_board_members)
