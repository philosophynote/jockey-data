"""
S3Accessor Unit Tests

S3Accessorの基本機能をモックを使用してテストします。
"""

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.infrastructure.s3_accessor import S3Accessor
from app.models.exceptions import S3AccessError


class TestS3Accessor:
    """S3Accessorのテストクラス"""

    @patch("app.infrastructure.s3_accessor.boto3")
    def test_init_success(self, mock_boto3):
        """正常な初期化のテスト"""
        # SSMクライアントのモック
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = lambda Name, WithDecryption: {
            "Parameter": {"Value": f"mock_{Name}"}
        }

        # S3クライアントのモック
        mock_s3 = MagicMock()

        # boto3.clientのモック
        def client_factory(service_name, **kwargs):
            if service_name == "ssm":
                return mock_ssm
            elif service_name == "s3":
                return mock_s3

        mock_boto3.client.side_effect = client_factory

        # S3Accessorの初期化
        accessor = S3Accessor()

        # アサーション
        assert accessor.bucket_name == "mock_BUCKET_NAME"
        assert accessor.region_name == "mock_REGION_NAME"
        assert accessor.client == mock_s3

    @patch("app.infrastructure.s3_accessor.boto3")
    def test_get_object_success(self, mock_boto3):
        """S3からのオブジェクト取得成功のテスト"""
        # モックの設定
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = lambda Name, WithDecryption: {
            "Parameter": {"Value": f"mock_{Name}"}
        }

        mock_s3 = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = b"test_data"
        mock_s3.get_object.return_value = {"Body": mock_body}

        def client_factory(service_name, **kwargs):
            if service_name == "ssm":
                return mock_ssm
            elif service_name == "s3":
                return mock_s3

        mock_boto3.client.side_effect = client_factory

        # S3Accessorの初期化とテスト
        accessor = S3Accessor()
        result = accessor.get_object("test.pickle")

        # アサーション
        assert result == b"test_data"
        mock_s3.get_object.assert_called_once_with(
            Bucket="mock_BUCKET_NAME",
            Key="test.pickle"
        )

    @patch("app.infrastructure.s3_accessor.boto3")
    def test_get_object_not_found(self, mock_boto3):
        """S3からのオブジェクトが存在しない場合のテスト"""
        # モックの設定
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = lambda Name, WithDecryption: {
            "Parameter": {"Value": f"mock_{Name}"}
        }

        mock_s3 = MagicMock()
        # NoSuchKeyエラーをシミュレート
        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_s3.get_object.side_effect = ClientError(error_response, "GetObject")

        def client_factory(service_name, **kwargs):
            if service_name == "ssm":
                return mock_ssm
            elif service_name == "s3":
                return mock_s3

        mock_boto3.client.side_effect = client_factory

        # S3Accessorの初期化とテスト
        accessor = S3Accessor()
        result = accessor.get_object("nonexistent.pickle")

        # アサーション（NoSuchKeyの場合はNoneを返す）
        assert result is None

    @patch("app.infrastructure.s3_accessor.boto3")
    def test_get_object_s3_error(self, mock_boto3):
        """S3アクセスエラーのテスト"""
        # モックの設定
        mock_ssm = MagicMock()
        mock_ssm.get_parameter.side_effect = lambda Name, WithDecryption: {
            "Parameter": {"Value": f"mock_{Name}"}
        }

        mock_s3 = MagicMock()
        # その他のS3エラーをシミュレート
        error_response = {"Error": {"Code": "AccessDenied"}}
        mock_s3.get_object.side_effect = ClientError(error_response, "GetObject")

        def client_factory(service_name, **kwargs):
            if service_name == "ssm":
                return mock_ssm
            elif service_name == "s3":
                return mock_s3

        mock_boto3.client.side_effect = client_factory

        # S3Accessorの初期化とテスト
        accessor = S3Accessor()

        # アサーション（S3AccessErrorが発生することを確認）
        with pytest.raises(S3AccessError):
            accessor.get_object("test.pickle")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
