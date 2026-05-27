from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_current_user
from models.schemas import FavoriteRequest, FavoriteResponse
from services.favorites_service import FavoritesService

router = APIRouter()
favorites_service = FavoritesService()


# ── SIMPAN FAVORIT ──
@router.post("/", response_model=FavoriteResponse)
async def add_favorite(
    request: FavoriteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Menyimpan hasil virtual try-on atau pasangan outfit rekomendasi
    ke favorit pengguna. Foto disimpan ke Cloudinary dan metadata
    disimpan ke Firebase Realtime Database menggunakan
    db.reference('users/{uid}/favorites/{favorite_id}').set()
    """
    result = favorites_service.add_favorite(
        user_id=current_user["uid"],
        request=request
    )
    return result


# ── AMBIL SEMUA FAVORIT ──
@router.get("/", response_model=list)
async def get_favorites(
    current_user: dict = Depends(get_current_user)
):
    """
    Mengambil seluruh daftar favorit pengguna dari
    Firebase Realtime Database menggunakan
    db.reference('users/{uid}/favorites').get()
    """
    favorites = favorites_service.get_all_favorites(current_user["uid"])
    return favorites


# ── AMBIL SATU FAVORIT ──
@router.get("/{favorite_id}", response_model=FavoriteResponse)
async def get_favorite(
    favorite_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Mengambil satu item favorit berdasarkan favorite_id
    dari Firebase Realtime Database menggunakan
    db.reference('users/{uid}/favorites/{favorite_id}').get()
    """
    favorite = favorites_service.get_favorite_by_id(
        current_user["uid"], favorite_id
    )
    if not favorite:
        raise HTTPException(
            status_code=404,
            detail="Item favorit tidak ditemukan"
        )
    return favorite


# ── HAPUS FAVORIT ──
@router.delete("/{favorite_id}")
async def delete_favorite(
    favorite_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Menghapus item favorit dari Firebase Realtime Database
    menggunakan db.reference('users/{uid}/favorites/{favorite_id}').delete()
    dan menghapus foto dari Cloudinary menggunakan
    cloudinary.uploader.destroy(public_id)
    """
    success = favorites_service.delete_favorite(
        current_user["uid"], favorite_id
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Item favorit tidak ditemukan"
        )
    return {"message": "Item favorit berhasil dihapus"}


# ── CEK APAKAH SUDAH DIFAVORITKAN ──
@router.get("/check/{reference_id}")
async def check_favorite(
    reference_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Memeriksa apakah suatu hasil try-on atau outfit rekomendasi
    sudah disimpan ke favorit berdasarkan reference_id
    """
    is_favorite = favorites_service.is_favorited(
        current_user["uid"], reference_id
    )
    return {"is_favorite": is_favorite}
