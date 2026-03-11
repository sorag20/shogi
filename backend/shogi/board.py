from typing import Optional, List, Tuple
from .piece import Piece, PieceType, Owner

class Board:
    """Represents a 9x9 shogi board"""
    
    BOARD_SIZE = 9
    
    def __init__(self):
        """Initialize an empty board"""
        self.board = [[None for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
    
    def __repr__(self):
        return f'<Board {self.BOARD_SIZE}x{self.BOARD_SIZE}>'
    
    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Get piece at position"""
        if not self._is_valid_position(row, col):
            raise ValueError(f'Invalid position: ({row}, {col})')
        return self.board[row][col]
    
    def set_piece(self, row: int, col: int, piece: Optional[Piece]) -> None:
        """Set piece at position"""
        if not self._is_valid_position(row, col):
            raise ValueError(f'Invalid position: ({row}, {col})')
        self.board[row][col] = piece
    
    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> Optional[Piece]:
        """Move piece from one position to another, return captured piece if any"""
        if not self._is_valid_position(from_row, from_col):
            raise ValueError(f'Invalid from position: ({from_row}, {from_col})')
        if not self._is_valid_position(to_row, to_col):
            raise ValueError(f'Invalid to position: ({to_row}, {to_col})')
        
        piece = self.get_piece(from_row, from_col)
        if piece is None:
            raise ValueError(f'No piece at ({from_row}, {from_col})')
        
        # Get captured piece
        captured = self.get_piece(to_row, to_col)
        
        # Move piece
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)
        
        return captured
    
    def add_piece(self, row: int, col: int, piece: Piece) -> None:
        """Add piece at position"""
        if not self._is_valid_position(row, col):
            raise ValueError(f'Invalid position: ({row}, {col})')
        if self.get_piece(row, col) is not None:
            raise ValueError(f'Position ({row}, {col}) is already occupied')
        self.set_piece(row, col, piece)
    
    def remove_piece(self, row: int, col: int) -> Optional[Piece]:
        """Remove piece at position"""
        if not self._is_valid_position(row, col):
            raise ValueError(f'Invalid position: ({row}, {col})')
        piece = self.get_piece(row, col)
        self.set_piece(row, col, None)
        return piece
    
    def find_king(self, owner: Owner) -> Optional[Tuple[int, int]]:
        """Find king position for given owner"""
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                piece = self.get_piece(row, col)
                if piece and piece.piece_type == PieceType.KING and piece.owner == owner:
                    return (row, col)
        return None
    
    def to_dict(self) -> List[List]:
        """Convert board to dictionary"""
        return [[piece.to_dict() if piece else None for piece in row] for row in self.board]
    
    @staticmethod
    def from_dict(data: List[List]) -> 'Board':
        """Create board from dictionary"""
        board = Board()
        for row in range(Board.BOARD_SIZE):
            for col in range(Board.BOARD_SIZE):
                piece_data = data[row][col]
                if piece_data:
                    board.set_piece(row, col, Piece.from_dict(piece_data))
        return board
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is valid"""
        return 0 <= row < self.BOARD_SIZE and 0 <= col < self.BOARD_SIZE
    
    def get_all_pieces(self, owner: Owner) -> List[Tuple[int, int, Piece]]:
        """Get all pieces for given owner"""
        pieces = []
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                piece = self.get_piece(row, col)
                if piece and piece.owner == owner:
                    pieces.append((row, col, piece))
        return pieces
