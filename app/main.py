from fastapi import FastAPI
from sqlalchemy import text
from app.database.database import engine

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the E-commerce Backend API!"}

@app.get("/health")
async def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected", 
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    