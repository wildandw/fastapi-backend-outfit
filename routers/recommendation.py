from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_current_user
from models.schemas import RecommendationRequest, RecommendationResponse
from services.recommendation_service import RecommendationService

router = APIRouter()
recommendation_service = RecommendationService()


# ── SKPL-F-011, F-012, F-013 ──
@router.post("/outfit", response_model=RecommendationResponse)
async def get_outfit_recommendation(
    request: RecommendationRequest,
    current_user: dict = Depends(get_current_user)
):
    """

    Alur proses:
    1. Mengambil item yang dipilih dari Firebase
    2. Menentukan kategori lawan (tops/bottoms)
    3. Mengambil semua kandidat dari Firebase
    4. Menghitung skor setiap pasangan menggunakan calculate_score()
    5. Menormalisasi skor: normalized = round((total / 115) * 100, 2)
    6. Mengurutkan menggunakan sorted(scores, key=lambda x: x["score"], reverse=True)
    7. Mengambil top_3 = sorted_scores[:3]
    8. Menyusun alasan pencocokan menggunakan generate_reason()
    """
    # Validasi item_id
    if not request.item_id:
        raise HTTPException(
            status_code=400,
            detail="item_id tidak boleh kosong"
        )

    result = recommendation_service.get_recommendations(
        user_id=current_user["uid"],
        item_id=request.item_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Item pakaian tidak ditemukan di lemari digital"
        )

    return result
