from typing import List, Tuple, Optional
from .piece import Piece, PieceType, Owner
from .position import Position

class MoveValidator:
    """Validates shogi moves"""
    
    @staticmethod
    def is_valid_move(position: Position, from_row: int, from_col: int, 
                     to_row: int, to_col: int, promotion: bool = False) -> bool:
        """
        Check if a move is legal
        
        Args:
            position: Current position
            from_row, from_col: Source position
            to_row, to_col: Destination position
            promotion: Whether to promote the piece
        
        Returns:
            True if move is legal, False otherwise
        """
        # Check positions are valid
        if not MoveValidator._is_valid_position(from_row, from_col):
            return False
        if not MoveValidator._is_valid_position(to_row, to_col):
            return False
        
        # Check source has a piece
        piece = position.board.get_piece(from_row, from_col)
        if piece is None:
            return False
        
        # Check it's the correct player's turn
        if piece.owner != position.turn:
            return False
        
        # Check destination is not occupied by own piece
        dest_piece = position.board.get_piece(to_row, to_col)
        if dest_piece and dest_piece.owner == piece.owner:
            return False
        
        # Check piece can move to destination
        if not MoveValidator._can_piece_move(position, piece, from_row, from_col, to_row, to_col):
            return False
        
        # Check move doesn't leave king in check (simplified - not implemented)
        # This would require full check detection
        
        return True
    
    @staticmethod
    def _can_piece_move(position: Position, piece: Piece, from_row: int, from_col: int,
                       to_row: int, to_col: int) -> bool:
        """Check if piece can move to destination based on piece type"""
        
        if piece.piece_type == PieceType.PAWN:
            return MoveValidator._can_pawn_move(piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.LANCE:
            return MoveValidator._can_lance_move(position, piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.KNIGHT:
            return MoveValidator._can_knight_move(piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.SILVER:
            return MoveValidator._can_silver_move(piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.GOLD:
            return MoveValidator._can_gold_move(piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.BISHOP:
            return MoveValidator._can_bishop_move(position, piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.ROOK:
            return MoveValidator._can_rook_move(position, piece, from_row, from_col, to_row, to_col)
        elif piece.piece_type == PieceType.KING:
            return MoveValidator._can_king_move(piece, from_row, from_col, to_row, to_col)
        
        return False
    
    @staticmethod
    def _can_pawn_move(piece: Piece, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Pawn moves one square forward"""
        if from_col != to_col:
            return False
        
        if piece.owner == Owner.BLACK:
            return to_row == from_row + 1
        else:
            return to_row == from_row - 1
    
    @staticmethod
    def _can_lance_move(position: Position, piece: Piece, from_row: int, from_col: int,
                       to_row: int, to_col: int) -> bool:
        """Lance moves any number of squares forward"""
        if from_col != to_col:
            return False
        
        if piece.owner == Owner.BLACK:
            if to_row <= from_row:
                return False
            # Check path is clear
            for row in range(from_row + 1, to_row):
                if position.board.get_piece(row, from_col) is not None:
                    return False
        else:
            if to_row >= from_row:
                return False
            # Check path is clear
            for row in range(to_row + 1, from_row):
                if position.board.get_piece(row, from_col) is not None:
                    return False
        
        return True
    
    @staticmethod
    def _can_knight_move(piece: Piece, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Knight moves in L-shape"""
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        if row_diff == 2 and col_diff == 1:
            if piece.owner == Owner.BLACK:
                return to_row > from_row
            else:
                return to_row < from_row
        
        return False
    
    @staticmethod
    def _can_silver_move(piece: Piece, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Silver moves diagonally forward or one square forward"""
        row_diff = to_row - from_row
        col_diff = abs(to_col - from_col)
        
        if piece.owner == Owner.BLACK:
            if row_diff <= 0:
                return False
            if row_diff == 1 and col_diff <= 1:
                return True
            if row_diff == 2 and col_diff == 0:
                return False
        else:
            if row_diff >= 0:
                return False
            if row_diff == -1 and col_diff <= 1:
                return True
        
        return False
    
    @staticmethod
    def _can_gold_move(piece: Piece, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """Gold moves one square in most directions"""
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        if row_diff > 1 or col_diff > 1:
            return False
        
        if row_diff == 0 and col_diff == 0:
            return False
        
        # Cannot move diagonally backward
        if piece.owner == Owner.BLACK:
            if to_row < from_row and col_diff == 1:
                return False
        else:
            if to_row > from_row and col_diff == 1:
                return False
        
        return True
    
    @staticmethod
    def _can_bishop_move(position: Position, piece: Piece, from_row: int, from_col: int,
                        to_row: int, to_col: int) -> bool:
        """Bishop moves diagonally"""
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        if row_diff != col_diff or row_diff == 0:
            return False
        
        # Check path is clear
        row_step = 1 if to_row > from_row else -1
        col_step = 1 if to_col > from_col else -1
        
        row, col = from_row + row_step, from_col + col_step
        while (row, col) != (to_row, to_col):
            if position.board.get_piece(row, col) is not None:
                return False
            row += row_step
            col += col_step
        
        return True
    
    @staticmethod
    def _can_rook_move(position: Position, piece: Piece, from_row: int, from_col: int,
                      to_row: int, to_col: int) -> bool:
        """Rook moves horizontally or vertically"""
        if from_row != to_row and from_col != to_col:
            return False
        
        if from_row == to_row and from_col == to_col:
            return False
        
        # Check path is clear
        if from_row == to_row:
            col_step = 1 if to_col > from_col else -1
            for col in range(from_col + col_step, to_col, col_step):
                if position.board.get_piece(from_row, col) is not None:
                    return False
        else:
            row_step = 1 if to_row > from_row else -1
            for row in range(from_row + row_step, to_row, row_step):
                if position.board.get_piece(row, from_col) is not None:
                    return False
        
        return True
    
    @staticmethod
    def _can_king_move(piece: Piece, from_row: int, from_col: int, to_row: int, to_col: int) -> bool:
        """King moves one square in any direction"""
        row_diff = abs(to_row - from_row)
        col_diff = abs(to_col - from_col)
        
        return row_diff <= 1 and col_diff <= 1 and (row_diff > 0 or col_diff > 0)
    
    @staticmethod
    def _is_valid_position(row: int, col: int) -> bool:
        """Check if position is on board"""
        return 0 <= row < 9 and 0 <= col < 9
