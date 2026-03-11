# Design Document: 将棋アプリケーション

## Overview

将棋アプリケーションは、3層アーキテクチャ（フロントエンド、バックエンド、データベース）で構成されるWebアプリケーションです。Vue.jsで実装されたSPA（Single Page Application）がユーザーインターフェースを提供し、FlaskベースのRESTful APIがビジネスロジックとデータ永続化を担当します。AI評価値算出機能は外部PyTorchエンジンとの統合ポイントを提供します。

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Docker Host                          │
│                                                               │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Frontend   │      │   Backend    │      │  Database │ │
│  │   (Vue.js)   │◄────►│   (Flask)    │◄────►│  (MySQL)  │ │
│  │   Port 8080  │      │   Port 5000  │      │ Port 3306 │ │
│  └──────────────┘      └──────┬───────┘      └───────────┘ │
│                                │                             │
│                                ▼                             │
│                        ┌──────────────┐                      │
│                        │  AI Engine   │                      │
│                        │  (External)  │                      │
│                        │  (PyTorch)   │                      │
│                        └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Frontend**: Vue.js 3 + TypeScript + Vite
- **Backend**: Python 3.11 + Flask + SQLAlchemy
- **Database**: MySQL 8.0
- **Containerization**: Docker + Docker Compose
- **AI Integration**: REST API interface for PyTorch engine

## Components and Interfaces

### Frontend Components

#### 1. Board Component
将棋盤の表示と駒の操作を担当するコアコンポーネント。

**Responsibilities:**
- 9x9の将棋盤をレンダリング
- 駒のドラッグ&ドロップ処理
- 駒の選択状態管理
- 盤面の視覚的フィードバック

**Props:**
- `position: Position` - 現在の局面データ
- `mode: 'free' | 'replay'` - 動作モード
- `editable: boolean` - 編集可能かどうか

**Events:**
- `@move` - 駒が移動されたときに発火
- `@select` - 駒が選択されたときに発火

#### 2. Piece Component
個々の駒を表示するコンポーネント。

**Props:**
- `type: PieceType` - 駒の種類（歩、香、桂、銀、金、角、飛、玉）
- `owner: 'black' | 'white'` - 先手/後手
- `promoted: boolean` - 成駒かどうか
- `position: {x: number, y: number}` - 盤面上の位置

#### 3. ModeSelector Component
モード選択UI。

**Events:**
- `@mode-change` - モードが変更されたときに発火

#### 4. KifUploader Component
KIFファイルのアップロード処理。

**Events:**
- `@file-uploaded` - ファイルがアップロードされたときに発火

#### 5. ReplayControls Component
棋譜再生用のナビゲーションコントロール。

**Props:**
- `currentMove: number` - 現在の手数
- `totalMoves: number` - 総手数

**Events:**
- `@next` - 次の手へ
- `@previous` - 前の手へ
- `@jump` - 指定手数へジャンプ

#### 6. EvaluationDisplay Component
AI評価値の表示。

**Props:**
- `evaluation: number | null` - 評価値
- `loading: boolean` - 評価値計算中かどうか

**Events:**
- `@request-evaluation` - 評価値リクエスト

### Backend API Endpoints

#### Position Management

**POST /api/positions**
新しい局面を保存。

Request:
```json
{
  "board": [[piece_data]], 
  "turn": "black" | "white",
  "metadata": {}
}
```

Response:
```json
{
  "id": "uuid",
  "created_at": "timestamp"
}
```

**GET /api/positions/:id**
保存された局面を取得。

Response:
```json
{
  "id": "uuid",
  "board": [[piece_data]],
  "turn": "black" | "white",
  "metadata": {},
  "created_at": "timestamp"
}
```

#### KIF File Management

**POST /api/kif/upload**
KIFファイルをアップロードしてパース。

Request: `multipart/form-data` with file

Response:
```json
{
  "id": "uuid",
  "metadata": {
    "black_player": "string",
    "white_player": "string",
    "date": "string",
    "result": "string"
  },
  "moves": [
    {
      "move_number": 1,
      "notation": "7六歩(77)",
      "position": {...}
    }
  ]
}
```

**GET /api/kif/:id**
保存された棋譜を取得。

**GET /api/kif/:id/moves/:move_number**
特定の手数の局面を取得。

#### AI Evaluation

**POST /api/evaluate**
現在の局面の評価値を取得。

Request:
```json
{
  "position": {
    "board": [[piece_data]],
    "turn": "black" | "white"
  }
}
```

Response:
```json
{
  "evaluation": 123.45,
  "computed_at": "timestamp"
}
```

### Backend Components

#### 1. Position Model
局面データのモデル。

