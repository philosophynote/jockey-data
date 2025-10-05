"""
Jockey Service - 騎手データ取得のビジネスロジック

S3から騎手のpickleデータを取得し、JSON形式に変換します。
"""

from app.core.logging import get_logger
from app.infrastructure.dependencies import get_s3_accessor
from app.models.exceptions import JockeyNotFoundError, S3AccessError

logger = get_logger(__name__)


class JockeyService:
    """騎手データ取得サービス"""

    def __init__(self):
        """
        JockeyServiceの初期化

        S3Accessorのシングルトンインスタンスを取得します。
        """
        self.s3_accessor = get_s3_accessor()

    def _generate_s3_key(self, jockey_id: str) -> str:
        """
        騎手IDからS3オブジェクトキーを生成

        Args:
            jockey_id: 騎手ID（例: "05339"）

        Returns:
            S3オブジェクトキー（例: "05339.pickle"）
        """
        return f"{jockey_id}.pickle"

    def get_jockey_data_binary(self, jockey_id: str) -> bytes:
        """
        騎手IDに基づいてS3からバイナリデータを取得

        Args:
            jockey_id: 騎手ID

        Returns:
            S3から取得したpickleファイルのバイナリデータ

        Raises:
            JockeyNotFoundError: 指定された騎手IDのデータが見つからない場合
            S3AccessError: S3接続エラーが発生した場合
        """
        s3_key = self._generate_s3_key(jockey_id)

        logger.info(
            "Fetching jockey data from S3",
            extra={"jockey_id": jockey_id, "s3_key": s3_key}
        )

        try:
            data = self.s3_accessor.get_object(s3_key)

            if data is None:
                logger.warning(
                    "Jockey data not found",
                    extra={"jockey_id": jockey_id, "s3_key": s3_key}
                )
                raise JockeyNotFoundError(jockey_id)

            result: bytes = data
            logger.info(
                "Successfully retrieved jockey data",
                extra={"jockey_id": jockey_id, "data_size": len(result)}
            )
            return result

        except S3AccessError as e:
            logger.error(
                "S3 access error while fetching jockey data",
                extra={
                    "jockey_id": jockey_id,
                    "s3_key": s3_key,
                    "error": str(e)
                }
            )
            raise
