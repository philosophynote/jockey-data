"""
S3Accessor - AWS S3とSSM Parameter Storeへのアクセスを提供

既存のs3_accessor.pyを改良し、ログ機能と例外処理を強化したバージョン
"""

import os
from io import BytesIO
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.logging import get_logger
from app.models.exceptions import S3AccessError, SSMConfigError

logger = get_logger(__name__)


class S3Accessor:
    """
    AWS S3とSSM Parameter Storeへのアクセスを提供するクラス

    SSM Parameter Storeから認証情報を取得し、S3クライアントを初期化します。
    """

    def __init__(self):
        """
        S3Accessorの初期化

        環境変数AWS_REGIONを使用してSSMクライアントを作成し、
        必要な認証情報をSSM Parameter Storeから取得します。

        Raises:
            SSMConfigError: SSM Parameter Store認証情報の取得に失敗した場合
        """
        try:
            aws_region = os.environ.get("AWS_REGION", "ap-northeast-1")
            logger.info(f"Initializing S3Accessor with region: {aws_region}")

            self.ssm_client = boto3.client("ssm", region_name=aws_region)

            # SSM Parameter Storeから認証情報を取得
            self.aws_access_key_id = self.get_parameter("ACCESS_KEY")
            self.aws_secret_access_key = self.get_parameter("SECRET_ACCESS_KEY")
            self.region_name = self.get_parameter("REGION_NAME")
            self.bucket_name = self.get_parameter("BUCKET_NAME")

            # S3クライアントの初期化
            self.client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name,
            )

            logger.info(
                "S3Accessor initialized successfully",
                extra={"bucket": self.bucket_name, "region": self.region_name}
            )

        except Exception as e:
            logger.error(f"Failed to initialize S3Accessor: {e}")
            raise SSMConfigError("S3Accessor initialization", e)

    def get_parameter(self, name: str) -> str:
        """
        SSM Parameter Storeからパラメータを取得

        Args:
            name: パラメータ名

        Returns:
            パラメータ値

        Raises:
            SSMConfigError: パラメータ取得に失敗した場合
        """
        try:
            response = self.ssm_client.get_parameter(Name=name, WithDecryption=True)
            logger.debug(f"Retrieved SSM parameter: {name}")
            return response["Parameter"]["Value"]
        except ClientError as e:
            logger.error(
                "Failed to get SSM parameter",
                extra={"parameter": name, "error": str(e)}
            )
            raise SSMConfigError(name, e)
        except Exception as e:
            logger.error(f"Unexpected error getting SSM parameter: {e}")
            raise SSMConfigError(name, e)

    def get_object(self, key: str) -> Optional[bytes]:
        """
        S3からオブジェクトを取得

        Args:
            key: S3オブジェクトキー

        Returns:
            バイナリデータ（取得失敗時はNone）

        Raises:
            S3AccessError: S3接続エラーが発生した場合
        """
        try:
            logger.info("Fetching object from S3", extra={"bucket": self.bucket_name, "key": key})
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            data = response["Body"].read()
            logger.info("Successfully fetched object", extra={"bucket": self.bucket_name, "key": key, "size": len(data)})
            return data

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")

            if error_code == "NoSuchKey":
                # ファイルが存在しない場合はNoneを返す（404相当）
                logger.warning(
                    "Object not found in S3",
                    extra={"bucket": self.bucket_name, "key": key}
                )
                return None
            else:
                # その他のS3エラーは例外として送出
                logger.error(
                    "S3 access error",
                    extra={
                        "bucket": self.bucket_name,
                        "key": key,
                        "error_code": error_code,
                        "error": str(e)
                    }
                )
                raise S3AccessError(
                    f"Failed to get object from S3: {error_code}",
                    bucket=self.bucket_name,
                    key=key
                )

        except NoCredentialsError as e:
            logger.error(f"AWS credentials not found: {e}")
            raise S3AccessError("AWS credentials not found", bucket=self.bucket_name, key=key)

        except Exception as e:
            logger.error(
                "Unexpected error getting object from S3",
                extra={"bucket": self.bucket_name, "key": key, "error": str(e)}
            )
            raise S3AccessError(
                f"Unexpected error: {str(e)}",
                bucket=self.bucket_name,
                key=key
            )

    def list_objects(self, prefix: str, delimiter: str = "/") -> List[Dict[str, Any]]:
        """
        S3バケット内のオブジェクトをリスト表示

        Args:
            prefix: オブジェクトキーのプレフィックス
            delimiter: 区切り文字（デフォルト: "/"）

        Returns:
            オブジェクトのリスト
        """
        objects = []
        continuation_token = None

        try:
            while True:
                list_kwargs = {
                    "Bucket": self.bucket_name,
                    "Prefix": prefix,
                    "Delimiter": delimiter,
                }
                if continuation_token:
                    list_kwargs["ContinuationToken"] = continuation_token

                response = self.client.list_objects_v2(**list_kwargs)

                if "Contents" in response:
                    objects.extend(response["Contents"])

                if not response.get("IsTruncated"):
                    break

                continuation_token = response.get("NextContinuationToken")

            logger.info(
                "Listed objects in S3",
                extra={"bucket": self.bucket_name, "prefix": prefix, "count": len(objects)}
            )
            return objects

        except Exception as e:
            logger.error(
                "Error listing objects",
                extra={"bucket": self.bucket_name, "prefix": prefix, "error": str(e)}
            )
            return []

    def get_paginator(self, operation_name: str, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        S3操作の結果をページネーションして取得

        Args:
            operation_name: ページネーションするS3操作名（例: 'list_objects_v2'）
            prefix: キーをフィルタリングするプレフィックス（オプション）

        Returns:
            ページネーションされた結果のリスト
        """
        paginator = self.client.get_paginator(operation_name)
        paginated_objects = []

        try:
            pagination_config = {"Bucket": self.bucket_name}
            if prefix:
                pagination_config["Prefix"] = prefix

            for page in paginator.paginate(**pagination_config):
                if "Contents" in page:
                    paginated_objects.extend(page["Contents"])

            logger.info(f"Paginated {len(paginated_objects)} objects from S3")
            return paginated_objects

        except Exception as e:
            logger.error(f"Error in get_paginator: {e}")
            return []

    def upload_file(self, local_path: str, key: str) -> None:
        """
        ローカルファイルをS3にアップロード

        Args:
            local_path: ローカルファイルパス
            key: S3オブジェクトキー
        """
        try:
            self.client.upload_file(local_path, self.bucket_name, key)
            logger.info("Uploaded file to S3", extra={"bucket": self.bucket_name, "key": key})
        except Exception as e:
            logger.error(f"Error uploading file: {e}")

    def upload_fileobj(self, file_obj: BytesIO, key: str) -> None:
        """
        ファイルオブジェクトをS3にアップロード

        Args:
            file_obj: アップロードするファイルオブジェクト
            key: S3バケット内のオブジェクトキー
        """
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, key)
            logger.info("Uploaded file object to S3", extra={"bucket": self.bucket_name, "key": key})
        except Exception as e:
            logger.error(f"Error uploading file object: {e}")

    def put_object(self, body: bytes, key: str) -> None:
        """
        データをS3バケットにオブジェクトとして保存

        Args:
            body: S3にアップロードするデータ
            key: S3バケット内のオブジェクトキー
        """
        try:
            self.client.put_object(Body=body, Bucket=self.bucket_name, Key=key)
            logger.info("Put object to S3", extra={"bucket": self.bucket_name, "key": key})
        except Exception as e:
            logger.error(f"Error putting object: {e}")

    def upload_dataframe(self, df, key: str) -> None:
        """
        pandas DataFrameをpickle形式でS3にアップロード

        Args:
            df: pandas DataFrame
            key: S3バケット内のオブジェクトキー
        """
        try:
            buffer = BytesIO()
            df.to_pickle(buffer)
            buffer.seek(0)
            self.upload_fileobj(buffer, key)
            logger.info("Uploaded DataFrame to S3", extra={"bucket": self.bucket_name, "key": key})
        except Exception as e:
            logger.error(f"Error uploading DataFrame: {e}")
