import re
import chardet
from typing import List, Dict, Optional, Tuple
from .position import Position
from .piece import PieceType, Owner

class KifParseError(Exception):
    """Exception raised when KIF parsing fails"""
    pass

class KifParser:
    """Parser for KIF (Kifu) format files"""
    
    # Regex patterns for KIF format
    METADATA_PATTERN = r'^([^：]+)：(.+)$'
    MOVE_PATTERN = r'^\s*(\d+)\s+(.+?)(?:\((\d+)\))?(?:\s*(.*))?$'
    
    # Piece name mappings (Japanese to English)
    PIECE_NAMES_JP = {
        '歩': 'pawn',
        '香': 'lance',
        '桂': 'knight',
        '銀': 'silver',
        '金': 'gold',
        '角': 'bishop',
        '飛': 'rook',
        '玉': 'king',
        '王': 'king',
    }
    
    # Promoted piece names
    PROMOTED_NAMES_JP = {
        'と': 'pawn',
        '成香': 'lance',
        '成桂': 'knight',
        '成銀': 'silver',
        '馬': 'bishop',
        '龍': 'rook',
    }
    
    @staticmethod
    def parse_file(file_content: str) -> Dict:
        """
        Parse KIF file content
        
        Args:
            file_content: Raw file content as string
            
        Returns:
            Dictionary with metadata and moves
            
        Raises:
            KifParseError: If parsing fails
        """
        try:
            # Convert to bytes if needed for encoding detection
            if isinstance(file_content, str):
                # Already decoded, use as-is
                content = file_content
            else:
                # Try to detect encoding
                content = None
                detected = chardet.detect(file_content)

                # Try detected encoding first
                if detected and detected.get('encoding'):
                    try:
                        content = file_content.decode(detected['encoding'], errors='strict')
                    except (UnicodeDecodeError, LookupError, TypeError):
                        pass

                # Try shift_jis (common for Japanese KIF files)
                if content is None:
                    try:
                        content = file_content.decode('shift_jis', errors='strict')
                    except UnicodeDecodeError:
                        pass

                # Try utf-8
                if content is None:
                    try:
                        content = file_content.decode('utf-8', errors='strict')
                    except UnicodeDecodeError:
                        pass

                # Last resort: shift_jis with error replacement
                if content is None:
                    content = file_content.decode('shift_jis', errors='replace')
            
            lines = content.split('\n')
            
            # Parse metadata
            metadata = KifParser._parse_metadata(lines)
            
            # Parse moves
            moves = KifParser._parse_moves(lines)
            
            return {
                'metadata': metadata,
                'moves': moves
            }
        
        except Exception as e:
            raise KifParseError(f'Failed to parse KIF file: {str(e)}')
    
    @staticmethod
    def _parse_metadata(lines: List[str]) -> Dict:
        """Parse metadata section of KIF file"""
        metadata = {
            'black_player': None,
            'white_player': None,
            'game_date': None,
            'result': None,
        }
        
        for line in lines:
            if not line.strip() or line.startswith('手数'):
                break
            
            match = re.match(KifParser.METADATA_PATTERN, line)
            if match:
                key, value = match.groups()
                key = key.strip()
                value = value.strip()
                
                if key == '先手':
                    metadata['black_player'] = value
                elif key == '後手':
                    metadata['white_player'] = value
                elif key == '開始日時':
                    metadata['game_date'] = value
                elif key == '棋戦':
                    metadata['event'] = value
                elif key == '結果':
                    metadata['result'] = value
        
        return metadata
    
    @staticmethod
    def _parse_moves(lines: List[str]) -> List[Dict]:
        """Parse moves section of KIF file"""
        moves = []
        move_number = 0
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and metadata
            if not line or '：' in line:
                continue
            
            # Skip header line
            if '手数' in line:
                continue
            
            # Parse move line
            match = re.match(KifParser.MOVE_PATTERN, line)
            if match:
                move_num_str, notation, time_str, comment = match.groups()
                
                try:
                    move_num = int(move_num_str)
                    
                    # Parse notation
                    move_data = KifParser._parse_notation(notation, move_num)
                    
                    if move_data:
                        move_data['comment'] = comment.strip() if comment else None
                        moves.append(move_data)
                
                except ValueError as e:
                    raise KifParseError(f'Invalid move at line {move_num_str}: {str(e)}')
        
        return moves
    
    @staticmethod
    def _parse_notation(notation: str, move_number: int) -> Optional[Dict]:
        """
        Parse move notation
        
        Format: 7六歩(77) or 7六歩 or 投了
        """
        notation = notation.strip()
        
        # Handle special moves
        if notation in ['投了', '中断', '中止']:
            return None
        
        # Extract destination square and piece type
        # Format: [destination][piece_name]
        match = re.match(r'^(\d)(\d)(.+?)(?:\((\d)(\d)\))?$', notation)
        
        if not match:
            return None
        
        to_col_str, to_row_str, piece_notation, from_col_str, from_row_str = match.groups()
        
        to_col = int(to_col_str) - 1  # Convert to 0-indexed
        to_row = int(to_row_str) - 1
        
        # Parse piece type and promotion
        piece_type, promoted = KifParser._parse_piece_notation(piece_notation)
        
        if not piece_type:
            return None
        
        from_col = int(from_col_str) - 1 if from_col_str else None
        from_row = int(from_row_str) - 1 if from_row_str else None
        
        return {
            'move_number': move_number,
            'notation': notation,
            'from_square': f'{from_col_str}{from_row_str}' if from_col_str else None,
            'to_square': f'{to_col_str}{to_row_str}',
            'piece_type': piece_type,
            'is_promotion': promoted,
            'is_drop': from_col is None and from_row is None,
        }
    
    @staticmethod
    def _parse_piece_notation(notation: str) -> Tuple[Optional[str], bool]:
        """
        Parse piece notation
        
        Returns:
            Tuple of (piece_type, is_promoted)
        """
        notation = notation.strip()
        
        # Check for promoted pieces
        for jp_name, piece_type in KifParser.PROMOTED_NAMES_JP.items():
            if notation.startswith(jp_name):
                return piece_type, True
        
        # Check for regular pieces
        for jp_name, piece_type in KifParser.PIECE_NAMES_JP.items():
            if notation.startswith(jp_name):
                # Check if promotion is indicated
                promoted = '成' in notation or notation.endswith('成')
                return piece_type, promoted
        
        return None, False
    
    @staticmethod
    def validate_moves(moves: List[Dict]) -> bool:
        """
        Validate move sequence
        
        Args:
            moves: List of move dictionaries
            
        Returns:
            True if all moves are valid
            
        Raises:
            KifParseError: If validation fails
        """
        if not moves:
            return True
        
        # Check move numbers are sequential
        for i, move in enumerate(moves):
            expected_num = i + 1
            if move['move_number'] != expected_num:
                raise KifParseError(
                    f'Move number mismatch at position {i}: '
                    f'expected {expected_num}, got {move["move_number"]}'
                )
        
        return True
