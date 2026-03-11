import pytest
from io import BytesIO
from app import create_app, db
from models import Kifu as KifuModel

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

class TestKifUploadAPI:
    """Test KIF upload API"""
    
    def test_upload_valid_kif(self, client):
        """Test uploading a valid KIF file"""
        kif_content = b"""開始日時：2024/01/01
先手：先手名
後手：後手名
手数----指手---------消費時間--
   1 ７六歩(77)   ( 0:00/00:00:00)
   2 ３四歩(33)   ( 0:00/00:00:00)
"""
        
        data = {
            'file': (BytesIO(kif_content), 'test.kif')
        }
        
        response = client.post('/api/kif/upload', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 201
        result = response.get_json()
        assert 'id' in result
        assert 'metadata' in result
        assert 'moves' in result
        assert len(result['moves']) == 2
    
    def test_upload_no_file(self, client):
        """Test uploading without file"""
        response = client.post('/api/kif/upload', content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type"""
        data = {
            'file': (BytesIO(b'content'), 'test.txt')
        }
        
        response = client.post('/api/kif/upload', data=data, content_type='multipart/form-data')
        
        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result
    
    def test_upload_invalid_kif_format(self, client):
        """Test uploading invalid KIF format"""
        data = {
            'file': (BytesIO(b'This is not a valid KIF file'), 'test.kif')
        }
        
        response = client.post('/api/kif/upload', data=data, content_type='multipart/form-data')
        
        # Should still accept but may have no moves
        assert response.status_code in [201, 422]
    
    def test_get_kifu(self, client, app):
        """Test getting a kifu"""
        with app.app_context():
            kifu = KifuModel(black_player='A', white_player='B')
            db.session.add(kifu)
            db.session.commit()
            kifu_id = kifu.id
        
        response = client.get(f'/api/kif/{kifu_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == kifu_id
    
    def test_get_kifu_not_found(self, client):
        """Test getting non-existent kifu"""
        response = client.get('/api/kif/nonexistent')
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
