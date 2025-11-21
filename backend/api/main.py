from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import assets

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
app.include_router(assets.router, prefix="/api/assets", tags=["assets"])

@app.get("/")
async def root():
    return {"message": "Portfolio Management API is running"}
