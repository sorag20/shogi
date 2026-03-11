import pytest
from datetime import datetime, date
from app import db
from models import Position, Kifu, Move

class TestPositionModel:
    """Test Position model"""
    
    def test_position_creation(self, app):
        """Test creating a position"""
        with app.app_context():
            board_state = {
                'board': [[None for _ in range(9)] for _ in range(9)],
                'hands': {'black': {}, 'white': {}},
                'turn': 'black'
            }
            position = Position(board_state=board_state, turn='black')
            db.session.add(position)
            db.session.commit()
            
            assert position.id is not None
            assert position.board_state == board_state
            assert position.turn == 'black'
    
    def test_position_to_dict(self, app):
        """Test position to_dict method"""
        with app.app_context():
            board_state = {'board': []}
            position = Position(board_state=board_state, turn='white')
            db.session.add(position)
            db.session.commit()
            
            pos_dict = position.to_dict()
            assert pos_dict['id'] == position.id
            assert pos_dict['board_state'] == board_state
            assert pos_dict['turn'] == 'white'
            assert 'created_at' in pos_dict
            assert 'updated_at' in pos_dict
    
    def test_position_from_dict(self, app):
        """Test creating position from dictionary"""
        with app.app_context():
            data = {
                'board_state': {'board': []},
                'turn': 'black',
                'metadata': {'test': 'value'}
            }
            position = Position.from_dict(data)
            
            assert position.board_state == data['board_state']
            assert position.turn == data['turn']
            assert position.metadata == data['metadata']
    
    def test_position_validation_success(self, app):
        """Test position validation succeeds"""
        with app.app_context():
            position = Position(board_state={'board': []}, turn='black')
            assert position.validate() is True
    
    def test_position_validation_missing_board_state(self, app):
        """Test position validation fails without board_state"""
        with app.app_context():
            position = Position(turn='black')
            with pytest.raises(ValueError):
                position.validate()
    
    def test_position_validation_invalid_turn(self, app):
        """Test position validation fails with invalid turn"""
        with app.app_context():
            position = Position(board_state={'board': []}, turn='invalid')
            with pytest.raises(ValueError):
                position.validate()

class TestKifuModel:
    """Test Kifu model"""
    
    def test_kifu_creation(self, app):
        """Test creating a kifu"""
        with app.app_context():
            kifu = Kifu(
                black_player='Player A',
                white_player='Player B',
                game_date=date(2024, 1, 1),
                result='Black wins'
            )
            db.session.add(kifu)
            db.session.commit()
            
            assert kifu.id is not None
            assert kifu.black_player == 'Player A'
            assert kifu.white_player == 'Player B'
    
    def test_kifu_to_dict(self, app):
        """Test kifu to_dict method"""
        with app.app_context():
            kifu = Kifu(black_player='A', white_player='B')
            db.session.add(kifu)
            db.session.commit()
            
            kifu_dict = kifu.to_dict()
            assert kifu_dict['id'] == kifu.id
            assert kifu_dict['black_player'] == 'A'
            assert kifu_dict['white_player'] == 'B'
    
    def test_kifu_from_dict(self, app):
        """Test creating kifu from dictionary"""
        with app.app_context():
            data = {
                'black_player': 'Player A',
                'white_player': 'Player B',
                'result': 'Draw'
            }
            kifu = Kifu.from_dict(data)
            
            assert kifu.black_player == data['black_player']
            assert kifu.white_player == data['white_player']
            assert kifu.result == data['result']
    
    def test_kifu_validation(self, app):
        """Test kifu validation"""
        with app.app_context():
            kifu = Kifu()
            assert kifu.validate() is True

class TestMoveModel:
    """Test Move model"""
    
    def test_move_creation(self, app):
        """Test creating a move"""
        with app.app_context():
            kifu = Kifu(black_player='A', white_player='B')
            db.session.add(kifu)
            db.session.commit()
            
            move = Move(
                kifu_id=kifu.id,
                move_number=1,
                notation='7六歩',
                from_square='7g',
                to_square='7f',
                piece_type='pawn'
            )
            db.session.add(move)
            db.session.commit()
            
            assert move.id is not None
            assert move.kifu_id == kifu.id
            assert move.move_number == 1
    
    def test_move_to_dict(self, app):
        """Test move to_dict method"""
        with app.app_context():
            kifu = Kifu()
            db.session.add(kifu)
            db.session.commit()
            
            move = Move(
                kifu_id=kifu.id,
                move_number=1,
                notation='7六歩'
            )
            db.session.add(move)
            db.session.commit()
            
            move_dict = move.to_dict()
            assert move_dict['id'] == move.id
            assert move_dict['move_number'] == 1
            assert move_dict['notation'] == '7六歩'
    
    def test_move_from_dict(self, app):
        """Test creating move from dictionary"""
        with app.app_context():
            kifu = Kifu()
            db.session.add(kifu)
            db.session.commit()
            
            data = {
                'kifu_id': kifu.id,
                'move_number': 1,
                'notation': '7六歩',
                'is_promotion': False
            }
            move = Move.from_dict(data)
            
            assert move.kifu_id == data['kifu_id']
            assert move.move_number == data['move_number']
            assert move.notation == data['notation']
    
    def test_move_validation_success(self, app):
        """Test move validation succeeds"""
        with app.app_context():
            kifu = Kifu()
            db.session.add(kifu)
            db.session.commit()
            
            move = Move(
                kifu_id=kifu.id,
                move_number=1,
                notation='7六歩'
            )
            assert move.validate() is True
    
    def test_move_validation_missing_kifu_id(self, app):
        """Test move validation fails without kifu_id"""
        with app.app_context():
            move = Move(move_number=1, notation='7六歩')
            with pytest.raises(ValueError):
                move.validate()
    
    def test_move_validation_invalid_move_number(self, app):
        """Test move validation fails with invalid move_number"""
        with app.app_context():
            kifu = Kifu()
            db.session.add(kifu)
            db.session.commit()
            
            move = Move(kifu_id=kifu.id, move_number=0, notation='7六歩')
            with pytest.raises(ValueError):
                move.validate()
    
    def test_kifu_move_relationship(self, app):
        """Test relationship between Kifu and Move"""
        with app.app_context():
            kifu = Kifu(black_player='A', white_player='B')
            db.session.add(kifu)
            db.session.commit()
            
            move1 = Move(kifu_id=kifu.id, move_number=1, notation='7六歩')
            move2 = Move(kifu_id=kifu.id, move_number=2, notation='3四歩')
            db.session.add_all([move1, move2])
            db.session.commit()
            
            # Refresh to load relationship
            db.session.refresh(kifu)
            assert len(kifu.moves) == 2
            assert kifu.moves[0].move_number == 1
            assert kifu.moves[1].move_number == 2
