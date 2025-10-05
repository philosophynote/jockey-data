"""
Jockey Service Unit Tests

JockeyServiceの実際のpickleファイルを使用してテストします。
"""

import os
import pickle
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.models.exceptions import JockeyNotFoundError, PickleDeserializeError, S3AccessError
from app.services.jockey_service import JockeyService


class TestJockeyService:
    """JockeyServiceのテストクラス"""

    @pytest.fixture
    def real_pickle_data(self):
        """実際のpickleファイルを読み込むフィクスチャ"""
        pickle_path = os.path.join(os.path.dirname(__file__), "..", "data", "05339.pickle")
        with open(pickle_path, "rb") as f:
            return f.read()

    @pytest.fixture
    def real_dataframe(self):
        """実際のpickleファイルからDataFrameを読み込むフィクスチャ"""
        pickle_path = os.path.join(os.path.dirname(__file__), "..", "data", "05339.pickle")
        with open(pickle_path, "rb") as f:
            return pickle.load(f)

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_generate_s3_key(self, mock_get_s3_accessor):
        """S3キー生成のテスト"""
        mock_s3_accessor = MagicMock()
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        key = service._generate_s3_key("05339")

        assert key == "05339.pickle"

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_binary_success(self, mock_get_s3_accessor, real_pickle_data):
        """騎手データ取得成功のテスト（実データ使用）"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = real_pickle_data
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        result = service.get_jockey_data_binary("05339")

        assert result == real_pickle_data
        assert len(result) > 0
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

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_deserialize_pickle_success(self, mock_get_s3_accessor, real_pickle_data):
        """pickleデシリアライズ成功のテスト"""
        mock_s3_accessor = MagicMock()
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        result = service.deserialize_pickle(real_pickle_data, "05339")

        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert len(result.columns) > 0

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_deserialize_pickle_invalid_data(self, mock_get_s3_accessor):
        """無効なpickleデータのデシリアライズテスト"""
        mock_s3_accessor = MagicMock()
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        invalid_data = pickle.dumps("not a dataframe")

        with pytest.raises(PickleDeserializeError) as exc_info:
            service.deserialize_pickle(invalid_data, "05339")

        assert exc_info.value.jockey_id == "05339"

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_deserialize_pickle_corrupted_data(self, mock_get_s3_accessor):
        """破損したpickleデータのデシリアライズテスト"""
        mock_s3_accessor = MagicMock()
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        corrupted_data = b"corrupted pickle data"

        with pytest.raises(PickleDeserializeError) as exc_info:
            service.deserialize_pickle(corrupted_data, "05339")

        assert exc_info.value.jockey_id == "05339"

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_dataframe_to_json_success(self, mock_get_s3_accessor, real_dataframe):
        """DataFrame→JSON変換成功のテスト"""
        mock_s3_accessor = MagicMock()
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        result = service.dataframe_to_json(real_dataframe, "05339")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)

        # 日付フィールドがISO 8601形式の文字列になっていることを確認
        if "日付" in result[0]:
            date_value = result[0]["日付"]
            assert isinstance(date_value, str)
            # ISO 8601形式チェック (YYYY-MM-DDTHH:MM:SS)
            assert "T" in date_value

    @patch("app.services.jockey_service.get_s3_accessor")
    def test_get_jockey_data_full_flow(self, mock_get_s3_accessor, real_pickle_data):
        """完全フロー（S3取得→デシリアライズ→JSON変換）のテスト"""
        mock_s3_accessor = MagicMock()
        mock_s3_accessor.get_object.return_value = real_pickle_data
        mock_get_s3_accessor.return_value = mock_s3_accessor

        service = JockeyService()
        result = service.get_jockey_data("05339")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)

        # 日付フィールドがISO 8601形式になっていることを確認
        if "日付" in result[0]:
            assert isinstance(result[0]["日付"], str)
            assert "T" in result[0]["日付"]

        # S3アクセスが呼ばれたことを確認
        mock_s3_accessor.get_object.assert_called_once_with("05339.pickle")
