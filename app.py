"""
FlavorShare - Recipe Sharing Platform with Image Upload
"""

from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from datetime import datetime
import os
import secrets
from PIL import Image

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Image upload configuration
app.config['UPLOAD_FOLDER'] = 'static/images/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Image saving function
def save_picture(form_picture):
    """Save uploaded picture with random name and resize it"""
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images/uploads', picture_fn)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Resize image
    output_size = (800, 600)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

# Database Models
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    recipes = db.relationship('Recipe', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    prep_time = db.Column(db.Integer)
    cook_time = db.Column(db.Integer)
    servings = db.Column(db.Integer)
    image_file = db.Column(db.String(20), nullable=False, default='default_recipe.jpg')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    comments = db.relationship('Comment', backref='recipe', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='recipe', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    recipes = db.relationship('Recipe', backref='category', lazy=True)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'recipe_id', name='unique_favorite'),)

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RecipeForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    ingredients = TextAreaField('Ingredients', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    prep_time = IntegerField('Preparation Time (minutes)')
    cook_time = IntegerField('Cooking Time (minutes)')
    servings = IntegerField('Servings')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = FileField('Recipe Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Post Recipe')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post Comment')

# Routes
@app.route('/')
@app.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    recipes = Recipe.query.order_by(Recipe.date_posted.desc()).paginate(page=page, per_page=6)
    categories = Category.query.all()
    return render_template('index.html', recipes=recipes, categories=categories)

@app.route('/about')
def about():
    return render_template('about.html', title='About')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/recipe/new', methods=['GET', 'POST'])
@login_required
def new_recipe():
    form = RecipeForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Handle image upload
        if form.image.data:
            picture_file = save_picture(form.image.data)
        else:
            picture_file = 'default_recipe.jpg'
        
        recipe = Recipe(
            title=form.title.data,
            description=form.description.data,
            ingredients=form.ingredients.data,
            instructions=form.instructions.data,
            prep_time=form.prep_time.data,
            cook_time=form.cook_time.data,
            servings=form.servings.data,
            image_file=picture_file,
            category_id=form.category_id.data,
            author=current_user
        )
        db.session.add(recipe)
        db.session.commit()
        flash('Your recipe has been created!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe.id))
    
    return render_template('create_recipe.html', title='New Recipe', form=form, legend='New Recipe')

@app.route('/recipe/<int:recipe_id>')
def recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    comments = Comment.query.filter_by(recipe_id=recipe_id).order_by(Comment.date_posted.desc()).all()
    form = CommentForm()
    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first() is not None
    return render_template('recipe_detail.html', title=recipe.title, recipe=recipe, comments=comments, form=form, is_favorite=is_favorite)

@app.route('/recipe/<int:recipe_id>/update', methods=['GET', 'POST'])
@login_required
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    
    form = RecipeForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        recipe.title = form.title.data
        recipe.description = form.description.data
        recipe.ingredients = form.ingredients.data
        recipe.instructions = form.instructions.data
        recipe.prep_time = form.prep_time.data
        recipe.cook_time = form.cook_time.data
        recipe.servings = form.servings.data
        recipe.category_id = form.category_id.data
        
        # Handle new image upload
        if form.image.data:
            picture_file = save_picture(form.image.data)
            recipe.image_file = picture_file
        
        db.session.commit()
        flash('Your recipe has been updated!', 'success')
        return redirect(url_for('recipe', recipe_id=recipe.id))
    
    elif request.method == 'GET':
        form.title.data = recipe.title
        form.description.data = recipe.description
        form.ingredients.data = recipe.ingredients
        form.instructions.data = recipe.instructions
        form.prep_time.data = recipe.prep_time
        form.cook_time.data = recipe.cook_time
        form.servings.data = recipe.servings
        form.category_id.data = recipe.category_id
    
    return render_template('create_recipe.html', title='Update Recipe', form=form, legend='Update Recipe')

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    if recipe.author != current_user:
        abort(403)
    db.session.delete(recipe)
    db.session.commit()
    flash('Your recipe has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, recipe=recipe)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
    return redirect(url_for('recipe', recipe_id=recipe.id))

@app.route('/recipe/<int:recipe_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)
    favorite = Favorite.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
    if favorite:
        db.session.delete(favorite)
        flash('Recipe removed from favorites!', 'info')
    else:
        favorite = Favorite(user_id=current_user.id, recipe_id=recipe_id)
        db.session.add(favorite)
        flash('Recipe added to favorites!', 'success')
    
    db.session.commit()
    return redirect(url_for('recipe', recipe_id=recipe.id))

@app.route('/dashboard')
@login_required
def dashboard():
    user_recipes = Recipe.query.filter_by(author=current_user).order_by(Recipe.date_posted.desc()).all()
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.date_added.desc()).all()
    return render_template('dashboard.html', title='Dashboard', user_recipes=user_recipes, favorites=favorites)

@app.route('/user/<string:username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    recipes = Recipe.query.filter_by(author=user).order_by(Recipe.date_posted.desc()).all()
    return render_template('profile.html', title=f"{username}'s Profile", user=user, recipes=recipes)

# UPDATED RECIPES ROUTE WITH ADVANCED FILTERS
@app.route('/recipes')
def recipes():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'newest')
    min_time = request.args.get('min_time', type=int)
    max_time = request.args.get('max_time', type=int)
    
    query = Recipe.query
    
    # Category filter
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Search filter
    if search:
        query = query.filter(
            (Recipe.title.contains(search)) | 
            (Recipe.description.contains(search)) |
            (Recipe.ingredients.contains(search))
        )
    
    # Time filter
    if min_time is not None:
        query = query.filter((Recipe.prep_time + Recipe.cook_time) >= min_time)
    if max_time is not None:
        query = query.filter((Recipe.prep_time + Recipe.cook_time) <= max_time)
    
    # Sorting
    if sort_by == 'newest':
        query = query.order_by(Recipe.date_posted.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Recipe.date_posted.asc())
    elif sort_by == 'popular':
        # Sort by number of favorites
        query = query.outerjoin(Favorite).group_by(Recipe.id).order_by(db.func.count(Favorite.id).desc())
    elif sort_by == 'quickest':
        query = query.order_by((Recipe.prep_time + Recipe.cook_time).asc())
    
    recipes = query.paginate(page=page, per_page=9)
    categories = Category.query.all()
    
    return render_template('recipes.html', 
                         title='Recipes', 
                         recipes=recipes, 
                         categories=categories, 
                         selected_category=category_id, 
                         search=search,
                         sort_by=sort_by,
                         min_time=min_time,
                         max_time=max_time)

# ===== MAIN ENTRY POINT =====
if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables ready")
            
            # Add default categories if none exist
            if Category.query.count() == 0:
                categories = [
                    {'name': 'Breakfast', 'description': 'Start your day'},
                    {'name': 'Lunch', 'description': 'Midday meals'},
                    {'name': 'Dinner', 'description': 'Evening meals'},
                    {'name': 'Desserts', 'description': 'Sweet treats'},
                    {'name': 'Appetizers', 'description': 'Starters'},
                    {'name': 'Vegetarian', 'description': 'Meat-free'},
                    {'name': 'Quick & Easy', 'description': '30 mins or less'},
                    {'name': 'Healthy', 'description': 'Nutritious'}
                ]
                for cat in categories:
                    category = Category(name=cat['name'], description=cat['description'])
                    db.session.add(category)
                db.session.commit()
                print("✅ Default categories added")
                
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    app.run(debug=True, port=5001)