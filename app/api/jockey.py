"""
Jockey API Router - 騎手データ取得エンドポイント

騎手IDに基づいてレースデータを取得するAPIエンドポイントを提供します。
"""

from typing import Any, List

from fastapi import APIRouter, Path

from app.core.logging import get_logger
from app.services.jockey_service import JockeyService

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["jockey"])


@router.get("/jockey/{jockey_id}", response_model=List[dict[str, Any]])
async def get_jockey_data(
    jockey_id: str = Path(..., description="騎手ID（例: 05339）")
) -> List[dict[str, Any]]:
    """
    騎手IDに基づいてレースデータを取得

    Args:
        jockey_id: 騎手ID

    Returns:
        レースデータのJSONリスト

    Raises:
        HTTPException: データ取得エラー時
            - 404: 騎手データが見つからない場合
            - 500: S3接続エラーまたはデータ処理エラー
            - 503: SSM設定取得エラー
    """
    logger.info("API request received", extra={"jockey_id": jockey_id})

    service = JockeyService()
    result = service.get_jockey_data(jockey_id)

    logger.info(
        "API request completed",
        extra={"jockey_id": jockey_id, "record_count": len(result)}
    )
    return result
