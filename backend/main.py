import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.routers import asteroids

load_dotenv()

app = FastAPI(
    title="AsteroidWatch API",
    description="Collision Risk Engine and NASA Near-Earth Object Telemetry API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asteroids.router)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AsteroidWatch Collision Risk Engine",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
