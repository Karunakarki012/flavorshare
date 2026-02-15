"""
Database models for FlavorShare application
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """User model for authentication and profile"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    avatar = db.Column(db.String(200), default='default_avatar.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recipes = db.relationship('Recipe', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Category(db.Model):
    """Recipe categories"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    recipes = db.relationship('Recipe', backref='category', lazy=True)
    
    def __repr__(self):
        return f"Category('{self.name}')"


class Recipe(db.Model):
    """Recipe model containing all recipe information"""
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ingredients = db.Column(db.Text, nullable=False)  # Stored as JSON string or formatted text
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer, nullable=True)  # In minutes
    cook_time = db.Column(db.Integer, nullable=True)  # In minutes
    servings = db.Column(db.Integer, nullable=True)
    image = db.Column(db.String(200), default='default_recipe.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='recipe', lazy=True, cascade='all, delete-orphan')
    favorited_by = db.relationship('Favorite', backref='recipe', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"Recipe('{self.title}', by {self.author.username})"
    
    @property
    def total_time(self):
        """Calculate total preparation and cooking time"""
        return (self.prep_time or 0) + (self.cook_time or 0)


class Comment(db.Model):
    """User comments on recipes"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    
    def __repr__(self):
        return f"Comment by {self.author.username} on Recipe {self.recipe_id}"


class Favorite(db.Model):
    """User favorite recipes (many-to-many relationship)"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    
    # Ensure a user can only favorite a recipe once
    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_user_recipe'),)
    
    def __repr__(self):
        return f"Favorite(User {self.user_id}, Recipe {self.recipe_id})"