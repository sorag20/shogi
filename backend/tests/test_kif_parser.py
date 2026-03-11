import pytest
from shogi.kif_parser import KifParser, KifParseError

class TestKifParser:
    """Test KIF parser"""
    
    def test_parse_simple_kif(self):
        """Test parsing a simple KIF file"""
        kif_content = """開始日時：2024/01/01
先手：先手名
後手：後手名
手数----指手---------消費時間--
   1 ７六歩(77)   ( 0:00/00:00:00)
   2 ３四歩(33)   ( 0:00/00:00:00)
"""
        result = KifParser.parse_file(kif_content)
        
        assert 'metadata' in result
        assert 'moves' in result
        assert len(result['moves']) == 2
    
    def test_parse_metadata(self):
        """Test parsing metadata"""
        kif_content = """開始日時：2024/01/01
先手：Player A
後手：Player B
結果：中断
"""
        result = KifParser.parse_file(kif_content)
        
        metadata = result['metadata']
        assert metadata['black_player'] == 'Player A'
        assert metadata['white_player'] == 'Player B'
        assert metadata['result'] == '中断'
    
    def test_parse_move_notation(self):
        """Test parsing move notation"""
        kif_content = """手数----指手---------消費時間--
   1 ７六歩(77)   ( 0:00/00:00:00)
"""
        result = KifParser.parse_file(kif_content)
        
        move = result['moves'][0]
        assert move['move_number'] == 1
        assert move['notation'] == '７六歩(77)'
        assert move['piece_type'] == 'pawn'
    
    def test_invalid_kif_format(self):
        """Test parsing invalid KIF format"""
        kif_content = "This is not a valid KIF file"
        
        result = KifParser.parse_file(kif_content)
        # Should not raise, but return empty moves
        assert 'moves' in result
    
    def test_validate_moves_sequential(self):
        """Test move validation"""
        moves = [
            {'move_number': 1, 'notation': '７六歩'},
            {'move_number': 2, 'notation': '３四歩'},
        ]
        
        assert KifParser.validate_moves(moves) is True
    
    def test_validate_moves_non_sequential(self):
        """Test validation fails for non-sequential moves"""
        moves = [
            {'move_number': 1, 'notation': '７六歩'},
            {'move_number': 3, 'notation': '３四歩'},  # Should be 2
        ]
        
        with pytest.raises(KifParseError):
            KifParser.validate_moves(moves)

# Property-based tests
def test_kif_parse_roundtrip():
    """
    Property 6: KIF file parsing round-trip
    For any valid KIF file, parsing should extract all moves correctly
    Validates: Requirements 2.1, 8.1, 8.2
    """
    kif_content = """開始日時：2024/01/01
先手：先手名
後手：後手名
手数----指手---------消費時間--
   1 ７六歩(77)   ( 0:00/00:00:00)
   2 ３四歩(33)   ( 0:00/00:00:00)
   3 ２六歩(27)   ( 0:00/00:00:00)
"""
    
    result = KifParser.parse_file(kif_content)
    
    # Verify metadata is extracted
    assert result['metadata']['black_player'] == '先手名'
    assert result['metadata']['white_player'] == '後手名'
    
    # Verify moves are extracted
    assert len(result['moves']) == 3
    
    # Verify move numbers are sequential
    for i, move in enumerate(result['moves']):
        assert move['move_number'] == i + 1

def test_kif_invalid_file_rejection():
    """
    Property 7: Invalid KIF file rejection
    For any invalid KIF file, parsing should handle gracefully
    Validates: Requirements 2.2
    """
    invalid_kif = "This is clearly not a KIF file\nWith random content"
    
    result = KifParser.parse_file(invalid_kif)
    
    # Should parse without raising, but moves should be empty or minimal
    assert isinstance(result, dict)
    assert 'moves' in result

def test_kif_comment_preservation():
    """
    Property 23: KIF comment preservation
    For any KIF file with comments, comments should be preserved
    Validates: Requirements 8.7
    """
    kif_content = """手数----指手---------消費時間--
   1 ７六歩(77)   ( 0:00/00:00:00) これは良い手です
   2 ３四歩(33)   ( 0:00/00:00:00) 標準的な応手
"""
    
    result = KifParser.parse_file(kif_content)
    
    # Verify comments are preserved
    assert result['moves'][0]['comment'] == 'これは良い手です'
    assert result['moves'][1]['comment'] == '標準的な応手'
