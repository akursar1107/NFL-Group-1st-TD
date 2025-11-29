from flask import Blueprint

main_bp = Blueprint('main', __name__)

# Import and register main routes here
from ..routes import *
