import os
from datetime import timedelta

# Get the base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Basic Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-12345'
    
    # Database - FIXED: Using SQLite properly
    DATABASE_FOLDER = os.path.join(BASE_DIR, 'database')
    DATABASE_PATH = os.path.join(DATABASE_FOLDER, 'delivery.db')

    # Create database folder if it doesn't exist
    os.makedirs(DATABASE_FOLDER, exist_ok=True)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Fix for potential Heroku postgres:// URL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Default to SQLite if no DATABASE_URL is set
    if not SQLALCHEMY_DATABASE_URI:
           SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
           SQLALCHEMY_TRACK_MODIFICATIONS = False
           SQLALCHEMY_ECHO = False  # Set to True for SQL debugging
        
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Business settings - Algeria specific
    DELIVERY_BASE_FEE = 100.0  # 200 DZD
    PLATFORM_COMMISSION = 10  # 10%
    PLATFORM_SERVICE_FEE = 50.0  # 50 DZD
    
    # Currency
    CURRENCY = 'DZD'
    CURRENCY_SYMBOL = 'د.ج'
    
    # Pagination
    ORDERS_PER_PAGE = 20
    ITEMS_PER_PAGE = 50
    
    # SocketIO
    SOCKETIO_ASYNC_MODE = 'threading'
    SOCKETIO_PING_TIMEOUT = 60
    SOCKETIO_PING_INTERVAL = 25
    
    # Timezone
    TIMEZONE = 'Africa/Algiers'
    
    # Default location (Algiers)
    DEFAULT_LAT = 36.7538
    DEFAULT_LNG = 3.0588
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Force HTTPS
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Strong secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in .env
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Security headers (handled by Nginx, but also in Flask)
    PREFERRED_URL_SCHEME = 'https'

    # Flask settings
    BASE_DIR = BASE_DIR
 
    # Add to Config class
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_API_KEY_HERE')