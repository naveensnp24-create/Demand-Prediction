"""DemandPredict FastAPI application."""

import json
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.database import init_db
from backend.app.api import upload, forecast, predict, segments, insights, health, catalog


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(
    title="DemandPredict API",
    version="1.0.0",
    lifespan=lifespan,
    description="Demand forecasts, behavioral customer segmentation, purchase propensity and inventory planning.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=json.loads(
        os.getenv("CORS_ORIGINS", '["http://localhost:5173", "http://127.0.0.1:5173"]')
    ),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
for module in [health, upload, forecast, predict, segments, insights, catalog]:
    app.include_router(module.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "DemandPredict API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
