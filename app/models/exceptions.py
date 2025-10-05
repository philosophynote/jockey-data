"""
Custom Exception Classes

APIで使用するカスタム例外を定義
"""


class JockeyDataException(Exception):
    """Base exception for jockey data API"""
    pass


class JockeyNotFoundError(JockeyDataException):
    """
    指定された騎手IDのデータが見つからない場合に発生する例外
    HTTPステータスコード: 404
    """
    def __init__(self, jockey_id: str):
        self.jockey_id = jockey_id
        super().__init__(f"Jockey with ID '{jockey_id}' not found")


class S3AccessError(JockeyDataException):
    """
    S3へのアクセスに失敗した場合に発生する例外
    HTTPステータスコード: 500
    """
    def __init__(self, message: str, bucket: str = None, key: str = None):
        self.bucket = bucket
        self.key = key
        super().__init__(message)


class PickleDeserializeError(JockeyDataException):
    """
    pickleファイルのデシリアライズに失敗した場合に発生する例外
    HTTPステータスコード: 500
    """
    def __init__(self, jockey_id: str, original_error: Exception = None):
        self.jockey_id = jockey_id
        self.original_error = original_error
        message = f"Failed to deserialize data for jockey {jockey_id}"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)


class SSMConfigError(JockeyDataException):
    """
    SSM Parameter Storeからの設定取得に失敗した場合に発生する例外
    HTTPステータスコード: 503
    """
    def __init__(self, parameter_name: str, original_error: Exception = None):
        self.parameter_name = parameter_name
        self.original_error = original_error
        message = f"Failed to retrieve SSM parameter '{parameter_name}'"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)
