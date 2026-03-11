import pytest
from hypothesis import given, strategies as st
from shogi.piece import Piece, PieceType, Owner

class TestPiece:
    """Test Piece model"""
    
    def test_piece_creation(self):
        """Test creating a piece"""
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        assert piece.piece_type == PieceType.PAWN
        assert piece.owner == Owner.BLACK
        assert piece.promoted is False
    
    def test_piece_equality(self):
        """Test piece equality"""
        piece1 = Piece(PieceType.PAWN, Owner.BLACK)
        piece2 = Piece(PieceType.PAWN, Owner.BLACK)
        piece3 = Piece(PieceType.PAWN, Owner.WHITE)
        
        assert piece1 == piece2
        assert piece1 != piece3
    
    def test_piece_to_dict(self):
        """Test piece to_dict"""
        piece = Piece(PieceType.PAWN, Owner.BLACK, promoted=True)
        data = piece.to_dict()
        
        assert data['type'] == 'pawn'
        assert data['owner'] == 'black'
        assert data['promoted'] is True
    
    def test_piece_from_dict(self):
        """Test piece from_dict"""
        data = {'type': 'pawn', 'owner': 'black', 'promoted': True}
        piece = Piece.from_dict(data)
        
        assert piece.piece_type == PieceType.PAWN
        assert piece.owner == Owner.BLACK
        assert piece.promoted is True
    
    def test_piece_promotion(self):
        """Test piece promotion"""
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        assert piece.can_promote() is True
        assert piece.promote() is True
        assert piece.promoted is True
        assert piece.can_promote() is False
    
    def test_king_cannot_promote(self):
        """Test that king cannot be promoted"""
        piece = Piece(PieceType.KING, Owner.BLACK)
        assert piece.can_promote() is False
        assert piece.promote() is False

# Property-based tests
@given(
    piece_type=st.sampled_from(list(PieceType)),
    owner=st.sampled_from(list(Owner)),
    promoted=st.booleans()
)
def test_piece_serialization_roundtrip(piece_type, owner, promoted):
    """
    Property 1: Piece serialization round-trip
    For any piece, serializing and deserializing should produce an equivalent piece
    Validates: Requirements 1.2, 1.3, 1.5, 1.6
    """
    piece = Piece(piece_type, owner, promoted)
    data = piece.to_dict()
    restored = Piece.from_dict(data)
    
    assert restored == piece
    assert restored.piece_type == piece.piece_type
    assert restored.owner == piece.owner
    assert restored.promoted == piece.promoted

@given(st.sampled_from(list(PieceType)))
def test_piece_promotion_idempotence(piece_type):
    """
    Property 4: Piece promotion state toggle
    For any promotable piece, toggling promotion state should work correctly
    Validates: Requirements 1.6
    """
    if piece_type == PieceType.KING:
        pytest.skip("King cannot be promoted")
    
    piece = Piece(piece_type, Owner.BLACK)
    original_promoted = piece.promoted
    
    # Toggle promotion
    piece.promote()
    assert piece.promoted is True
    
    # Toggle back
    piece.unpromote()
    assert piece.promoted == original_promoted
