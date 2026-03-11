import pytest
from hypothesis import given, strategies as st
from shogi.board import Board
from shogi.piece import Piece, PieceType, Owner

class TestBoard:
    """Test Board model"""
    
    def test_board_creation(self):
        """Test creating a board"""
        board = Board()
        assert board.BOARD_SIZE == 9
        # All positions should be empty
        for row in range(9):
            for col in range(9):
                assert board.get_piece(row, col) is None
    
    def test_add_piece(self):
        """Test adding a piece"""
        board = Board()
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        board.add_piece(0, 0, piece)
        
        assert board.get_piece(0, 0) == piece
    
    def test_remove_piece(self):
        """Test removing a piece"""
        board = Board()
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        board.add_piece(0, 0, piece)
        
        removed = board.remove_piece(0, 0)
        assert removed == piece
        assert board.get_piece(0, 0) is None
    
    def test_move_piece(self):
        """Test moving a piece"""
        board = Board()
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        board.add_piece(0, 0, piece)
        
        captured = board.move_piece(0, 0, 1, 0)
        assert board.get_piece(1, 0) == piece
        assert board.get_piece(0, 0) is None
        assert captured is None
    
    def test_move_piece_with_capture(self):
        """Test moving a piece with capture"""
        board = Board()
        piece1 = Piece(PieceType.PAWN, Owner.BLACK)
        piece2 = Piece(PieceType.PAWN, Owner.WHITE)
        
        board.add_piece(0, 0, piece1)
        board.add_piece(1, 0, piece2)
        
        captured = board.move_piece(0, 0, 1, 0)
        assert board.get_piece(1, 0) == piece1
        assert captured == piece2
    
    def test_find_king(self):
        """Test finding king"""
        board = Board()
        king = Piece(PieceType.KING, Owner.BLACK)
        board.add_piece(4, 4, king)
        
        pos = board.find_king(Owner.BLACK)
        assert pos == (4, 4)
    
    def test_board_to_dict(self):
        """Test board to_dict"""
        board = Board()
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        board.add_piece(0, 0, piece)
        
        data = board.to_dict()
        assert data[0][0] == piece.to_dict()
    
    def test_board_from_dict(self):
        """Test board from_dict"""
        board1 = Board()
        piece = Piece(PieceType.PAWN, Owner.BLACK)
        board1.add_piece(0, 0, piece)
        
        data = board1.to_dict()
        board2 = Board.from_dict(data)
        
        assert board2.get_piece(0, 0) == piece

# Property-based tests
@given(
    row=st.integers(min_value=0, max_value=8),
    col=st.integers(min_value=0, max_value=8)
)
def test_piece_addition_and_removal(row, col):
    """
    Property 3: Piece addition and removal
    For any position, adding a piece and then removing it should restore empty state
    Validates: Requirements 1.5
    """
    board = Board()
    piece = Piece(PieceType.PAWN, Owner.BLACK)
    
    board.add_piece(row, col, piece)
    assert board.get_piece(row, col) == piece
    
    removed = board.remove_piece(row, col)
    assert removed == piece
    assert board.get_piece(row, col) is None

@given(
    from_row=st.integers(min_value=0, max_value=8),
    from_col=st.integers(min_value=0, max_value=8),
    to_row=st.integers(min_value=0, max_value=8),
    to_col=st.integers(min_value=0, max_value=8)
)
def test_piece_movement(from_row, from_col, to_row, to_col):
    """
    Property 1: Piece movement
    For any valid positions, moving a piece should place it at destination
    Validates: Requirements 1.3, 1.4
    """
    if (from_row, from_col) == (to_row, to_col):
        pytest.skip("Source and destination are the same")
    
    board = Board()
    piece = Piece(PieceType.PAWN, Owner.BLACK)
    board.add_piece(from_row, from_col, piece)
    
    board.move_piece(from_row, from_col, to_row, to_col)
    
    assert board.get_piece(to_row, to_col) == piece
    assert board.get_piece(from_row, from_col) is None

@given(st.data())
def test_board_serialization_roundtrip(data):
    """
    Property 5: Board serialization round-trip
    For any board state, serializing and deserializing should produce equivalent board
    Validates: Requirements 1.7, 4.1, 4.3, 4.5
    """
    board1 = Board()
    
    # Add some random pieces
    positions = data.draw(st.lists(
        st.tuples(
            st.integers(0, 8),
            st.integers(0, 8),
            st.sampled_from(list(PieceType)),
            st.sampled_from(list(Owner))
        ),
        unique_by=lambda x: (x[0], x[1]),
        max_size=5
    ))
    
    for row, col, piece_type, owner in positions:
        try:
            board1.add_piece(row, col, Piece(piece_type, owner))
        except ValueError:
            pass  # Position already occupied
    
    # Serialize and deserialize
    data_dict = board1.to_dict()
    board2 = Board.from_dict(data_dict)
    
    # Verify all pieces are preserved
    for row in range(9):
        for col in range(9):
            piece1 = board1.get_piece(row, col)
            piece2 = board2.get_piece(row, col)
            assert piece1 == piece2
