from enum import Enum
from typing import Optional

class PieceType(Enum):
    """Shogi piece types"""
    PAWN = 'pawn'
    LANCE = 'lance'
    KNIGHT = 'knight'
    SILVER = 'silver'
    GOLD = 'gold'
    BISHOP = 'bishop'
    ROOK = 'rook'
    KING = 'king'

class Owner(Enum):
    """Piece owner (player)"""
    BLACK = 'black'
    WHITE = 'white'

class Piece:
    """Represents a single shogi piece"""
    
    def __init__(self, piece_type: PieceType, owner: Owner, promoted: bool = False):
        self.piece_type = piece_type
        self.owner = owner
        self.promoted = promoted
    
    def __repr__(self):
        promoted_str = '+' if self.promoted else ''
        return f'{promoted_str}{self.piece_type.value}({self.owner.value[0]})'
    
    def __eq__(self, other):
        if not isinstance(other, Piece):
            return False
        return (self.piece_type == other.piece_type and 
                self.owner == other.owner and 
                self.promoted == other.promoted)
    
    def to_dict(self):
        """Convert piece to dictionary"""
        return {
            'type': self.piece_type.value,
            'owner': self.owner.value,
            'promoted': self.promoted
        }
    
    @staticmethod
    def from_dict(data):
        """Create piece from dictionary"""
        if data is None:
            return None
        return Piece(
            piece_type=PieceType(data['type']),
            owner=Owner(data['owner']),
            promoted=data.get('promoted', False)
        )
    
    def can_promote(self):
        """Check if piece can be promoted"""
        if self.promoted:
            return False
        # King cannot be promoted
        if self.piece_type == PieceType.KING:
            return False
        return True
    
    def promote(self):
        """Promote the piece"""
        if self.can_promote():
            self.promoted = True
            return True
        return False
    
    def unpromote(self):
        """Unpromote the piece"""
        if self.promoted:
            self.promoted = False
            return True
        return False
