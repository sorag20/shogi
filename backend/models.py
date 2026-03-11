import uuid
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(db.Model):
    """User model - represents a user account"""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    kifus = db.relationship('Kifu', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

        if include_email:
            data['email'] = self.email

        return data

class Position(db.Model):
    """Position model - represents a shogi board position"""
    __tablename__ = 'positions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_state = db.Column(db.JSON, nullable=False)
    turn = db.Column(db.Enum('black', 'white'), nullable=False, default='black')
    position_metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Position {self.id}>'
    
    def to_dict(self):
        """Convert position to dictionary"""
        return {
            'id': self.id,
            'board_state': self.board_state,
            'turn': self.turn,
            'metadata': self.position_metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data):
        """Create position from dictionary"""
        position = Position(
            board_state=data.get('board_state'),
            turn=data.get('turn', 'black'),
            position_metadata=data.get('metadata')
        )
        return position
    
    def validate(self):
        """Validate position data"""
        if not self.board_state:
            raise ValueError('board_state is required')
        
        if not isinstance(self.board_state, (dict, list)):
            raise ValueError('board_state must be a dict or list')
        
        if self.turn not in ['black', 'white']:
            raise ValueError('turn must be "black" or "white"')
        
        return True

class Kifu(db.Model):
    """Kifu model - represents a game record"""
    __tablename__ = 'kifus'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    original_filename = db.Column(db.String(255), nullable=True)
    black_player = db.Column(db.String(255), nullable=True)
    white_player = db.Column(db.String(255), nullable=True)
    game_date = db.Column(db.Date, nullable=True)
    result = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    moves = db.relationship('Move', backref='kifu', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Kifu {self.id}>'
    
    def to_dict(self, include_moves=False):
        """Convert kifu to dictionary"""
        data = {
            'id': self.id,
            'black_player': self.black_player,
            'white_player': self.white_player,
            'game_date': self.game_date.isoformat() if self.game_date else None,
            'result': self.result,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_moves:
            data['moves'] = [move.to_dict() for move in self.moves]
        
        return data
    
    @staticmethod
    def from_dict(data):
        """Create kifu from dictionary"""
        kifu = Kifu(
            black_player=data.get('black_player'),
            white_player=data.get('white_player'),
            game_date=data.get('game_date'),
            result=data.get('result')
        )
        return kifu
    
    def validate(self):
        """Validate kifu data"""
        # Kifu can have optional fields, so minimal validation
        return True

class Move(db.Model):
    """Move model - represents a single move in a game"""
    __tablename__ = 'moves'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kifu_id = db.Column(db.String(36), db.ForeignKey('kifus.id'), nullable=False)
    move_number = db.Column(db.Integer, nullable=False)
    notation = db.Column(db.String(50), nullable=False)
    from_square = db.Column(db.String(10), nullable=True)
    to_square = db.Column(db.String(10), nullable=True)
    piece_type = db.Column(db.String(20), nullable=True)
    is_promotion = db.Column(db.Boolean, default=False)
    is_drop = db.Column(db.Boolean, default=False)
    comment = db.Column(db.Text, nullable=True)
    position_after = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_kifu_id', 'kifu_id'),
        db.Index('idx_move_number', 'move_number'),
    )
    
    def __repr__(self):
        return f'<Move {self.id}>'
    
    def to_dict(self):
        """Convert move to dictionary"""
        return {
            'id': self.id,
            'kifu_id': self.kifu_id,
            'move_number': self.move_number,
            'notation': self.notation,
            'from_square': self.from_square,
            'to_square': self.to_square,
            'piece_type': self.piece_type,
            'is_promotion': self.is_promotion,
            'is_drop': self.is_drop,
            'comment': self.comment,
            'position_after': self.position_after,
            'created_at': self.created_at.isoformat()
        }
    
    @staticmethod
    def from_dict(data):
        """Create move from dictionary"""
        move = Move(
            kifu_id=data.get('kifu_id'),
            move_number=data.get('move_number'),
            notation=data.get('notation'),
            from_square=data.get('from_square'),
            to_square=data.get('to_square'),
            piece_type=data.get('piece_type'),
            is_promotion=data.get('is_promotion', False),
            is_drop=data.get('is_drop', False),
            comment=data.get('comment'),
            position_after=data.get('position_after')
        )
        return move
    
    def validate(self):
        """Validate move data"""
        if not self.kifu_id:
            raise ValueError('kifu_id is required')
        
        if self.move_number is None or self.move_number < 1:
            raise ValueError('move_number must be a positive integer')
        
        if not self.notation:
            raise ValueError('notation is required')
        
        return True
