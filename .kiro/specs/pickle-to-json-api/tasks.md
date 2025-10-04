# 実装タスク

## タスク一覧

- [ ] 1. プロジェクト基盤の構築
- [ ] 1.1 FastAPIアプリケーションの初期化
  - FastAPIとUvicornの依存関係をプロジェクトに追加
  - FastAPIアプリケーションのエントリーポイントを作成
  - CORSミドルウェアを設定して全オリジンを許可
  - ヘルスチェックエンドポイントを実装
  - _Requirements: 5.2_

- [ ] 1.2 プロジェクト構造の構築
  - アプリケーションのディレクトリ構造を作成（API層、サービス層、インフラ層）
  - カスタム例外クラスを定義（JockeyNotFoundError、S3AccessError、PickleDeserializeError）
  - ログ設定を構築（構造化ログとログレベル設定）
  - _Requirements: 4.1, 4.2_

- [ ] 2. データアクセス層の実装
- [ ] 2.1 S3Accessorの統合
  - 既存のS3Accessorクラスをインフラ層にインポート
  - S3Accessorをグローバルスコープで初期化してコールドスタートを最適化
  - SSM Parameter Storeからの認証情報取得が正常に動作することを検証
  - S3接続エラー時の例外ハンドリングを確認
  - _Requirements: 2.1, 2.3, 2.4, 5.3_

- [ ] 3. ビジネスロジック層の実装
- [ ] 3.1 騎手データ取得サービスの実装
  - 騎手IDからS3キー名を生成する機能
  - S3AccessorからバイナリデータをString取得する機能
  - 取得失敗時にJockeyNotFoundErrorを送出する機能
  - S3接続エラー時のログ出力とエラーハンドリング
  - _Requirements: 1.2, 2.1, 2.2, 4.2_

- [ ] 3.2 pickleデシリアライズとJSON変換機能の実装
  - S3から取得したバイナリデータをpandasでデシリアライズする機能
  - デシリアライズ失敗時にPickleDeserializeErrorを送出する機能
  - pandas DataFrameをJSON形式に変換する機能（orient='records'）
  - 日付フィールドをISO 8601形式の文字列に変換する機能
  - JSON変換失敗時のエラーハンドリング
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 4. API層の実装
- [ ] 4.1 騎手データ取得エンドポイントの実装
  - `/api/jockey/{jockey_id}` GETエンドポイントを実装
  - パスパラメータからjockey_idを抽出
  - サービス層を呼び出してレースデータを取得
  - 成功時に200 OKとJSON配列を返却
  - _Requirements: 1.1, 1.4_

- [ ] 4.2 エラーハンドリングミドルウェアの実装
  - JockeyNotFoundErrorを404 HTTPレスポンスに変換
  - S3AccessErrorを500 HTTPレスポンスに変換
  - PickleDeserializeErrorを500 HTTPレスポンスに変換
  - 予期しない例外を500 HTTPレスポンスに変換
  - エラー詳細をログに記録し、クライアントには汎用メッセージのみ返却
  - _Requirements: 1.3, 2.2, 3.3, 4.3, 4.4_

- [ ] 5. 単体テストの実装
- [ ] 5.1 サービス層の単体テスト
  - 正常系: S3からデータ取得→デシリアライズ→JSON変換の成功ケース
  - 異常系: S3からNone返却時にJockeyNotFoundError送出を検証
  - 異常系: pickleデシリアライズ失敗時にPickleDeserializeError送出を検証
  - 日付フィールドがISO 8601形式に変換されることを検証
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 5.2 API層の単体テスト
  - `/api/jockey/{jockey_id}` エンドポイントの正常系テスト（200レスポンス）
  - 存在しないjockey_idで404レスポンスが返却されることを検証
  - S3接続エラー時に500レスポンスが返却されることを検証
  - エラーレスポンスに内部詳細が含まれないことを検証
  - _Requirements: 1.1, 1.3, 1.4, 2.2, 4.3_

- [ ] 5.3 ヘルスチェックエンドポイントのテスト
  - `/health` エンドポイントが200を返すことを検証
  - レスポンス時間が5秒以内であることを検証
  - _Requirements: 要件定義外（運用要件）_

- [ ] 6. 統合テストの実装
- [ ] 6.1 エンドツーエンドフローのテスト
  - モックS3を使用してAPI→サービス→S3Accessorの連携を検証
  - 実際のpickleファイルを使用したJSON変換の整合性テスト
  - CORS設定が正しく動作することを検証（Preflightリクエスト）
  - _Requirements: 1.1, 2.1, 3.1, 3.2, 5.2_

- [ ] 6.2 エラーフロー統合テスト
  - S3から404を受信した場合のエンドツーエンドエラーフロー検証
  - S3接続エラー時のエンドツーエンドエラーフロー検証
  - SSM Parameter Store認証失敗時の503レスポンス検証
  - _Requirements: 1.3, 2.2, 2.3_

- [ ] 7. Lambda Web Adapterデプロイメント準備
- [ ] 7.1 Dockerfileの作成
  - Python 3.13ベースイメージの選択
  - Lambda Web Adapterを/opt/extensionsにコピー
  - 依存関係のインストール（fastapi、uvicorn、pandas、boto3）
  - アプリケーションコードのコピー
  - Uvicorn起動コマンドの設定
  - _Requirements: デプロイメント要件_

- [ ] 7.2 Lambda環境変数の設定準備
  - AWS_LWA_PORT、AWS_LWA_INVOKE_MODE等の環境変数リストを作成
  - Lambda Function設定のテンプレート（SAM/CloudFormation）を作成
  - Lambda実行ロール（IAMポリシー）の定義
  - _Requirements: 2.4, 5.3, デプロイメント要件_

- [ ] 7.3 ローカルテスト環境の構築
  - Dockerイメージをローカルビルドするスクリプト作成
  - ローカルでのLambda環境シミュレーション実行手順を文書化
  - ローカルテスト用のAWS認証情報設定手順を文書化
  - _Requirements: デプロイメント要件_

- [ ] 8. パフォーマンステストの実装
- [ ] 8.1 レスポンスタイム測定
  - P50、P95、P99レスポンスタイムを測定するテストスクリプト
  - 小規模DataFrame（100行）、中規模（1,000行）、大規模（10,000行）での性能測定
  - S3 get_object APIのレイテンシ測定
  - _Requirements: パフォーマンス要件_

- [ ] 8.2 メモリ使用量測定
  - 大規模DataFrameのデシリアライズ時のメモリプロファイリング
  - Lambda 2GB設定での動作確認
  - メモリ不足が発生する閾値の特定
  - _Requirements: パフォーマンス要件_

- [ ] 9. 最終統合と検証
- [ ] 9.1 全機能統合テスト
  - 全エンドポイントの動作確認
  - 既存の騎手ID（05339）でのエンドツーエンド検証
  - エラーケースの網羅的な検証
  - ログ出力の確認（CloudWatch Logsシミュレーション）
  - _Requirements: 全要件_

- [ ] 9.2 デプロイメント前チェックリスト
  - Dockerイメージサイズが10GB以下であることを確認
  - コールドスタート時間が15秒以下であることを確認
  - 全テストが成功していることを確認
  - セキュリティ設定（CORS、認証情報管理）の最終確認
  - _Requirements: デプロイメント要件_
