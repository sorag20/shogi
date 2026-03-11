import pytest
from hypothesis import given, strategies as st
from app import create_app, db
from models import Position as PositionModel

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

class TestPositionPersistence:
    """Test position persistence"""
    
    def test_position_save_and_retrieve(self, app):
        """Test saving and retrieving a position"""
        with app.app_context():
            board_state = {'board': []}
            position = PositionModel(board_state=board_state, turn='black')
            db.session.add(position)
            db.session.commit()
            position_id = position.id
            
            # Retrieve
            retrieved = PositionModel.query.get(position_id)
            assert retrieved is not None
            assert retrieved.board_state == board_state
            assert retrieved.turn == 'black'
    
    def test_position_update_persistence(self, app):
        """Test updating and persisting a position"""
        with app.app_context():
            board_state = {'board': []}
            position = PositionModel(board_state=board_state, turn='black')
            db.session.add(position)
            db.session.commit()
            position_id = position.id
            
            # Update
            position.turn = 'white'
            db.session.commit()
            
            # Retrieve and verify
            retrieved = PositionModel.query.get(position_id)
            assert retrieved.turn == 'white'

# Property-based tests
@given(
    turn=st.sampled_from(['black', 'white']),
    metadata=st.just({'test': 'value'})
)
def test_position_roundtrip_persistence(turn, metadata):
    """
    Property 5: Position persistence round-trip
    For any position, saving and retrieving should produce equivalent position
    Validates: Requirements 1.7, 4.1, 4.3, 4.5
    """
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Create and save
        board_state = {'board': []}
        original = PositionModel(board_state=board_state, turn=turn, metadata=metadata)
        db.session.add(original)
        db.session.commit()
        original_id = original.id
        
        # Retrieve
        retrieved = PositionModel.query.get(original_id)
        
        # Verify
        assert retrieved is not None
        assert retrieved.board_state == original.board_state
        assert retrieved.turn == original.turn
        assert retrieved.metadata == original.metadata
        
        db.session.remove()
        db.drop_all()
