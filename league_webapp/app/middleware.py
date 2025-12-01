"""Performance monitoring middleware for Flask application."""
import time
import logging
from flask import request, g
from functools import wraps

logger = logging.getLogger(__name__)


def setup_request_timing(app):
    """Add request timing to all requests."""
    
    @app.before_request
    def before_request():
        """Record the start time of each request."""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Log request duration and details."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            # Log slow requests (> 1 second)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration:.3f}s | Status: {response.status_code}"
                )
            
            # Add timing header to all responses
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


def setup_database_monitoring(app):
    """Monitor database query counts."""
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Track when a query starts."""
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Track when a query completes and log slow queries."""
        total_time = time.time() - conn.info['query_start_time'].pop(-1)
        
        # Log slow queries (> 100ms)
        if total_time > 0.1:
            logger.warning(f"Slow query ({total_time:.3f}s): {statement[:200]}")
    
    @app.before_request
    def reset_query_count():
        """Reset query counter at the start of each request."""
        g.query_count = 0
    
    @event.listens_for(Engine, "after_cursor_execute")
    def increment_query_count(conn, cursor, statement, parameters, context, executemany):
        """Count queries per request."""
        if hasattr(g, 'query_count'):
            g.query_count += 1
    
    @app.after_request
    def log_query_count(response):
        """Log query count for each request."""
        if hasattr(g, 'query_count') and g.query_count > 10:
            logger.warning(
                f"High query count: {request.method} {request.path} "
                f"executed {g.query_count} queries"
            )
        return response


def setup_error_logging(app):
    """Set up comprehensive error logging."""
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Log all unhandled exceptions."""
        logger.error(
            f"Unhandled exception in {request.method} {request.path}: {str(e)}",
            exc_info=True
        )
        # Re-raise the exception to let Flask's error handlers deal with it
        raise


def setup_monitoring(app):
    """Initialize all monitoring and logging."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set up all monitoring
    setup_request_timing(app)
    setup_database_monitoring(app)
    setup_error_logging(app)
    
    logger.info("Performance monitoring initialized")
