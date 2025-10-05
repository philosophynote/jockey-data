"""
Jockey Service Unit Tests

JockeyServiceの基本機能をモックを使用してテストします。
"""

from unittest.mock import MagicMock, patch

import pytest

from app.models.exceptions import JockeyNotFoundError, S3AccessError
from app.services.jockey_service import JockeyService


class TestJockeyService:
    """JockeyServiceのテストクラス"""

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_generate_s3_key(self, mock_get_s3_accessor):
        """S3キー生成のテスト"""
        mock_s3_accessor = MagicMock()
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        key = service._generate_s3_key("05339")

        assert key == "05339.pickle"

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_binary_success(self, mock_get_s3_accessor):
        """騎手データ取得成功のテスト"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = b"test_pickle_data"
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        result = service.get_jockey_data_binary("05339")

        assert result == b"test_pickle_data"
        mock_s3_accessor.get_object.assert_called_once_with("05339.pickle")

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_binary_not_found(self, mock_get_s3_accessor):
        """騎手データが見つからない場合のテスト"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = None
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()

        with pytest.raises(JockeyNotFoundError) as exc_info:
            service.get_jockey_data_binary("99999")

        assert exc_info.value.jockey_id == "99999"
        mock_s3_accessor.get_object.assert_called_once_with("99999.pickle")

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_binary_s3_error(self, mock_get_s3_accessor):
        """S3アクセスエラーのテスト"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.side_effect = S3AccessError(
            "S3 connection failed",
            bucket="test-bucket",
            key="05339.pickle"
        )
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()

        with pytest.raises(S3AccessError) as exc_info:
            service.get_jockey_data_binary("05339")

        assert "S3 connection failed" in str(exc_info.value)
        mock_s3_accessor.get_object.assert_called_once_with("05339.pickle")
