# 謄本照会チャットボット (Touhon Chatbot)

登記簿謄本PDFをアップロードし、内容をAIチャットで照会できるWebアプリケーション。

## 技術スタック

- **Frontend**: Next.js 14 / React 18 / TypeScript / TailwindCSS
- **Backend**: FastAPI / Python 3.12 / SQLAlchemy (async)
- **Database**: PostgreSQL 16 + pgvector
- **AI**: Anthropic Claude API
- **OCR**: Google Cloud Vision API
- **Storage**: Google Cloud Storage (ローカルフォールバックあり)

## ローカル開発

```bash
cp .env.example .env
# .env を編集してAPIキーを設定
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## Railway デプロイ

### 構成

Railway プロジェクトに以下の3サービスを作成する:

1. **PostgreSQL** — Railway プラグインとして追加
2. **Backend** — GitHub repo を接続、Root Directory を `backend` に設定
3. **Frontend** — GitHub repo を接続、Root Directory を `frontend` に設定

### デプロイ手順

1. Railway で新規プロジェクトを作成
2. "Add Plugin" → PostgreSQL を追加
3. PostgreSQL の接続情報を使って `backend/sql/init.sql` を実行（テーブル初期化）
4. "New Service" → GitHub repo → Root Directory: `backend`
5. "New Service" → GitHub repo → Root Directory: `frontend`
6. 各サービスに環境変数を設定（下記参照）
7. 各サービスに Public Domain を生成

### 環境変数

#### Backend

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `DATABASE_URL` | Yes | `${{Postgres.DATABASE_URL}}` (Railway参照変数) |
| `BACKEND_SECRET_KEY` | Yes | JWT署名用のランダム文字列 |
| `CORS_ORIGINS` | Yes | Frontend の Railway URL (例: `https://xxx.up.railway.app`) |
| `ANTHROPIC_API_KEY` | Yes | Anthropic Claude API キー |
| `GOOGLE_CREDENTIALS_JSON` | No | GCP サービスアカウントの JSON を丸ごと貼り付け |
| `GCS_BUCKET_NAME` | No | Google Cloud Storage バケット名 |
| `RATE_LIMIT_REQUESTS` | No | レートリミット回数 (デフォルト: 20) |
| `RATE_LIMIT_WINDOW_SECONDS` | No | レートリミット期間秒 (デフォルト: 60) |
| `PORT` | No | Railway が自動設定 (デフォルト: 8000) |

#### Frontend

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `NEXT_PUBLIC_BACKEND_URL` | Yes | Backend の Railway URL (例: `https://xxx.up.railway.app`) |
| `NEXTAUTH_URL` | Yes | Frontend の Railway URL (例: `https://xxx.up.railway.app`) |
| `NEXTAUTH_SECRET` | Yes | ランダム文字列 (`openssl rand -base64 32` で生成) |

> **注意**: `NEXT_PUBLIC_BACKEND_URL` は `NEXT_PUBLIC_` プレフィックスのためビルド時に埋め込まれる。Backend を先にデプロイして URL を確定させること。

### DB 初期化

PostgreSQL プラグイン追加後、`backend/sql/init.sql` を実行してテーブルとpgvector拡張を初期化する:

```bash
# Railway CLI を使用する場合
railway run psql $DATABASE_URL -f backend/sql/init.sql
```
