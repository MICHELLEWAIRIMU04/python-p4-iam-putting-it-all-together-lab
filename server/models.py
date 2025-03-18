from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)
    image_url = db.Column(db.String, nullable=True)
    bio = db.Column(db.String, nullable=True)

    recipes = db.relationship('Recipe', back_populates='user', cascade='all, delete-orphan')

    serialize_rules = ('-recipes.user',)

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hash is not readable.')

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates('username')
    def validate_username(self, key, username):
        if not username or len(username) < 3:
            raise ValueError('Username must be at least 3 characters long.')
        return username

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    user = db.relationship('User', back_populates='recipes')
    
    serialize_rules = ('-user.recipes',)
    
    @validates('title', 'instructions', 'minutes_to_complete')
    def validate_fields(self, key, value):
        if not value:
            raise ValueError(f'{key} is required.')
        if key == 'instructions' and len(value) < 50:
            raise ValueError('Instructions must be at least 50 characters long.')
        if key == 'minutes_to_complete' and (not isinstance(value, int) or value <= 0):
            raise ValueError('Minutes to complete must be a positive number.')
        return value
