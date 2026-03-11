import type { Piece, PieceType, Owner, BoardState } from '../types/shogi'

export interface Position {
  row: number
  col: number
}

/**
 * 指定された駒が移動可能な位置を取得
 */
export function getValidMoves(
  board: (Piece | null)[][],
  fromRow: number,
  fromCol: number
): Position[] {
  const piece = board[fromRow][fromCol]
  if (!piece) return []

  const moves: Position[] = []
  const direction = piece.owner === 'black' ? -1 : 1 // 黒は上(-)、白は下(+)

  switch (piece.type) {
    case 'pawn':
      if (piece.promoted) {
        // と金：金と同じ動き
        addGoldMoves(moves, fromRow, fromCol, direction, board, piece.owner)
      } else {
        // 歩：前に1マス
        addMove(moves, fromRow + direction, fromCol, board, piece.owner)
      }
      break

    case 'lance':
      if (piece.promoted) {
        // 成香：金と同じ動き
        addGoldMoves(moves, fromRow, fromCol, direction, board, piece.owner)
      } else {
        // 香：前方に直進
        addSlidingMoves(moves, fromRow, fromCol, direction, 0, board, piece.owner)
      }
      break

    case 'knight':
      if (piece.promoted) {
        // 成桂：金と同じ動き
        addGoldMoves(moves, fromRow, fromCol, direction, board, piece.owner)
      } else {
        // 桂：前方2マス+左右1マス
        addMove(moves, fromRow + direction * 2, fromCol - 1, board, piece.owner)
        addMove(moves, fromRow + direction * 2, fromCol + 1, board, piece.owner)
      }
      break

    case 'silver':
      if (piece.promoted) {
        // 成銀：金と同じ動き
        addGoldMoves(moves, fromRow, fromCol, direction, board, piece.owner)
      } else {
        // 銀：前方3方向と斜め後ろ2方向
        addMove(moves, fromRow + direction, fromCol - 1, board, piece.owner) // 左前
        addMove(moves, fromRow + direction, fromCol, board, piece.owner) // 前
        addMove(moves, fromRow + direction, fromCol + 1, board, piece.owner) // 右前
        addMove(moves, fromRow - direction, fromCol - 1, board, piece.owner) // 左後ろ
        addMove(moves, fromRow - direction, fromCol + 1, board, piece.owner) // 右後ろ
      }
      break

    case 'gold':
      // 金：前方3方向と横2方向と真後ろ
      addGoldMoves(moves, fromRow, fromCol, direction, board, piece.owner)
      break

    case 'bishop':
      if (piece.promoted) {
        // 竜馬：斜め方向に直進+縦横1マス
        addSlidingMoves(moves, fromRow, fromCol, -1, -1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, -1, 1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 1, -1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 1, 1, board, piece.owner)
        addMove(moves, fromRow - 1, fromCol, board, piece.owner) // 上
        addMove(moves, fromRow + 1, fromCol, board, piece.owner) // 下
        addMove(moves, fromRow, fromCol - 1, board, piece.owner) // 左
        addMove(moves, fromRow, fromCol + 1, board, piece.owner) // 右
      } else {
        // 角：斜め方向に直進
        addSlidingMoves(moves, fromRow, fromCol, -1, -1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, -1, 1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 1, -1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 1, 1, board, piece.owner)
      }
      break

    case 'rook':
      if (piece.promoted) {
        // 竜王：縦横に直進+斜め1マス
        addSlidingMoves(moves, fromRow, fromCol, -1, 0, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 1, 0, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 0, -1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 0, 1, board, piece.owner)
        addMove(moves, fromRow - 1, fromCol - 1, board, piece.owner) // 左上
        addMove(moves, fromRow - 1, fromCol + 1, board, piece.owner) // 右上
        addMove(moves, fromRow + 1, fromCol - 1, board, piece.owner) // 左下
        addMove(moves, fromRow + 1, fromCol + 1, board, piece.owner) // 右下
      } else {
        // 飛：縦横に直進
        addSlidingMoves(moves, fromRow, fromCol, -1, 0, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 1, 0, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 0, -1, board, piece.owner)
        addSlidingMoves(moves, fromRow, fromCol, 0, 1, board, piece.owner)
      }
      break

    case 'king':
      // 玉：全方向1マス
      addMove(moves, fromRow - 1, fromCol - 1, board, piece.owner)
      addMove(moves, fromRow - 1, fromCol, board, piece.owner)
      addMove(moves, fromRow - 1, fromCol + 1, board, piece.owner)
      addMove(moves, fromRow, fromCol - 1, board, piece.owner)
      addMove(moves, fromRow, fromCol + 1, board, piece.owner)
      addMove(moves, fromRow + 1, fromCol - 1, board, piece.owner)
      addMove(moves, fromRow + 1, fromCol, board, piece.owner)
      addMove(moves, fromRow + 1, fromCol + 1, board, piece.owner)
      break
  }

  return moves
}

/**
 * 金の動き（金、と金、成香、成桂、成銀）
 */
function addGoldMoves(
  moves: Position[],
  row: number,
  col: number,
  direction: number,
  board: (Piece | null)[][],
  owner: Owner
) {
  addMove(moves, row + direction, col - 1, board, owner) // 左前
  addMove(moves, row + direction, col, board, owner) // 前
  addMove(moves, row + direction, col + 1, board, owner) // 右前
  addMove(moves, row, col - 1, board, owner) // 左
  addMove(moves, row, col + 1, board, owner) // 右
  addMove(moves, row - direction, col, board, owner) // 後ろ
}

/**
 * 1マスの移動を追加
 */
function addMove(
  moves: Position[],
  row: number,
  col: number,
  board: (Piece | null)[][],
  owner: Owner
) {
  if (isValidPosition(row, col)) {
    const targetPiece = board[row][col]
    // 空きマスまたは相手の駒なら移動可能
    if (!targetPiece || targetPiece.owner !== owner) {
      moves.push({ row, col })
    }
  }
}

/**
 * 直進移動を追加（飛車、角、香）
 */
function addSlidingMoves(
  moves: Position[],
  fromRow: number,
  fromCol: number,
  rowDir: number,
  colDir: number,
  board: (Piece | null)[][],
  owner: Owner
) {
  let row = fromRow + rowDir
  let col = fromCol + colDir

  while (isValidPosition(row, col)) {
    const targetPiece = board[row][col]

    if (!targetPiece) {
      // 空きマス：移動可能、続行
      moves.push({ row, col })
    } else if (targetPiece.owner !== owner) {
      // 相手の駒：移動可能、終了
      moves.push({ row, col })
      break
    } else {
      // 自分の駒：移動不可、終了
      break
    }

    row += rowDir
    col += colDir
  }
}

/**
 * 盤面内の位置かチェック
 */
function isValidPosition(row: number, col: number): boolean {
  return row >= 0 && row < 9 && col >= 0 && col < 9
}

/**
 * 成れるかどうかをチェック
 */
export function canPromote(piece: Piece, fromRow: number, toRow: number): boolean {
  if (piece.promoted) return false
  if (piece.type === 'gold' || piece.type === 'king') return false

  // 敵陣（相手側3段）に入るか、敵陣から出るか
  if (piece.owner === 'black') {
    // 黒（先手）：0-2行が敵陣
    return fromRow <= 2 || toRow <= 2
  } else {
    // 白（後手）：6-8行が敵陣
    return fromRow >= 6 || toRow >= 6
  }
}
