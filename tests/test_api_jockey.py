"""
Jockey API Endpoint Tests

FastAPIのTestClientを使用してAPIエンドポイントをテストします。
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.exceptions import S3AccessError, SSMConfigError

client = TestClient(app)


class TestJockeyAPI:
    """Jockey APIのテストクラス"""

    @pytest.fixture
    def real_pickle_data(self):
        """実際のpickleファイルを読み込むフィクスチャ"""
        pickle_path = os.path.join(os.path.dirname(__file__), "test_data.pickle")
        with open(pickle_path, "rb") as f:
            return f.read()

    def test_health_check(self):
        """ヘルスチェックエンドポイントのテスト"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self):
        """ルートエンドポイントのテスト"""
        response = client.get("/")
        assert response.status_code == 200
        assert "message" in response.json()

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_success(self, mock_get_s3_accessor, real_pickle_data):
        """騎手データ取得成功のテスト"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = real_pickle_data
        mock_get_s3_accessor.return_value = mock_s3_accessor

        response = client.get("/api/jockey/05339")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert isinstance(data[0], dict)

        # 日付フィールドがISO 8601形式になっていることを確認
        if "日付" in data[0]:
            assert isinstance(data[0]["日付"], str)
            assert "T" in data[0]["日付"]

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_not_found(self, mock_get_s3_accessor):
        """騎手データが見つからない場合のテスト（404レスポンス）"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = None
        mock_get_s3_accessor.return_value = mock_s3_accessor

        response = client.get("/api/jockey/99999")

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Not Found"
        assert "99999" in data["message"]
        assert data["jockey_id"] == "99999"

        # 内部エラー詳細が含まれていないことを確認
        assert "S3" not in data["message"]
        assert "pickle" not in data["message"].lower()

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_s3_error(self, mock_get_s3_accessor):
        """S3接続エラーのテスト（500レスポンス）"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.side_effect = S3AccessError(
            "S3 connection failed",
            bucket="test-bucket",
            key="05339.pickle"
        )
        mock_get_s3_accessor.return_value = mock_s3_accessor

        response = client.get("/api/jockey/05339")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal Server Error"
        assert "S3" in data["message"]

        # 内部エラー詳細（バケット名、キー名）が含まれていないことを確認
        assert "test-bucket" not in data["message"]
        assert "05339.pickle" not in data["message"]

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_pickle_error(self, mock_get_s3_accessor):
        """pickleデシリアライズエラーのテスト（500レスポンス）"""
        mock_s3_accessor = MagicMock()
        # 破損したpickleデータを返す
        mock_s3_accessor.get_object.return_value = b"corrupted pickle data"
        mock_get_s3_accessor.return_value = mock_s3_accessor

        response = client.get("/api/jockey/05339")

        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal Server Error"
        assert "process" in data["message"].lower() or "jockey data" in data["message"].lower()

        # 内部エラー詳細が含まれていないことを確認
        assert "pickle" not in data["message"].lower()
        assert "deserialize" not in data["message"].lower()

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_ssm_config_error(self, mock_get_s3_accessor):
        """SSM設定エラーのテスト（503レスポンス）"""
        mock_get_s3_accessor.side_effect = SSMConfigError("BUCKET_NAME", Exception("Permission denied"))

        response = client.get("/api/jockey/05339")

        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "Service Unavailable"
        assert "configuration" in data["message"].lower() or "support" in data["message"].lower()

        # 内部エラー詳細（パラメータ名）が含まれていないことを確認
        assert "BUCKET_NAME" not in data["message"]

    def test_openapi_schema(self):
        """OpenAPIスキーマが生成されることを確認"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "paths" in schema
        assert "/api/jockey/{jockey_id}" in schema["paths"]

    def test_api_documentation(self):
        """API自動ドキュメントにアクセスできることを確認"""
        response = client.get("/docs")
        assert response.status_code == 200
