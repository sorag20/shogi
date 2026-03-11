import type { Piece, PieceType, Owner } from '../types/shogi'

/**
 * 駒の名前を取得
 */
export function getPieceName(type: PieceType, promoted: boolean): string {
  const names: Record<PieceType, string> = {
    pawn: promoted ? 'と' : '歩',
    lance: promoted ? '成香' : '香',
    knight: promoted ? '成桂' : '桂',
    silver: promoted ? '成銀' : '銀',
    gold: '金',
    bishop: promoted ? '馬' : '角',
    rook: promoted ? '竜' : '飛',
    king: '玉',
  }
  return names[type] || type
}

/**
 * 座標を将棋の表記に変換（例: 7七）
 */
export function coordinatesToNotation(row: number, col: number): string {
  // 列は9から1（右から左）
  const colNum = 9 - col
  // 行は1から9（上から下）
  const rowNum = row + 1

  // 漢数字
  const rowKanji = ['一', '二', '三', '四', '五', '六', '七', '八', '九'][rowNum - 1]

  return `${colNum}${rowKanji}`
}

/**
 * 移動を棋譜表記に変換
 */
export function moveToNotation(
  piece: Piece,
  fromRow: number,
  fromCol: number,
  toRow: number,
  toCol: number,
  isCapture: boolean,
  promoted: boolean
): string {
  const coord = coordinatesToNotation(toRow, toCol)
  const pieceName = getPieceName(piece.type, piece.promoted || promoted)

  // 基本形式: ▲7六歩 または ▽3四歩
  const prefix = piece.owner === 'black' ? '▲' : '△'

  // 成った場合は「成」を追加
  const promoteStr = promoted && !piece.promoted ? '成' : ''

  return `${prefix}${coord}${pieceName}${promoteStr}`
}

/**
 * 移動の説明を生成
 */
export function getMoveDescription(
  piece: Piece,
  fromRow: number,
  fromCol: number,
  toRow: number,
  toCol: number,
  isCapture: boolean,
  promoted: boolean
): string {
  const from = coordinatesToNotation(fromRow, fromCol)
  const to = coordinatesToNotation(toRow, toCol)
  const pieceName = getPieceName(piece.type, piece.promoted)
  const owner = piece.owner === 'black' ? '先手' : '後手'

  let desc = `${owner}：${from}の${pieceName}を${to}へ移動`

  if (isCapture) {
    desc += '（駒を取る）'
  }

  if (promoted && !piece.promoted) {
    desc += '・成'
  }

  return desc
}
