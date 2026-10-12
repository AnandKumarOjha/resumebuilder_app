from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from flask import current_app
from itsdangerous import URLSafeTimedSerializer

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    is_premium = db.Column(db.Boolean, default=False)
    
    personal_info = db.relationship('PersonalInfo', backref='owner', uselist=False, lazy=True)
    roles = db.relationship('ResumeRole', backref='author', lazy=True)

    def get_reset_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.id}, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token, max_age=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token, salt='password-reset-salt', max_age=max_age)
            user_id = data.get('user_id')
        except Exception:
            return None
        return db.session.get(User, user_id)

class PersonalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    linkedin = db.Column(db.String(120))
    portfolio = db.Column(db.String(120))

class ResumeRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_name = db.Column(db.String(100), nullable=False)
    summary = db.Column(db.Text)
    
    experiences = db.relationship('Experience', backref='role', lazy=True, cascade="all, delete-orphan")
    educations = db.relationship('Education', backref='role', lazy=True, cascade="all, delete-orphan")
    skills = db.relationship('Skill', backref='role', lazy=True, cascade="all, delete-orphan")

class Experience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('resume_role.id'), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    job_title = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    description = db.Column(db.Text)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('resume_role.id'), nullable=False)
    institution = db.Column(db.String(100), nullable=False)
    degree = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))

class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('resume_role.id'), nullable=False)
    skill_name = db.Column(db.String(50), nullable=False)