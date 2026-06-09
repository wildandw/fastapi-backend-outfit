from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_current_user
from models.schemas import RecommendationRequest, RecommendationResponse
from services.recommendation_service import RecommendationService

router = APIRouter()
recommendation_service = RecommendationService()


@router.get(
    "/{item_id}",
    response_model=RecommendationResponse
)
async def get_outfit_recommendation(
    item_id: str,
    current_user: dict = Depends(get_current_user)
):

    result = recommendation_service.get_recommendations(
        user_id=current_user["uid"],
        item_id=item_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Item pakaian tidak ditemukan"
        )

    return result