**Fields:**
- `id: UUID` - 主キー
- `board_state: JSON` - 盤面状態（9x9配列）
- `turn: Enum` - 手番
- `metadata: JSON` - メタデータ
- `created_at: DateTime`
- `updated_at: DateTime`

#### 2. Kifu Model
棋譜データのモデル。

**Fields:**
- `id: UUID` - 主キー
- `black_player: String`
- `white_player: String`
- `game_date: Date`
- `result: String`
- `created_at: DateTime`

#### 3. Move Model
指し手データのモデル。

**Fields:**
- `id: UUID` - 主キー
- `kifu_id: UUID` - 外部キー
- `move_number: Integer`
- `notation: String` - 棋譜表記
- `from_square: String` - 移動元
- `to_square: String` - 移動先
- `piece_type: String`
- `is_promotion: Boolean`
- `is_drop: Boolean`
- `comment: Text`
- `position_after: JSON` - この手の後の局面

#### 4. KifParser Service
KIFファイルのパース処理。

**Methods:**
- `parse(file_content: str) -> KifuData` - KIFファイルをパース
- `validate_moves(moves: List[Move]) -> bool` - 手の合法性チェック
- `extract_metadata(content: str) -> dict` - メタデータ抽出

#### 5. PositionSerializer Service
局面データのシリアライズ/デシリアライズ。

**Methods:**
- `serialize(position: Position) -> dict` - 局面をJSON化
- `deserialize(data: dict) -> Position` - JSONから局面を復元
- `to_sfen(position: Position) -> str` - SFEN形式に変換（AI連携用）

#### 6. AIEngineClient Service
外部AI評価エンジンとの通信。

**Methods:**
- `evaluate(position: Position) -> float` - 評価値を取得
- `is_available() -> bool` - エンジンの可用性チェック

**Configuration:**
- `AI_ENGINE_URL: str` - AIエンジンのエンドポイント
- `TIMEOUT: int` - タイムアウト設定

## Data Models

### Position Data Structure

```python
{
  "board": [
    [  # 9x9 array, board[y][x]
      {"type": "lance", "owner": "white", "promoted": false},
      {"type": "knight", "owner": "white", "promoted": false},
      # ... 9 columns
    ],
    # ... 9 rows
  ],
  "hands": {
    "black": {"pawn": 2, "lance": 0, ...},
    "white": {"pawn": 1, "lance": 1, ...}
  },
  "turn": "black" | "white"
}
```

### KIF File Format

標準的なKIF形式：
```
# ---- 棋譜ファイル ----
開始日時：2024/01/01
棋戦：
手合割：平手
先手：先手名
後手：後手名
手数----指手---------消費時間--
   1 ７六歩(77)   ( 0:00/00:00:00)
   2 ３四歩(33)   ( 0:00/00:00:00)
   3 ２六歩(27)   ( 0:00/00:00:00)
```

### SFEN Format (AI Engine Interface)

将棋の局面を表す標準フォーマット：
```
sfen lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1
```

## Correctness Properties

*プロパティとは、システムのすべての有効な実行において真であるべき特性や動作のことです。これは人間が読める仕様と機械で検証可能な正確性保証の橋渡しとなります。*


### Property 1: 駒の移動操作
*任意の*局面と任意の駒に対して、その駒を別のマスに移動させた場合、移動後の局面では駒が指定されたマスに存在すること
**Validates: Requirements 1.3, 1.4**

### Property 2: 駒の選択状態
*任意の*駒に対して、その駒を選択した場合、システムはその駒を選択状態として記録し、視覚的にハイライト表示すること
**Validates: Requirements 1.2**

### Property 3: 駒の追加・削除
*任意の*駒タイプと任意の盤面位置に対して、駒を追加した場合はその位置に駒が存在し、駒を削除した場合はその位置が空になること
**Validates: Requirements 1.5**

### Property 4: 駒の成り状態切り替え
*任意の*成ることができる駒に対して、成り状態を切り替えた場合、駒の成り状態が反転すること
**Validates: Requirements 1.6**

### Property 5: 局面の永続化ラウンドトリップ
*任意の*局面に対して、その局面をデータベースに保存してから取得した場合、元の局面と同一の局面が復元されること
**Validates: Requirements 1.7, 4.1, 4.3, 4.5**

### Property 6: KIFファイルのパースと指し手抽出
*任意の*有効なKIFファイルに対して、パース処理を実行した場合、すべての指し手が正しく抽出され、手数と棋譜表記が保持されること
**Validates: Requirements 2.1, 8.1, 8.2**

