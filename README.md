# Jockey Data API

![CI](https://github.com/YOUR_USERNAME/jockey-data/workflows/CI/badge.svg)

騎手IDに基づいてAWS S3からpickleファイルを取得し、JSON形式で返却するREST APIサーバー。

## Features

- 🚀 FastAPI + Uvicornによる高性能REST API
- 🔄 AWS S3からのpickleファイル自動取得
- 📊 pandas DataFrameからJSON形式への変換
- ✅ CI/CD（Lint + Type Check + Test + Coverage）

## Development

### セットアップ

```zsh
# 依存関係をインストール
uv sync --extra dev

# 開発サーバーの起動
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### テスト実行

```zsh
# 全テストを実行
uv run pytest tests/ -v

# カバレッジレポート付き
uv run pytest tests/ --cov=app --cov-report=term-missing
```

### コード品質チェック

```zsh
# Linter
uv run ruff check app tests

# 自動修正
uv run ruff check app tests --fix

# 型チェック
uv run mypy app
```

## CI/CD

GitHub Actionsで以下を自動実行:
- ✅ Linting (ruff)
- ✅ Type checking (mypy)
- ✅ Unit tests (pytest)
- ✅ Coverage report

## License

MIT
