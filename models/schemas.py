from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FavoriteType(str, Enum):
    tryon = "tryon"
    outfit = "outfit"
    
# ── AUTH / USER MODELS ──

class UserProfileRequest(BaseModel):
    """Schema request untuk menyimpan profil user"""
    username: str
    email: str

# ── WARDROBE MODELS ──

class ClothingItemCreate(BaseModel):
    """Schema untuk membuat item pakaian baru"""
    name: str
    category: str           # Tops / Bottoms
    color: str              # Warna dominan
    style: str              # Casual / Formal / Sporty / dll
    activities: str         # Hangout / Work / Sport / dll
    pattern: str            # Solid / Stripe / Floral / dll

class ClothingItemUpdate(BaseModel):
    """Schema untuk mengubah metadata pakaian"""
    name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    style: Optional[str] = None
    activities: Optional[str] = None
    pattern: Optional[str] = None

class ClothingItemResponse(BaseModel):
    """Schema response untuk item pakaian"""
    id: str
    name: str
    category: str
    color: str
    style: str
    activities: str
    pattern: str
    imageUrl: str
    createdAt: str

class DetectedAttributes(BaseModel):
    """Schema untuk hasil deteksi atribut otomatis"""
    color: str
    category: str
    style: str
    activities: str
    pattern: str
    confidence: float

# ── RECOMMENDATION MODELS ──

class RecommendationRequest(BaseModel):
    """Schema request untuk rekomendasi outfit"""
    item_id: str

class ScoreDetail(BaseModel):
    """Schema rincian skor rule-based"""
    color_score: float      # maks 45 poin
    pattern_score: float    # maks 25 poin
    occasion_score: float   # maks 30 poin
    style_score: float      # maks 15 poin
    total_score: float
    normalized_score: float # skala 0-100

class RecommendationResultItem(BaseModel):
    """Schema satu hasil rekomendasi"""
    item: ClothingItemResponse
    score_detail: ScoreDetail
    reason: str

class RecommendationResponse(BaseModel):
    """Schema response top 3 rekomendasi"""
    selected_item: ClothingItemResponse
    recommendations: List[RecommendationResultItem]
    total_candidates: int

# ── VIRTUAL TRY-ON MODELS ──

# class TryOnRequest(BaseModel):
#     """Schema request virtual try-on"""
#     person_image_url: str
#     top_item_id: str
#     bottom_item_id: str

class TryOnResponse(BaseModel):
    """Schema response hasil virtual try-on"""
    tryon_id: str
    result_image_url: str
    top_item_id: str
    bottom_item_id: str
    processing_time_seconds: float
    created_at: str


# ── FAVORITES MODELS ──

class FavoriteRequest(BaseModel):
    """Schema request untuk menyimpan favorit"""
    favorite_type: FavoriteType     # 'tryon' atau 'outfit'
    reference_id: str               # tryon_id atau recommendation_id
    image_url: str                  # URL gambar yang akan disimpan ke Cloudinary
    top_item_id: str                # ID atasan
    bottom_item_id: str             # ID bawahan
    note: Optional[str] = None      # Catatan opsional dari pengguna

class FavoriteResponse(BaseModel):
    """Schema response untuk item favorit"""
    favorite_id: str
    type: str
    reference_id: str
    image_url: str
    public_id: Optional[str] = None
    top_item_id: str
    bottom_item_id: str
    note: Optional[str] = None
    created_at: str