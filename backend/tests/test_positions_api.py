import pytest
import json
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

class TestPositionsAPI:
    """Test Positions API endpoints"""
    
    def test_create_position(self, client):
        """Test creating a position"""
        board_state = {
            'board': [[None for _ in range(9)] for _ in range(9)],
            'hands': {'black': {}, 'white': {}},
            'turn': 'black'
        }
        
        response = client.post('/api/positions', 
            json={
                'board_state': board_state,
                'turn': 'black'
            },
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'id' in data
        assert data['turn'] == 'black'
    
    def test_create_position_missing_board_state(self, client):
        """Test creating position without board_state"""
        response = client.post('/api/positions',
            json={'turn': 'black'},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_get_position(self, client, app):
        """Test getting a position"""
        with app.app_context():
            board_state = {'board': []}
            position = PositionModel(board_state=board_state, turn='black')
            db.session.add(position)
            db.session.commit()
            position_id = position.id
        
        response = client.get(f'/api/positions/{position_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == position_id
    
    def test_get_position_not_found(self, client):
        """Test getting non-existent position"""
        response = client.get('/api/positions/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_update_position(self, client, app):
        """Test updating a position"""
        with app.app_context():
            board_state = {'board': []}
            position = PositionModel(board_state=board_state, turn='black')
            db.session.add(position)
            db.session.commit()
            position_id = position.id
        
        response = client.put(f'/api/positions/{position_id}',
            json={'turn': 'white'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['turn'] == 'white'
    
    def test_delete_position(self, client, app):
        """Test deleting a position"""
        with app.app_context():
            board_state = {'board': []}
            position = PositionModel(board_state=board_state, turn='black')
            db.session.add(position)
            db.session.commit()
            position_id = position.id
        
        response = client.delete(f'/api/positions/{position_id}')
        
        assert response.status_code == 204
        
        # Verify it's deleted
        with app.app_context():
            deleted = PositionModel.query.get(position_id)
            assert deleted is None
    
    def test_delete_position_not_found(self, client):
        """Test deleting non-existent position"""
        response = client.delete('/api/positions/nonexistent')
        
        assert response.status_code == 404
