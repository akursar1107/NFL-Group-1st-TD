"""
API Blueprint - Main router
Imports all sub-modules and registers routes
"""
from flask import Blueprint

# Create the main API blueprint
api_bp = Blueprint('api', __name__)

# Import all route modules to register them
from . import standings
from . import picks
from . import games
from . import analysis
from . import admin

# Export the blueprint
__all__ = ['api_bp']
