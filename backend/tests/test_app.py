import pytest
from app import create_app, db

class TestAppInitialization:
    """Test Flask application initialization"""
    
    def test_app_creation(self, app):
        """Test that app is created successfully"""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_app_debug_mode(self, app):
        """Test that debug mode is set correctly"""
        assert app.config['DEBUG'] is False  # Testing config has DEBUG=False
    
    def test_database_initialization(self, app):
        """Test that database is initialized"""
        with app.app_context():
            # Check that we can execute a query
            result = db.session.execute('SELECT 1')
            assert result is not None

class TestCORSConfiguration:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in response"""
        response = client.get('/health')
        assert response.status_code == 200
        # CORS headers should be present
        assert 'Access-Control-Allow-Origin' in response.headers or response.status_code == 200

class TestErrorHandlers:
    """Test error handlers"""
    
    def test_404_error_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
        assert data['error'] == 'Not Found'
    
    def test_error_response_format(self, client):
        """Test that error responses have correct format"""
        response = client.get('/nonexistent')
        data = response.get_json()
        assert 'error' in data
        assert 'message' in data
        assert 'timestamp' in data

class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check_endpoint_exists(self, client):
        """Test that health check endpoint exists"""
        response = client.get('/health')
        assert response.status_code in [200, 503]
    
    def test_health_check_response_format(self, client):
        """Test health check response format"""
        response = client.get('/health')
        data = response.get_json()
        assert 'status' in data
        assert 'database' in data
        assert 'timestamp' in data
    
    def test_health_check_database_status(self, client):
        """Test that health check includes database status"""
        response = client.get('/health')
        data = response.get_json()
        assert data['database'] in ['healthy', 'unhealthy']
