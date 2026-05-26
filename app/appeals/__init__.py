from flask import Blueprint

bp = Blueprint('appeals', __name__)

from app.appeals import routes