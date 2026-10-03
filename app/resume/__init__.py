from flask import Blueprint

resume = Blueprint('resume', __name__)

from app.resume import routes