### Property 7: 無効なKIFファイルの拒否
*任意の*無効または破損したKIFファイルに対して、パース処理を実行した場合、システムはエラーメッセージを返し、ファイルを拒否すること
**Validates: Requirements 2.2**

### Property 8: 棋譜ナビゲーションのラウンドトリップ
*任意の*棋譜と任意の手数に対して、次の手に進んでから前の手に戻った場合、元の局面と同一の局面に戻ること
**Validates: Requirements 2.5, 2.6**

### Property 9: 手数表示の正確性
*任意の*棋譜の任意の手数に対して、その手数の局面を表示した場合、正しい手数と棋譜表記が表示されること
**Validates: Requirements 2.7**

### Property 10: 特定手数へのジャンプ
*任意の*棋譜と任意の有効な手数に対して、その手数にジャンプした場合、システムは正しくその手数の局面を表示すること
**Validates: Requirements 2.8**

### Property 11: 棋譜の永続化ラウンドトリップ
*任意の*KIFファイルに対して、そのファイルをアップロードしてデータベースに保存してから取得した場合、元の棋譜データ（メタデータと指し手）が完全に復元されること
**Validates: Requirements 2.9, 4.2, 4.4, 4.5**

### Property 12: AI評価値リクエストの送信
*任意の*局面に対して、評価値をリクエストした場合、バックエンドは正しいフォーマット（SFEN形式）でAIエンジンにリクエストを送信すること
**Validates: Requirements 3.2**

### Property 13: 評価値の表示
*任意の*評価値に対して、AIエンジンから評価値が返された場合、システムはその評価値を数値としてフロントエンドに表示すること
**Validates: Requirements 3.3**

### Property 14: 局面変更後の評価値再リクエスト
*任意の*局面変更に対して、局面が変更された後に評価値を再リクエストした場合、システムは新しい局面に対する評価値を取得すること
**Validates: Requirements 3.5**

### Property 15: AIエンジンエラーハンドリング
*任意の*AIエンジンのエラー状態に対して、エラーが発生した場合、システムは適切なエラーメッセージをユーザーに表示すること
**Validates: Requirements 3.6**

### Property 16: 局面データのシリアライゼーションラウンドトリップ
*任意の*局面に対して、その局面をシリアライズしてからデシリアライズした場合、元の局面と同一の局面が復元されること
**Validates: Requirements 5.2**

### Property 17: 無効なAPIリクエストのエラーハンドリング
*任意の*無効なAPIリクエストに対して、バックエンドは適切なHTTPエラーコード（4xx）とエラーメッセージを返すこと
**Validates: Requirements 5.6**

### Property 18: 盤面レンダリングの完全性
*任意の*局面に対して、その局面をレンダリングした場合、盤面上のすべての駒が正しい位置に表示されること
**Validates: Requirements 6.1**

### Property 19: ローディング状態の表示
*任意の*APIリクエストに対して、リクエスト実行中はローディング状態が表示され、完了後はローディング状態が解除されること
**Validates: Requirements 6.6**

### Property 20: エラーメッセージの表示
*任意の*操作エラーに対して、エラーが発生した場合、システムはユーザーにエラーメッセージを表示すること
**Validates: Requirements 6.7**

### Property 21: 手の合法性検証
*任意の*指し手に対して、その手が将棋のルールに従って合法かどうかを正しく判定すること
**Validates: Requirements 8.4**

### Property 22: 不正な手のエラー報告
*任意の*不正な手を含むKIFファイルに対して、パース処理を実行した場合、システムはエラーメッセージと該当する手数を報告すること
**Validates: Requirements 8.5**

### Property 23: KIFコメントの保持
*任意の*コメントを含むKIFファイルに対して、パース処理を実行した場合、すべてのコメントが保持され、対応する手と関連付けられること
**Validates: Requirements 8.7**

## Error Handling

### Frontend Error Handling

1. **Network Errors**
   - APIリクエスト失敗時にユーザーフレンドリーなエラーメッセージを表示
   - リトライオプションを提供
   - タイムアウト設定（30秒）

2. **File Upload Errors**
   - ファイルサイズ制限（10MB）
   - サポートされていないファイル形式の拒否
   - パースエラーの詳細表示

3. **Validation Errors**
   - 不正な入力に対するインラインバリデーション
   - エラーメッセージの即座表示

### Backend Error Handling

1. **API Error Responses**
   - 400 Bad Request: 不正なリクエストパラメータ
   - 404 Not Found: リソースが見つからない
   - 422 Unprocessable Entity: KIFパースエラー、不正な手
   - 500 Internal Server Error: サーバー内部エラー
   - 503 Service Unavailable: AIエンジン接続エラー

