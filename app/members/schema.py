from uuid import UUID

from pydantic import BaseModel

from app.db.models.board_member import BoardRole


class AddBoardMemberRequest(BaseModel):
    username: str
    role: BoardRole = BoardRole.VIEWER


class BoardMemberResponse(BaseModel):
    username: str
    role: BoardRole


class BoardOwnerResponse(BaseModel):
    username: str


class BoardMembersResponse(BaseModel):
    owner: BoardOwnerResponse
    members: list[BoardMemberResponse]


class UpdateMemberRoleRequest(BaseModel):
    role: BoardRole