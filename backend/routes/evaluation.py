from flask import Blueprint, request, jsonify
import requests
import os
from datetime import datetime

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api')

AI_ENGINE_URL = os.getenv('AI_ENGINE_URL', 'http://localhost:8000')
AI_ENGINE_TIMEOUT = int(os.getenv('AI_ENGINE_TIMEOUT', '10'))

@evaluation_bp.route('/evaluate', methods=['POST'])
def evaluate():
    """Get evaluation for a position"""
    try:
        data = request.get_json()
        
        if not data or 'position' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'position is required'}), 400
        
        position = data['position']
        
        # Call AI engine
        try:
            response = requests.post(
                f'{AI_ENGINE_URL}/evaluate',
                json={'position': position},
                timeout=AI_ENGINE_TIMEOUT
            )
            
            if response.status_code != 200:
                return jsonify({
                    'error': 'Service Unavailable',
                    'message': 'AI Engine returned error'
                }), 503
            
            ai_result = response.json()
            
            return jsonify({
                'evaluation': ai_result.get('evaluation'),
                'best_move': ai_result.get('best_move'),
                'pv': ai_result.get('pv'),
                'computed_at': datetime.utcnow().isoformat()
            }), 200
        
        except requests.exceptions.Timeout:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'AI Engine timeout'
            }), 503
        except requests.exceptions.ConnectionError:
            return jsonify({
                'error': 'Service Unavailable',
                'message': 'Cannot connect to AI Engine'
            }), 503
    
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@evaluation_bp.route('/ai-status', methods=['GET'])
def ai_status():
    """Check AI engine status"""
    try:
        response = requests.get(
            f'{AI_ENGINE_URL}/health',
            timeout=5
        )
        
        if response.status_code == 200:
            return jsonify({'status': 'healthy'}), 200
        else:
            return jsonify({'status': 'unhealthy'}), 503
    
    except:
        return jsonify({'status': 'unavailable'}), 503
