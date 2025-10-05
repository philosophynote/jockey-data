"""
FastAPI Application Entry Point

騎手データをS3から取得してJSON形式で返却するREST APIサーバー
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.logging import setup_logging, get_logger

# ロギングの初期化
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)
logger = get_logger(__name__)

logger.info("Starting Jockey Data API application")

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Jockey Data API",
    description="騎手IDに基づいてS3からpickleファイルを取得し、JSON形式で返却するAPI",
    version="0.1.0",
)

# CORSミドルウェアの設定(全オリジンを許可)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では特定のオリジンに制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
async def health_check():
    """
    ヘルスチェックエンドポイント

    Returns:
        dict: ステータス情報
    """
    return JSONResponse(
        status_code=200, content={"status": "healthy", "service": "jockey-data-api"}
    )


@app.get("/", tags=["root"])
async def root():
    """
    ルートエンドポイント

    Returns:
        dict: API情報
    """
    return {
        "message": "Jockey Data API",
        "version": "0.1.0",
        "docs": "/docs",
    }
