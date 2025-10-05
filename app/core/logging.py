"""
Logging Configuration

構造化ログとログレベルの設定を提供
"""

import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """
    構造化ログフォーマッター（JSON形式）

    CloudWatch Logsで解析しやすい形式でログを出力
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        ログレコードを構造化形式（JSON風）で出力

        Args:
            record: ログレコード

        Returns:
            フォーマット済みログメッセージ
        """
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 追加のフィールド（extra）を含める
        if hasattr(record, "jockey_id"):
            log_data["jockey_id"] = record.jockey_id
        if hasattr(record, "bucket"):
            log_data["bucket"] = record.bucket
        if hasattr(record, "key"):
            log_data["key"] = record.key
        if hasattr(record, "error"):
            log_data["error"] = record.error

        # 例外情報を含める
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return str(log_data)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    アプリケーションのログ設定を初期化

    Args:
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）

    Returns:
        設定済みのルートロガー
    """
    # ルートロガーの取得
    logger = logging.getLogger()

    # 既存のハンドラーをクリア
    logger.handlers.clear()

    # ログレベルの設定
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # コンソールハンドラーの作成
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logger.level)

    # フォーマッターの設定
    formatter = StructuredFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    # ハンドラーをロガーに追加
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    名前付きロガーを取得

    Args:
        name: ロガー名（通常は __name__ を使用）

    Returns:
        ロガーインスタンス
    """
    return logging.getLogger(name)
