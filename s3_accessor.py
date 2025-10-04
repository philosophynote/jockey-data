import os
import boto3
from io import BytesIO


class S3Accessor:
    def __init__(self):
        self.ssm_client = boto3.client("ssm", region_name=os.environ.get("AWS_REGION"))
        self.aws_access_key_id = self.get_parameter("ACCESS_KEY")
        self.aws_secret_access_key = self.get_parameter("SECRET_ACCESS_KEY")
        self.region_name = self.get_parameter("REGION_NAME")
        self.bucket_name = self.get_parameter("BUCKET_NAME")
        self.client = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
        )

    def get_parameter(self, name):
        response = self.ssm_client.get_parameter(Name=name, WithDecryption=True)
        return response["Parameter"]["Value"]

    def list_objects(self, prefix, delimiter="/"):
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

        except Exception as e:
            print(f"Error listing objects: {e}")

        return objects

    def get_object(self, key):
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read()
        except Exception as e:
            print(f"Error getting object: {e}")
            return None

    def get_paginator(self, operation_name, prefix=None):
        """
        S3操作の結果をまとめて取得します。

        Args:
            operation_name (str): ページネーションするS3操作名（例: 'list_objects_v2'）。
            prefix (str, optional): キーをフィルタリングするプレフィックス。

        Returns:
            list: ページネーションされた結果のリスト。
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
        except Exception as e:
            print(f"Error in get_paginator: {e}")

        return paginated_objects

    def upload_file(self, local_path, key):
        try:
            self.client.upload_file(local_path, self.bucket_name, key)
        except Exception as e:
            print(f"Error uploading file: {e}")

    def upload_fileobj(self, file_obj, key):
        """
        指定されたファイルオブジェクトをS3バケットにアップロードします。

        Args:
            file_obj (file-like object): アップロードするファイルオブジェクト。
            key (str): S3バケット内のオブジェクトキー。
        """
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, key)
        except Exception as e:
            print(f"Error uploading file object: {e}")

    def put_object(self, body, key):
        """
        指定されたデータをS3バケットにオブジェクトとして保存します。

        Args:
            body (bytes or str): S3にアップロードするデータ。
            key (str): S3バケット内のオブジェクトキー。
        """
        try:
            self.client.put_object(Body=body, Bucket=self.bucket_name, Key=key)
        except Exception as e:
            print(f"Error putting object: {e}")

    def upload_dataframe(self, df, key: str):
        try:
            buffer = BytesIO()
            df.to_pickle(buffer)
            buffer.seek(0)
            self.upload_fileobj(buffer, key)
            print(f"{key}にアップロードしました")
        except Exception as e:
            print(f"S3へのアップロード中にエラーが発生しました: {e}")
