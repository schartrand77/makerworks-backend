# app/middleware/cors.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

def setup_cors(app: FastAPI) -> None:
    # Load from env if set, fallback to defaults
    raw_origins = os.getenv("CORS_ORIGINS")
    if raw_origins:
        allowed_origins = [origin.strip() for origin in raw_origins.split(",")]
    else:
        allowed_origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://192.168.1.191:5173",
        ]

    # 🚨 Fail fast if required dev origin is not present
    required_origin = "http://192.168.1.191:5173"
    if required_origin not in allowed_origins:
        raise RuntimeError(f"🚨 CORS misconfiguration: {required_origin} is missing from allowed_origins")

    logging.info("✅ Setting up CORS middleware with the following origins:")
    for origin in allowed_origins:
        logging.info(f"   • {origin}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )