from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    wardrobe,
    recommendation,
    tryon,
    favorites,
    auth,
    register
)

app = FastAPI(
    title="Smart Outfit Recommendation API",
    description="Backend API untuk aplikasi Smart Rekomendasi Outfit Harian",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, tags=["Auth"])
app.include_router(register.router, tags=["Register"])
app.include_router(wardrobe.router, prefix="/wardrobe", tags=["Wardrobe"])
app.include_router(recommendation.router, prefix="/recommendation", tags=["Recommendation"])
app.include_router(tryon.router, prefix="/tryon", tags=["Virtual Try-On"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])

@app.get("/")
def root():
    return {"message": "Smart Outfit Recommendation API is running"}
