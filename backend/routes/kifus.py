from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from app import db
from models import Kifu as KifuModel, Move as MoveModel
from shogi.kif_parser import KifParser, KifParseError
import uuid
import os
from datetime import datetime

kifus_bp = Blueprint('kifus', __name__, url_prefix='/api/kif')

# Configuration
ALLOWED_EXTENSIONS = {'kif', 'kifu'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'kifus')

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@kifus_bp.route('/upload', methods=['POST'])
def upload_kifu():
    """Upload and parse a KIF file"""
    try:
        # Get user_id from session (optional - can upload without login)
        user_id = session.get('user_id')

        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'Bad Request', 'message': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'Bad Request', 'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'Bad Request', 'message': 'Invalid file type'}), 400

        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Seek back to start

        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'Bad Request', 'message': 'File too large'}), 400

        # Read file content
        file_content = file.read()

        # Parse KIF file
        try:
            parsed = KifParser.parse_file(file_content)
        except KifParseError as e:
            return jsonify({'error': 'Unprocessable Entity', 'message': str(e)}), 422

        # Validate moves
        try:
            KifParser.validate_moves(parsed['moves'])
        except KifParseError as e:
            return jsonify({'error': 'Unprocessable Entity', 'message': str(e)}), 422

        # Generate unique filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save file to storage
        file.seek(0)  # Reset file pointer
        with open(file_path, 'wb') as f:
            f.write(file.read())

        # Create Kifu model
        metadata = parsed['metadata']

        # game_date: KIFの日時文字列 → date型に変換
        raw_date = metadata.get('game_date')
        game_date = None
        if raw_date:
            for fmt in ('%Y/%m/%d %H:%M:%S', '%Y/%m/%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
                try:
                    game_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue

        kifu = KifuModel(
            user_id=user_id,
            file_path=file_path,
            original_filename=original_filename,
            black_player=metadata.get('black_player'),
            white_player=metadata.get('white_player'),
            game_date=game_date,
            result=metadata.get('result')
        )

        db.session.add(kifu)
        db.session.flush()  # Get the ID without committing

        # Create Move models
        for move_data in parsed['moves']:
            move = MoveModel(
                kifu_id=kifu.id,
                move_number=move_data['move_number'],
                notation=move_data['notation'],
                from_square=move_data.get('from_square'),
                to_square=move_data.get('to_square'),
                piece_type=move_data.get('piece_type'),
                is_promotion=move_data.get('is_promotion', False),
                is_drop=move_data.get('is_drop', False),
                comment=move_data.get('comment')
            )
            db.session.add(move)

        db.session.commit()

        # Prepare response
        moves_response = [move.to_dict() for move in kifu.moves]

        return jsonify({
            'id': kifu.id,
            'metadata': metadata,
            'moves': moves_response,
            'file_path': filename  # Return only filename, not full path
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@kifus_bp.route('/<kifu_id>', methods=['GET'])
def get_kifu(kifu_id):
    """Get a kifu by ID"""
    try:
        kifu = KifuModel.query.get(kifu_id)
        
        if not kifu:
            return jsonify({'error': 'Not Found', 'message': 'Kifu not found'}), 404
        
        return jsonify(kifu.to_dict(include_moves=True)), 200
    
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@kifus_bp.route('/<kifu_id>/moves/<int:move_number>', methods=['GET'])
def get_move_position(kifu_id, move_number):
    """Get a specific move's position"""
    try:
        kifu = KifuModel.query.get(kifu_id)
        
        if not kifu:
            return jsonify({'error': 'Not Found', 'message': 'Kifu not found'}), 404
        
        move = MoveModel.query.filter_by(kifu_id=kifu_id, move_number=move_number).first()
        
        if not move:
            return jsonify({'error': 'Not Found', 'message': 'Move not found'}), 404
        
        return jsonify(move.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500

@kifus_bp.route('/<kifu_id>/info', methods=['GET'])
def get_kifu_info(kifu_id):
    """Get kifu information (metadata and move count)"""
    try:
        kifu = KifuModel.query.get(kifu_id)
        
        if not kifu:
            return jsonify({'error': 'Not Found', 'message': 'Kifu not found'}), 404
        
        move_count = MoveModel.query.filter_by(kifu_id=kifu_id).count()
        
        return jsonify({
            'id': kifu.id,
            'black_player': kifu.black_player,
            'white_player': kifu.white_player,
            'game_date': kifu.game_date,
            'result': kifu.result,
            'total_moves': move_count,
            'created_at': kifu.created_at.isoformat(),
            'updated_at': kifu.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
