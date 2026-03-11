# 将棋アプリケーション

将棋の局面を自由に編集したり、棋譜ファイルを再生したりできるWebアプリケーションです。AI評価値の表示機能を備え、棋譜研究や局面分析をサポートします。

## 機能

- **自由配置モード**: 将棋盤上で駒を自由に配置・移動できます
- **棋譜再生モード**: .kifファイルを読み込んで棋譜を再生できます
- **AI評価値表示**: 現在の局面に対するAI評価値を表示できます
- **データ永続化**: 作成した局面や読み込んだ棋譜をデータベースに保存できます

## 技術スタック

- **フロントエンド**: Vue.js 3 + TypeScript + Vite
- **バックエンド**: Python 3.11 + Flask
- **データベース**: MySQL 8.0
- **コンテナ化**: Docker + Docker Compose

## セットアップ

### 前提条件

- Docker
- Docker Compose

### インストール

1. リポジトリをクローン
```bash
git clone <repository-url>
cd shogi-app
```

2. 環境変数を設定（必要に応じて）
```bash
# .env ファイルは既に作成されています
# 必要に応じて編集してください
```

3. Docker Composeで起動
```bash
docker-compose up -d
```

4. アプリケーションにアクセス
- フロントエンド: http://localhost:8080
- バックエンド API: http://localhost:5000
- MySQL: localhost:3306

## 開発

### バックエンド開発

```bash
# バックエンドコンテナに入る
docker-compose exec backend bash

# テストを実行
pytest

# プロパティベーステストを実行
pytest --hypothesis-seed=0
```

### フロントエンド開発

```bash
# フロントエンドコンテナに入る
docker-compose exec frontend bash

# テストを実行
npm test

# ビルド
npm run build
```

### データベース

```bash
# MySQLコンテナに入る
docker-compose exec db mysql -u shogi_user -p shogi_db

# パスワード: shogi_password
```

## API エンドポイント

### 局面管理

- `POST /api/positions` - 新しい局面を保存
- `GET /api/positions/:id` - 局面を取得
- `PUT /api/positions/:id` - 局面を更新
- `DELETE /api/positions/:id` - 局面を削除

### 棋譜管理

- `POST /api/kif/upload` - KIFファイルをアップロード
- `GET /api/kif/:id` - 棋譜を取得
- `GET /api/kif/:id/moves/:move_number` - 特定手数の局面を取得

### AI評価値

- `POST /api/evaluate` - 局面の評価値を取得

## プロジェクト構造

```
shogi-app/
├── docker-compose.yml      # Docker Compose設定
├── .env                     # 環境変数
├── README.md               # このファイル
├── backend/                # バックエンドアプリケーション
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── ...
├── frontend/               # フロントエンドアプリケーション
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   └── ...
│   └── ...
└── db/                     # データベース初期化スクリプト
    └── init.sql
```

## トラブルシューティング

### ポートが既に使用されている場合

```bash
# 別のポートを使用するように docker-compose.yml を編集
# または既存のコンテナを停止
docker-compose down
```

### データベース接続エラー

```bash
# MySQLコンテナが起動しているか確認
docker-compose ps

# ログを確認
docker-compose logs db
```

### フロントエンドが表示されない

```bash
# フロントエンドコンテナのログを確認
docker-compose logs frontend

# ブラウザのキャッシュをクリア
```

## ライセンス

MIT

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。
