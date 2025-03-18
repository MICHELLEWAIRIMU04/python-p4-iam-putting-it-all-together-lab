from flask import request, session, jsonify
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api, bcrypt
from models import User, Recipe

class Signup(Resource):
    def post(self):
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return {'error': 'Missing required fields'}, 400
        try:
            user = User(
                username=data['username'],
                image_url=data.get('image_url', ''),
                bio=data.get('bio', '')
            )
            user.password_hash = data['password']
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return user.to_dict(), 201
        except IntegrityError:
            db.session.rollback()
            return {'error': 'Username already exists'}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        user = User.query.get(user_id)
        if not user:
            return {'error': 'User not found'}, 404
        return user.to_dict(), 200

class Login(Resource):
    def post(self):
        data = request.get_json()
        if not data or "username" not in data or "password" not in data:
            return {'error': 'Missing username or password'}, 400
        user = User.query.filter_by(username=data['username']).first()
        if user and user.authenticate(data['password']):
            session['user_id'] = user.id
            return user.to_dict(), 200
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if "user_id" in session:
            session.pop("user_id")
            return '', 204
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        recipes = Recipe.query.filter_by(user_id=user_id).all()
        return [recipe.to_dict() for recipe in recipes], 200

    def post(self):
        user_id = session.get('user_id')
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        data = request.get_json()
        if not data or "title" not in data or "instructions" not in data or "minutes_to_complete" not in data:
            return {'error': 'Missing required fields'}, 400
        if len(data['instructions']) < 50:
            return {'error': 'Instructions must be at least 50 characters long'}, 422
        recipe = Recipe(
            title=data['title'],
            instructions=data['instructions'],
            minutes_to_complete=data['minutes_to_complete'],
            user_id=user_id
        )
        db.session.add(recipe)
        db.session.commit()
        return recipe.to_dict(), 201

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)
