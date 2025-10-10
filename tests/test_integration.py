"""
Integration Tests

エンドツーエンドフローと統合テストを実施します。
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.exceptions import S3AccessError, SSMConfigError

client = TestClient(app)


class TestIntegration:
    """統合テストクラス"""

    @pytest.fixture
    def real_pickle_data(self):
        """実際のpickleファイルを読み込むフィクスチャ"""
        pickle_path = os.path.join(os.path.dirname(__file__), "test_data.pickle")
        with open(pickle_path, "rb") as f:
            return f.read()

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_end_to_end_flow_with_real_pickle(
        self, mock_get_s3_accessor, real_pickle_data
    ):
        """
        エンドツーエンドフロー: API→サービス→S3Accessor→pickle変換→JSON
        実際のpickleファイルを使用してJSON変換の整合性を検証
        """
        # モックS3 Accessorの設定
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = real_pickle_data
        mock_get_s3_accessor.return_value = mock_s3_accessor

        # APIリクエストを実行
        response = client.get("/api/jockey/05339")

        # レスポンスの検証
        assert response.status_code == 200
        data = response.json()

        # データ構造の検証
        assert isinstance(data, list)
        assert len(data) > 0
        assert isinstance(data[0], dict)

        # 日付フィールドがISO 8601形式になっていることを確認
        if "日付" in data[0]:
            assert isinstance(data[0]["日付"], str)
            # ISO 8601形式の検証（YYYY-MM-DDTHH:MM:SS形式）
            assert "T" in data[0]["日付"]
            assert len(data[0]["日付"]) >= 19  # 最小限の長さ

        # S3 Accessorが正しく呼ばれたことを確認
        mock_s3_accessor.get_object.assert_called_once()
        call_args = mock_s3_accessor.get_object.call_args[0]
        assert "05339" in call_args[0]  # S3キーに騎手IDが含まれている

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_end_to_end_error_flow_404(self, mock_get_s3_accessor):
        """
        エンドツーエンドエラーフロー: S3から404を受信した場合
        API→サービス→S3Accessor→404エラー→HTTPException
        """
        # S3がNoneを返す（データが見つからない）
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = None
        mock_get_s3_accessor.return_value = mock_s3_accessor

        response = client.get("/api/jockey/99999")

        # 404レスポンスの検証
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "Not Found"
        assert "99999" in data["message"]

        # 内部詳細が漏洩していないことを確認
        assert "S3" not in data["message"]
        assert "pickle" not in data["message"].lower()

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_end_to_end_error_flow_s3_connection(self, mock_get_s3_accessor):
        """
        エンドツーエンドエラーフロー: S3接続エラー
        API→サービス→S3Accessor→接続エラー→500エラー
        """
        # S3接続エラーを発生させる
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.side_effect = S3AccessError(
            "Connection timeout", bucket="test-bucket", key="05339.pickle"
        )
        mock_get_s3_accessor.return_value = mock_s3_accessor

        response = client.get("/api/jockey/05339")

        # 500レスポンスの検証
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "Internal Server Error"

        # S3エラーであることは伝えるが、内部詳細（バケット名など）は含まれない
        assert "S3" in data["message"]
        assert "test-bucket" not in data["message"]
        assert "05339.pickle" not in data["message"]

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_end_to_end_error_flow_ssm_config(self, mock_get_s3_accessor):
        """
        エンドツーエンドエラーフロー: SSM Parameter Store認証失敗
        API→サービス→SSM設定エラー→503エラー
        """
        # SSM設定エラーを発生させる
        mock_get_s3_accessor.side_effect = SSMConfigError(
            "BUCKET_NAME", Exception("Access Denied")
        )

        response = client.get("/api/jockey/05339")

        # 503レスポンスの検証
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "Service Unavailable"

        # 設定エラーであることは伝えるが、パラメータ名は含まれない
        assert (
            "configuration" in data["message"].lower()
            or "support" in data["message"].lower()
        )
        assert "BUCKET_NAME" not in data["message"]

    def test_cors_preflight_request(self):
        """
        CORS Preflightリクエストのテスト
        OPTIONSリクエストで適切なCORSヘッダーが返されることを検証
        """
        # OPTIONSリクエスト（Preflight）
        response = client.options(
            "/api/jockey/05339",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        # CORSヘッダーの検証
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        # allow_origins=["*"]の場合、リクエストのOriginがそのまま返される
        assert response.headers["access-control-allow-origin"] == "http://example.com"
        assert "access-control-allow-methods" in response.headers
        assert "GET" in response.headers["access-control-allow-methods"]

    def test_cors_actual_request(self):
        """
        CORS実際のリクエストのテスト
        実際のGETリクエストで適切なCORSヘッダーが返されることを検証
        """
        # Originヘッダーを含むGETリクエスト
        with patch("app.services.jockey_service.get_s3_accessor") as mock_get_s3_accessor:
            mock_s3_accessor = MagicMock()
            # 簡単なモックデータ
            import pickle
            import pandas as pd
            df = pd.DataFrame({"test": [1, 2, 3]})
            mock_s3_accessor.get_object.return_value = pickle.dumps(df)
            mock_get_s3_accessor.return_value = mock_s3_accessor

            response = client.get(
                "/api/jockey/05339",
                headers={"Origin": "http://example.com"},
            )

            # CORSヘッダーの検証
            assert "access-control-allow-origin" in response.headers
            # allow_origins=["*"]の場合、実際のリクエストでは "*" が返される
            assert response.headers["access-control-allow-origin"] == "*"
