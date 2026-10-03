from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models import User

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please log in.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PersonalInfoForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('City, Country / Address', validators=[DataRequired()])
    linkedin = StringField('LinkedIn URL', validators=[Optional()])
    portfolio = StringField('Portfolio / Website URL', validators=[Optional()])
    submit = SubmitField('Save Personal Info')

class ResumeRoleForm(FlaskForm):
    role_name = StringField('Job Role Title (e.g. Backend Developer, Data Analyst)', validators=[DataRequired()])
    summary = TextAreaField('Professional Summary', validators=[DataRequired()])
    submit = SubmitField('Save Role')

class ExperienceForm(FlaskForm):
    company = StringField('Company Name', validators=[DataRequired()])
    job_title = StringField('Job Title', validators=[DataRequired()])
    start_date = StringField('Start Date (e.g. Jan 2022)', validators=[DataRequired()])
    end_date = StringField('End Date (e.g. Present, Dec 2023)', validators=[DataRequired()])
    description = TextAreaField('Description / Key Achievements', validators=[DataRequired()])
    submit = SubmitField('Add Experience')

class EducationForm(FlaskForm):
    institution = StringField('University / Institution', validators=[DataRequired()])
    degree = StringField('Degree / Certificate', validators=[DataRequired()])
    start_date = StringField('Start Date', validators=[DataRequired()])
    end_date = StringField('End Date (or Expected)', validators=[DataRequired()])
    submit = SubmitField('Add Education')

class SkillForm(FlaskForm):
    skill_name = StringField('Skill Name (e.g. Python, SQL, Project Management)', validators=[DataRequired()])
    submit = SubmitField('Add Skill')