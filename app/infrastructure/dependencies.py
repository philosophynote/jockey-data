"""
Dependency Injection - グローバルな依存関係の管理

Lambda Web Adapterのコールドスタート最適化のため、
S3Accessorをグローバルスコープで初期化します。
"""

import os
from typing import Optional

from app.core.logging import get_logger
from app.infrastructure.s3_accessor import S3Accessor
from app.models.exceptions import SSMConfigError

logger = get_logger(__name__)

# グローバルなS3Accessorインスタンス
_s3_accessor: Optional[S3Accessor] = None


def get_s3_accessor() -> S3Accessor:
    """
    S3Accessorのシングルトンインスタンスを取得

    Lambda環境では、グローバルスコープで初期化することで
    コンテナの再利用時にSSM Parameter Storeへのアクセスを回避します。

    Returns:
        S3Accessorインスタンス

    Raises:
        SSMConfigError: 初期化に失敗した場合
    """
    global _s3_accessor

    if _s3_accessor is None:
        logger.info("Initializing S3Accessor (first time)")
        try:
            _s3_accessor = S3Accessor()
            logger.info("S3Accessor initialized successfully")
        except SSMConfigError as e:
            logger.error(f"Failed to initialize S3Accessor: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing S3Accessor: {e}")
            raise SSMConfigError("S3Accessor", e)
    else:
        logger.debug("Reusing existing S3Accessor instance")

    return _s3_accessor


def reset_s3_accessor() -> None:
    """
    S3Accessorインスタンスをリセット（主にテスト用）
    """
    global _s3_accessor
    _s3_accessor = None
    logger.info("S3Accessor instance reset")
