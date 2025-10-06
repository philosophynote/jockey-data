"""
Jockey Service - 騎手データ取得のビジネスロジック

S3から騎手のpickleデータを取得し、JSON形式に変換します。
"""

import pickle
from typing import Any, List

import pandas as pd

from app.core.logging import get_logger
from app.infrastructure.dependencies import get_s3_accessor
from app.models.exceptions import JockeyNotFoundError, PickleDeserializeError, S3AccessError

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

    def deserialize_pickle(self, pickle_data: bytes, jockey_id: str) -> pd.DataFrame:
        """
        pickleバイナリデータをpandas DataFrameにデシリアライズ

        Args:
            pickle_data: pickleバイナリデータ
            jockey_id: 騎手ID（エラーログ用）

        Returns:
            pandas DataFrame

        Raises:
            PickleDeserializeError: デシリアライズに失敗した場合
        """
        try:
            logger.debug(
                "Deserializing pickle data",
                extra={"jockey_id": jockey_id, "data_size": len(pickle_data)}
            )
            df = pickle.loads(pickle_data)

            if not isinstance(df, pd.DataFrame):
                raise PickleDeserializeError(
                    jockey_id,
                    Exception(f"Expected DataFrame, got {type(df)}")
                )

            logger.info(
                "Successfully deserialized pickle data",
                extra={"jockey_id": jockey_id, "rows": len(df), "columns": len(df.columns)}
            )
            return df

        except Exception as e:
            logger.error(
                "Failed to deserialize pickle data",
                extra={"jockey_id": jockey_id, "error": str(e)}
            )
            raise PickleDeserializeError(jockey_id, e) from e

    def dataframe_to_json(self, df: pd.DataFrame, jockey_id: str) -> List[dict[str, Any]]:
        """
        pandas DataFrameをJSON形式のリストに変換

        日付フィールドはISO 8601形式の文字列に変換されます。

        Args:
            df: pandas DataFrame
            jockey_id: 騎手ID（エラーログ用）

        Returns:
            JSON形式のレコードリスト

        Raises:
            PickleDeserializeError: JSON変換に失敗した場合
        """
        try:
            logger.debug(
                "Converting DataFrame to JSON",
                extra={"jockey_id": jockey_id, "rows": len(df)}
            )

            # 日付列をISO 8601形式に変換
            df_copy = df.copy()
            for col in df_copy.columns:
                if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].dt.strftime("%Y-%m-%dT%H:%M:%S")

            # orient='records'でJSON形式に変換
            result: List[dict[str, Any]] = df_copy.to_dict(orient="records")

            logger.info(
                "Successfully converted DataFrame to JSON",
                extra={"jockey_id": jockey_id, "record_count": len(result)}
            )
            return result

        except Exception as e:
            logger.error(
                "Failed to convert DataFrame to JSON",
                extra={"jockey_id": jockey_id, "error": str(e)}
            )
            raise PickleDeserializeError(jockey_id, e) from e

    def get_jockey_data(self, jockey_id: str) -> List[dict[str, Any]]:
        """
        騎手IDに基づいてS3からデータを取得し、JSON形式で返却

        S3からpickleファイルを取得 → デシリアライズ → JSON変換の
        完全なフローを実行します。

        Args:
            jockey_id: 騎手ID

        Returns:
            JSON形式のレースデータリスト

        Raises:
            JockeyNotFoundError: 指定された騎手IDのデータが見つからない場合
            S3AccessError: S3接続エラーが発生した場合
            PickleDeserializeError: デシリアライズまたはJSON変換に失敗した場合
        """
        logger.info("Starting jockey data retrieval", extra={"jockey_id": jockey_id})

        # S3からバイナリデータを取得
        binary_data = self.get_jockey_data_binary(jockey_id)

        # pickleデシリアライズ
        df = self.deserialize_pickle(binary_data, jockey_id)

        # JSON変換
        json_data = self.dataframe_to_json(df, jockey_id)

        logger.info(
            "Completed jockey data retrieval",
            extra={"jockey_id": jockey_id, "record_count": len(json_data)}
        )
        return json_data
