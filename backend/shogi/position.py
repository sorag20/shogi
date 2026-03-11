from typing import Dict, List, Optional
from .board import Board
from .piece import Piece, PieceType, Owner

class Position:
    """Represents a complete shogi position (board + hands + turn)"""
    
    def __init__(self, board: Optional[Board] = None, turn: Owner = Owner.BLACK):
        self.board = board or Board()
        self.turn = turn
        self.hands = {
            Owner.BLACK: {},
            Owner.WHITE: {}
        }
        self._initialize_hands()
    
    def _initialize_hands(self):
        """Initialize empty hands for both players"""
        for piece_type in PieceType:
            if piece_type != PieceType.KING:
                self.hands[Owner.BLACK][piece_type] = 0
                self.hands[Owner.WHITE][piece_type] = 0
    
    def add_to_hand(self, owner: Owner, piece_type: PieceType) -> None:
        """Add piece to player's hand"""
        if piece_type == PieceType.KING:
            raise ValueError('Cannot add king to hand')
        if piece_type not in self.hands[owner]:
            self.hands[owner][piece_type] = 0
        self.hands[owner][piece_type] += 1
    
    def remove_from_hand(self, owner: Owner, piece_type: PieceType) -> bool:
        """Remove piece from player's hand"""
        if piece_type not in self.hands[owner] or self.hands[owner][piece_type] == 0:
            return False
        self.hands[owner][piece_type] -= 1
        return True
    
    def get_hand_count(self, owner: Owner, piece_type: PieceType) -> int:
        """Get count of piece type in player's hand"""
        return self.hands[owner].get(piece_type, 0)
    
    def switch_turn(self) -> None:
        """Switch turn to other player"""
        self.turn = Owner.WHITE if self.turn == Owner.BLACK else Owner.BLACK
    
    def to_dict(self) -> dict:
        """Convert position to dictionary"""
        return {
            'board': self.board.to_dict(),
            'hands': {
                owner.value: {
                    piece_type.value: count 
                    for piece_type, count in pieces.items()
                }
                for owner, pieces in self.hands.items()
            },
            'turn': self.turn.value
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Position':
        """Create position from dictionary"""
        board = Board.from_dict(data['board'])
        turn = Owner(data['turn'])
        position = Position(board, turn)
        
        # Restore hands
        for owner_str, pieces_dict in data['hands'].items():
            owner = Owner(owner_str)
            for piece_type_str, count in pieces_dict.items():
                piece_type = PieceType(piece_type_str)
                position.hands[owner][piece_type] = count
        
        return position
    
    def get_initial_position() -> 'Position':
        """Get initial shogi position"""
        position = Position()
        board = position.board
        
        # Set up black pieces (top)
        board.set_piece(0, 0, Piece(PieceType.LANCE, Owner.BLACK))
        board.set_piece(0, 1, Piece(PieceType.KNIGHT, Owner.BLACK))
        board.set_piece(0, 2, Piece(PieceType.SILVER, Owner.BLACK))
        board.set_piece(0, 3, Piece(PieceType.GOLD, Owner.BLACK))
        board.set_piece(0, 4, Piece(PieceType.KING, Owner.BLACK))
        board.set_piece(0, 5, Piece(PieceType.GOLD, Owner.BLACK))
        board.set_piece(0, 6, Piece(PieceType.SILVER, Owner.BLACK))
        board.set_piece(0, 7, Piece(PieceType.KNIGHT, Owner.BLACK))
        board.set_piece(0, 8, Piece(PieceType.LANCE, Owner.BLACK))
        
        board.set_piece(1, 1, Piece(PieceType.BISHOP, Owner.BLACK))
        board.set_piece(1, 7, Piece(PieceType.ROOK, Owner.BLACK))
        
        for col in range(9):
            board.set_piece(2, col, Piece(PieceType.PAWN, Owner.BLACK))
        
        # Set up white pieces (bottom)
        for col in range(9):
            board.set_piece(6, col, Piece(PieceType.PAWN, Owner.WHITE))
        
        board.set_piece(7, 1, Piece(PieceType.ROOK, Owner.WHITE))
        board.set_piece(7, 7, Piece(PieceType.BISHOP, Owner.WHITE))
        
        board.set_piece(8, 0, Piece(PieceType.LANCE, Owner.WHITE))
        board.set_piece(8, 1, Piece(PieceType.KNIGHT, Owner.WHITE))
        board.set_piece(8, 2, Piece(PieceType.SILVER, Owner.WHITE))
        board.set_piece(8, 3, Piece(PieceType.GOLD, Owner.WHITE))
        board.set_piece(8, 4, Piece(PieceType.KING, Owner.WHITE))
        board.set_piece(8, 5, Piece(PieceType.GOLD, Owner.WHITE))
        board.set_piece(8, 6, Piece(PieceType.SILVER, Owner.WHITE))
        board.set_piece(8, 7, Piece(PieceType.KNIGHT, Owner.WHITE))
        board.set_piece(8, 8, Piece(PieceType.LANCE, Owner.WHITE))
        
        return position