2. **Database Errors**
   - 接続エラーのリトライロジック（最大3回）
   - トランザクションのロールバック
   - エラーログの記録

3. **AI Engine Errors**
   - タイムアウト処理（10秒）
   - 接続エラー時のフォールバック
   - エラー状態のキャッシュ（1分間）

### Error Logging

- すべてのエラーをログファイルに記録
- エラーレベル：DEBUG, INFO, WARNING, ERROR, CRITICAL
- ログローテーション設定

## Testing Strategy

### Unit Testing

**Frontend (Vue.js + Vitest)**
- コンポーネント単体テスト
- ユーザーインタラクションのシミュレーション
- エッジケース：空の盤面、満杯の持ち駒、境界値

**Backend (Python + pytest)**
- APIエンドポイントのテスト
- モデルのバリデーションテスト
- サービスクラスのテスト
- エッジケース：空のKIFファイル、巨大なファイル、不正なフォーマット

### Property-Based Testing

プロパティベーステストは、ランダムに生成された多数の入力に対して普遍的な特性を検証します。各プロパティテストは最低100回の反復実行を行います。

**Frontend Property Tests (fast-check)**
- Property 1-4: 駒操作の正確性
- Property 18: レンダリングの完全性
- Property 19-20: UI状態管理

**Backend Property Tests (Hypothesis)**
- Property 5: 局面永続化のラウンドトリップ
- Property 6-7: KIFパース機能
- Property 8-11: 棋譜ナビゲーションと永続化
- Property 12-15: AI評価値機能
- Property 16-17: シリアライゼーションとエラーハンドリング
- Property 21-23: 手の合法性とKIF処理

**Test Configuration:**
- 各プロパティテストは最低100回の反復実行
- 各テストには設計書のプロパティ番号を参照するタグを付与
- タグ形式：`# Feature: shogi-app, Property N: [プロパティ名]`

**Testing Libraries:**
- Frontend: fast-check (TypeScript用プロパティベーステストライブラリ)
- Backend: Hypothesis (Python用プロパティベーステストライブラリ)

### Integration Testing

- フロントエンドとバックエンドの統合テスト
- データベース接続テスト
- Docker環境での統合テスト

### End-to-End Testing

- Cypress/Playwrightを使用したE2Eテスト
- 主要なユーザーフロー：
  - 自由配置モードでの駒操作
  - KIFファイルのアップロードと再生
  - AI評価値の取得と表示

### Test Data

**KIF Test Files:**
- 有効な標準的な棋譜
- 不正なフォーマットの棋譜
- 不正な手を含む棋譜
- コメント付き棋譜
- 特殊な手（成り、打ち）を含む棋譜

**Position Test Data:**
- 初期局面
- 中盤の局面
- 終盤の局面
- 詰み局面
- 不正な局面（玉が2つなど）

## Implementation Notes

### KIF Parser Implementation

KIFパーサーは以下の手順で実装：
1. ファイルエンコーディング検出（Shift-JIS/UTF-8）
2. メタデータセクションのパース
3. 指し手セクションのパース
4. 各手の合法性検証
5. 局面の段階的構築

### Position Representation

内部的には9x9の2次元配列で表現：
- `board[y][x]` でアクセス（y: 0-8, x: 0-8）
- 座標系：左上が(0,0)、右下が(8,8)
- 将棋の表記（1一〜9九）との変換が必要

### AI Engine Integration

AIエンジンとの統合は以下のインターフェースで実現：

**Request Format:**
```json
POST /evaluate
{
  "sfen": "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1"
}
```

**Response Format:**
```json
{
  "evaluation": 123.45,
  "best_move": "7g7f",
  "pv": ["7g7f", "3c3d", "2g2f"]
}
```

### Docker Configuration

**docker-compose.yml structure:**
```yaml
services:
  frontend:
    build: ./frontend
    ports: ["8080:8080"]
    depends_on: [backend]
  
  backend:
    build: ./backend
    ports: ["5000:5000"]
    depends_on: [db]
    environment:
      - DATABASE_URL=mysql://user:pass@db:3306/shogi
      - AI_ENGINE_URL=http://ai-engine:8000
  
  db:
    image: mysql:8.0
    volumes: ["db-data:/var/lib/mysql"]
    environment:
      - MYSQL_DATABASE=shogi
      - MYSQL_ROOT_PASSWORD=password
```

### Security Considerations

- SQLインジェクション対策：SQLAlchemyのパラメータ化クエリ使用
- XSS対策：Vue.jsの自動エスケープ機能
- CSRF対策：トークンベース認証（将来の拡張）
- ファイルアップロード制限：サイズ、形式、スキャン
- レート制限：API呼び出しの制限（将来の拡張）
