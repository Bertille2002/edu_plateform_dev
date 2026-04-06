from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.validators import DataRequired, Email

class LoginForm(FlaskForm):
    username = StringField('Nom d’utilisateur', validators=[DataRequired()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])

class JoinForm(FlaskForm):
    role = SelectField('Type de compte', choices=[('student', 'Étudiant'), ('professor', 'Professeur')], validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])