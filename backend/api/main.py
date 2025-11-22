from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(dotenv_path="backend/.env")

from backend.api.routers import assets
from backend.api.dependencies import get_current_user

app = FastAPI(
    title="Portfolio Management API",
    description="API for the Portfolio Management System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assets.router, prefix="/api", tags=["assets"])

@app.get("/")
async def root():
    return {"message": "Portfolio Management API is running"}

@app.get("/api/me")
async def read_users_me(user = Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email}
