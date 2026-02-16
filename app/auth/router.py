from app.auth.schemas import RegisterRequest
from app.schemas.user import UserRead


@router.post("/register", response_model=UserRead)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await AuthService.register_user(db, data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
