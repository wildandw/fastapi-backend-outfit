from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_current_user
from models.schemas import TryOnRequest, TryOnResponse
from services.tryon_service import TryOnService

router = APIRouter()
tryon_service = TryOnService()


# ── SKPL-F-013, F-014, F-015 ──
@router.post("/", response_model=TryOnResponse)
async def virtual_try_on(
    request: TryOnRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-013: Memilih outfit hasil rekomendasi untuk divisualisasikan
    SKPL-F-014: Menampilkan hasil visualisasi virtual try-on
    SKPL-F-015: Menyimpan hasil visualisasi virtual try-on

    Alur proses:
    1. Mengekstrak person_image_url, top_item_id, bottom_item_id
    2. Mengambil image_url dari Firebase untuk top dan bottom item
    3. Mengunduh gambar menggunakan requests.get(url).content
    4. Resize menggunakan image.thumbnail((768, 768))
    5. Encode ke Base64 menggunakan base64.b64encode().decode('utf-8')
    6. Kirim ke OOTDiffusion untuk inferensi Tops
    7. Decode hasil dan simpan sebagai intermediate image
    8. Kirim ke OOTDiffusion untuk inferensi Bottoms
    9. Upload hasil ke Cloudinary
    10. Simpan metadata ke Firebase
    11. Kembalikan response JSON
    """
    result = tryon_service.process_tryon(
        user_id=current_user["uid"],
        person_image_url=request.person_image_url,
        top_item_id=request.top_item_id,
        bottom_item_id=request.bottom_item_id
    )
    return result


# ── SKPL-F-015 (ambil riwayat) ──
@router.get("/history")
async def get_tryon_history(
    current_user: dict = Depends(get_current_user)
):
    """
    SKPL-F-015: Mengambil riwayat hasil virtual try-on
    dari Firebase Realtime Database menggunakan
    db.reference('tryon/{uid}').get()
    """
    history = tryon_service.get_history(current_user["uid"])
    return {"history": history}


# ── SKPL-F-015 (hapus hasil) ──
@router.delete("/{tryon_id}")
async def delete_tryon_result(
    tryon_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Menghapus hasil virtual try-on dari Firebase
    dan Cloudinary berdasarkan tryon_id
    """
    success = tryon_service.delete_result(current_user["uid"], tryon_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Hasil virtual try-on tidak ditemukan"
        )
    return {"message": "Hasil virtual try-on berhasil dihapus"}
