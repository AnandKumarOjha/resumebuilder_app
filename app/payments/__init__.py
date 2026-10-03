from flask import Blueprint

payments = Blueprint('payments', __name__, url_prefix='/payment')

from app.payments import routes
