import type { BoardState, Piece } from '../types/shogi'

/**
 * 将棋の初期配置を作成
 */
export function createInitialBoard(): BoardState {
  const board: (Piece | null)[][] = Array(9)
    .fill(null)
    .map(() => Array(9).fill(null))

  // 後手（白）の駒配置（上側、0行目から）
  // 1段目（0行目）
  board[0][0] = { type: 'lance', owner: 'white', promoted: false }
  board[0][1] = { type: 'knight', owner: 'white', promoted: false }
  board[0][2] = { type: 'silver', owner: 'white', promoted: false }
  board[0][3] = { type: 'gold', owner: 'white', promoted: false }
  board[0][4] = { type: 'king', owner: 'white', promoted: false }
  board[0][5] = { type: 'gold', owner: 'white', promoted: false }
  board[0][6] = { type: 'silver', owner: 'white', promoted: false }
  board[0][7] = { type: 'knight', owner: 'white', promoted: false }
  board[0][8] = { type: 'lance', owner: 'white', promoted: false }

  // 2段目（1行目）
  board[1][1] = { type: 'rook', owner: 'white', promoted: false }
  board[1][7] = { type: 'bishop', owner: 'white', promoted: false }

  // 3段目（2行目）- 歩
  for (let col = 0; col < 9; col++) {
    board[2][col] = { type: 'pawn', owner: 'white', promoted: false }
  }

  // 先手（黒）の駒配置（下側、6行目から）
  // 7段目（6行目）- 歩
  for (let col = 0; col < 9; col++) {
    board[6][col] = { type: 'pawn', owner: 'black', promoted: false }
  }

  // 8段目（7行目）
  board[7][1] = { type: 'bishop', owner: 'black', promoted: false }
  board[7][7] = { type: 'rook', owner: 'black', promoted: false }

  // 9段目（8行目）
  board[8][0] = { type: 'lance', owner: 'black', promoted: false }
  board[8][1] = { type: 'knight', owner: 'black', promoted: false }
  board[8][2] = { type: 'silver', owner: 'black', promoted: false }
  board[8][3] = { type: 'gold', owner: 'black', promoted: false }
  board[8][4] = { type: 'king', owner: 'black', promoted: false }
  board[8][5] = { type: 'gold', owner: 'black', promoted: false }
  board[8][6] = { type: 'silver', owner: 'black', promoted: false }
  board[8][7] = { type: 'knight', owner: 'black', promoted: false }
  board[8][8] = { type: 'lance', owner: 'black', promoted: false }

  return {
    board,
    hands: {
      black: { pawn: 0, lance: 0, knight: 0, silver: 0, gold: 0, bishop: 0, rook: 0, king: 0 },
      white: { pawn: 0, lance: 0, knight: 0, silver: 0, gold: 0, bishop: 0, rook: 0, king: 0 },
    },
    turn: 'black',
  }
}

/**
 * 空の盤面を作成
 */
export function createEmptyBoard(): BoardState {
  return {
    board: Array(9)
      .fill(null)
      .map(() => Array(9).fill(null)),
    hands: {
      black: { pawn: 0, lance: 0, knight: 0, silver: 0, gold: 0, bishop: 0, rook: 0, king: 0 },
      white: { pawn: 0, lance: 0, knight: 0, silver: 0, gold: 0, bishop: 0, rook: 0, king: 0 },
    },
    turn: 'black',
  }
}
