from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_current_user
from app.cards.schema import CardResponse, CardCreate, CardUpdate
from app.cards.service import CardService
from app.db.database import get_db
from app.db.models import User


router_card = APIRouter(tags=["cards"])


@router_card.post("/columns/{column_id}/cards",response_model=CardResponse,)
async def create_card(column_id: UUID,data: CardCreate,db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await CardService.create_card(db=db,column_public_id=column_id,user=user,data=data)

@router_card.get("/columns/{column_id}/cards",response_model=list[CardResponse])
async def get_cards(column_id: UUID,db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user)):
    return await CardService.get_cards(db=db,column_public_id=column_id,user=user,)

@router_card.patch("/cards/{card_id}",response_model=CardResponse)
async def update_card(card_id: UUID,data: CardUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    return await CardService.update_card(db=db, card_public_id=card_id, user=user, data=data)

@router_card.delete("/cards/{card_id}",status_code=204)
async def delete_card(card_id: UUID,db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user)):
    await CardService.delete_card(db=db,card_public_id=card_id,user=user)