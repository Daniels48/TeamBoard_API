from enum import StrEnum


class BoardPermission(StrEnum):
    VIEW = "view"
    EDIT = "edit"
    MANAGE_MEMBERS = "manage_members"
