from flask import Blueprint, request, jsonify
from app import db
from models import Position as PositionModel
from shogi import Position, Owner
import uuid

positions_bp = Blueprint('positions', __name__, url_prefix='/api/positions')

@positions_bp.route('', methods=['POST'])
def create_position():
    """Create a new position"""
    try:
        data = request.get_json()
        
        if not data or 'board_state' not in data:
            return jsonify({'error': 'Bad Request', 'message': 'board_state is required'}), 400
        
        # Create position model
        position = PositionModel(
            board_state=data['board_state'],
            turn=data.get('turn', 'black'),
            metadata=data.get('metadata')
        )
        
        # Validate
        position.validate()
        
        # Save to database
        db.session.add(position)
        db.session.commit()
        
        return jsonify(position.to_dict()), 201
    
    except ValueError as e:
        return jsonify({'error': 'Unprocessable Entity', 'message': str(e)}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@positions_bp.route('/<position_id>', methods=['GET'])
def get_position(position_id):
    """Get a position by ID"""
    try:
        position = PositionModel.query.get(position_id)
        
        if not position:
            return jsonify({'error': 'Not Found', 'message': 'Position not found'}), 404
        
        return jsonify(position.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@positions_bp.route('/<position_id>', methods=['PUT'])
def update_position(position_id):
    """Update a position"""
    try:
        position = PositionModel.query.get(position_id)
        
        if not position:
            return jsonify({'error': 'Not Found', 'message': 'Position not found'}), 404
        
        data = request.get_json()
        
        if 'board_state' in data:
            position.board_state = data['board_state']
        if 'turn' in data:
            position.turn = data['turn']
        if 'metadata' in data:
            position.metadata = data['metadata']
        
        # Validate
        position.validate()
        
        db.session.commit()
        
        return jsonify(position.to_dict()), 200
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': 'Unprocessable Entity', 'message': str(e)}), 422
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@positions_bp.route('/<position_id>', methods=['DELETE'])
def delete_position(position_id):
    """Delete a position"""
    try:
        position = PositionModel.query.get(position_id)
        
        if not position:
            return jsonify({'error': 'Not Found', 'message': 'Position not found'}), 404
        
        db.session.delete(position)
        db.session.commit()
        
        return '', 204
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
