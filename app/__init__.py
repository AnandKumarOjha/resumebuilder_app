from flask import Flask, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.auth.routes import auth
    from app.dashboard.routes import dashboard
    from app.resume.routes import resume
    from app.payments.routes import payments

    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(resume)
    app.register_blueprint(payments)

    # Root landing route
    @app.route('/')
    def home():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return render_template('home.html')

    return app