# Requirements Document

## Introduction

将棋アプリケーションは、将棋の局面を自由に編集したり、棋譜ファイルを再生したりできるWebアプリケーションです。AI評価値の表示機能を備え、棋譜研究や局面分析をサポートします。

## Glossary

- **System**: 将棋アプリケーション全体
- **Board**: 将棋盤（9x9のマス目）
- **Piece**: 将棋の駒
- **KIF_File**: 棋譜ファイル（.kif形式）
- **Position**: 盤面上の局面（駒の配置状態）
- **Evaluation**: AI評価値（局面の優劣を数値化したもの）
- **Free_Mode**: 自由配置モード
- **Replay_Mode**: 棋譜再生モード
- **AI_Engine**: PyTorchで実装される評価値算出エンジン
- **Frontend**: Vue.jsで実装されるユーザーインターフェース
- **Backend**: Flaskで実装されるAPIサーバー
- **Database**: MySQLデータベース

## Requirements

### Requirement 1: 自由配置モード

**User Story:** ユーザーとして、将棋盤上で駒を自由に配置・移動できるようにしたい。これにより、任意の局面を作成して分析できるようにする。

#### Acceptance Criteria

1. WHEN Free_Mode is activated, THE System SHALL display an empty Board with initial position
2. WHEN a user clicks on a Piece, THE System SHALL highlight that Piece as selected
3. WHEN a user clicks on a square while a Piece is selected, THE System SHALL move the Piece to that square
4. WHEN a user drags a Piece to another square, THE System SHALL move the Piece to the destination square
5. THE System SHALL allow users to add or remove Pieces from the Board
6. THE System SHALL allow users to flip Pieces to promoted state
7. WHEN a Position is modified, THE System SHALL persist the current Position to Database

### Requirement 2: 棋譜再生モード

**User Story:** ユーザーとして、.kifファイルを読み込んで棋譜を再生できるようにしたい。これにより、過去の対局を確認・研究できるようにする。

#### Acceptance Criteria

1. WHEN a user uploads a KIF_File, THE System SHALL parse the file and extract move sequences
2. IF a KIF_File is invalid or corrupted, THEN THE System SHALL display an error message and reject the file
3. WHEN a KIF_File is successfully loaded, THE System SHALL display the initial Position
4. THE System SHALL provide navigation controls to move forward and backward through moves
5. WHEN a user clicks the next move button, THE System SHALL advance to the next Position
6. WHEN a user clicks the previous move button, THE System SHALL return to the previous Position
7. THE System SHALL display move numbers and move notation for the current Position
8. THE System SHALL allow users to jump to a specific move number
9. WHEN a KIF_File is loaded, THE System SHALL persist the棋譜 data to Database

### Requirement 3: AI評価値表示

**User Story:** ユーザーとして、現在の局面に対するAI評価値を確認したい。これにより、局面の優劣を客観的に判断できるようにする。

#### Acceptance Criteria

1. WHERE Free_Mode or Replay_Mode is active, THE System SHALL provide an option to request Evaluation
2. WHEN a user requests Evaluation, THE Backend SHALL send the current Position to AI_Engine
3. WHEN AI_Engine returns Evaluation results, THE System SHALL display the Evaluation value on Frontend
4. THE System SHALL display Evaluation as a numerical value indicating advantage
5. WHEN Position changes, THE System SHALL allow users to request updated Evaluation
6. IF AI_Engine is unavailable or returns an error, THEN THE System SHALL display an appropriate error message
7. THE System SHALL provide an interface for AI_Engine integration without implementing the AI logic

### Requirement 4: データ永続化

**User Story:** ユーザーとして、作成した局面や読み込んだ棋譜を保存して後で再利用したい。

#### Acceptance Criteria

1. WHEN a Position is created in Free_Mode, THE System SHALL save the Position to Database
2. WHEN a KIF_File is uploaded, THE System SHALL save the棋譜 metadata and moves to Database
3. THE System SHALL allow users to retrieve saved Positions from Database
4. THE System SHALL allow users to retrieve saved棋譜 from Database
5. WHEN retrieving saved data, THE System SHALL restore the exact Position or棋譜 state

### Requirement 5: バックエンドAPI

**User Story:** 開発者として、フロントエンドとバックエンドが明確に分離されたAPIを持ちたい。これにより、保守性と拡張性を確保する。

#### Acceptance Criteria

1. THE Backend SHALL provide RESTful API endpoints for all operations
2. THE Backend SHALL handle Position data serialization and deserialization
3. THE Backend SHALL handle KIF_File parsing and validation
4. THE Backend SHALL provide an endpoint to send Position data to AI_Engine
5. THE Backend SHALL handle Database connections and queries
6. WHEN API requests are invalid, THE Backend SHALL return appropriate HTTP error codes and messages
7. THE Backend SHALL implement CORS configuration to allow Frontend requests

### Requirement 6: フロントエンドUI

**User Story:** ユーザーとして、直感的で使いやすいインターフェースで将棋盤を操作したい。

#### Acceptance Criteria

1. THE Frontend SHALL render a visual Board with all Pieces
2. THE Frontend SHALL provide clear visual feedback for user interactions
3. THE Frontend SHALL display mode selection UI for Free_Mode and Replay_Mode
4. WHERE Replay_Mode is active, THE Frontend SHALL display navigation controls
5. THE Frontend SHALL display Evaluation values in a clear and readable format
6. THE Frontend SHALL handle loading states during API requests
7. THE Frontend SHALL display error messages when operations fail

### Requirement 7: Docker環境

**User Story:** 開発者として、アプリケーション全体をDockerで起動できるようにしたい。これにより、環境構築を簡素化し、デプロイを容易にする。

#### Acceptance Criteria

1. THE System SHALL provide Docker Compose configuration for all services
2. THE System SHALL include separate containers for Frontend, Backend, and Database
3. WHEN docker-compose up is executed, THE System SHALL start all services automatically
4. THE System SHALL configure network connections between containers
5. THE System SHALL persist Database data using Docker volumes
6. THE System SHALL expose appropriate ports for Frontend and Backend access
7. THE System SHALL include environment variable configuration for each service

### Requirement 8: KIFファイル形式対応

**User Story:** ユーザーとして、標準的な.kif形式の棋譜ファイルを読み込めるようにしたい。

#### Acceptance Criteria

1. WHEN parsing a KIF_File, THE System SHALL extract game metadata (players, date, result)
2. WHEN parsing a KIF_File, THE System SHALL extract move sequences in standard notation
3. THE System SHALL handle both Japanese and ASCII move notation
4. THE System SHALL validate move legality during parsing
5. IF a move in KIF_File is illegal, THEN THE System SHALL report the error with move number
6. THE System SHALL handle special moves (castling, promotion, drops)
7. THE System SHALL preserve comments in KIF_File for display
