from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from app import db
from models import User
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'No data provided'}), 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Validation
        if not username:
            return jsonify({'error': 'Bad Request', 'message': 'Username is required'}), 400

        if len(username) < 3:
            return jsonify({'error': 'Bad Request', 'message': 'Username must be at least 3 characters'}), 400

        if not email:
            return jsonify({'error': 'Bad Request', 'message': 'Email is required'}), 400

        if not validate_email(email):
            return jsonify({'error': 'Bad Request', 'message': 'Invalid email format'}), 400

        if not password:
            return jsonify({'error': 'Bad Request', 'message': 'Password is required'}), 400

        valid, error_msg = validate_password(password)
        if not valid:
            return jsonify({'error': 'Bad Request', 'message': error_msg}), 400

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Conflict', 'message': 'Username already exists'}), 409
            else:
                return jsonify({'error': 'Conflict', 'message': 'Email already exists'}), 409

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        # Create session
        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Bad Request', 'message': 'No data provided'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Bad Request', 'message': 'Username and password are required'}), 400

        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user or not user.check_password(password):
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid username or password'}), 401

        # Create session
        session['user_id'] = user.id
        session['username'] = user.username

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout a user"""
    try:
        session.pop('user_id', None)
        session.pop('username', None)

        return jsonify({'message': 'Logout successful'}), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user"""
    try:
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({'error': 'Unauthorized', 'message': 'Not logged in'}), 401

        user = User.query.get(user_id)

        if not user:
            session.pop('user_id', None)
            session.pop('username', None)
            return jsonify({'error': 'Unauthorized', 'message': 'User not found'}), 401

        return jsonify({
            'user': user.to_dict(include_email=True)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
