"""
Form definitions using Flask-WTF
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', 
                          validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                           validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        """Check if username already exists"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Check if email already exists"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', 
                          validators=[DataRequired()])
    password = PasswordField('Password', 
                           validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RecipeForm(FlaskForm):
    """Recipe creation/editing form"""
    title = StringField('Recipe Title', 
                       validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Description', 
                               validators=[Length(max=500)])
    ingredients = TextAreaField('Ingredients', 
                               validators=[DataRequired()],
                               description='Enter each ingredient on a new line')
    instructions = TextAreaField('Instructions', 
                                validators=[DataRequired()],
                                description='Enter each step on a new line')
    prep_time = IntegerField('Preparation Time (minutes)')
    cook_time = IntegerField('Cooking Time (minutes)')
    servings = IntegerField('Number of Servings')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    image = StringField('Image URL (optional)')
    submit = SubmitField('Save Recipe')


class CommentForm(FlaskForm):
    """Comment form for recipes"""
    content = TextAreaField('Comment', 
                           validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Post Comment')