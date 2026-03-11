export type PieceType = 'pawn' | 'lance' | 'knight' | 'silver' | 'gold' | 'bishop' | 'rook' | 'king'
export type Owner = 'black' | 'white'

export interface Piece {
  type: PieceType
  owner: Owner
  promoted: boolean
}

export interface BoardState {
  board: (Piece | null)[][]
  hands: {
    black: Record<PieceType, number>
    white: Record<PieceType, number>
  }
  turn: Owner
}

export interface Square {
  row: number
  col: number
  piece: Piece | null
}
