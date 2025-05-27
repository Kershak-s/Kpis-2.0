# Configuration settings for the application

class Config(object):
    # General configuration
    SECRET_KEY = 'cambia_esta_llave_por_una_mas_segura'
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    # Production settings
    SECRET_KEY = 'production_key_must_be_changed'  # Should be overridden by environment variable
    
    # The database URI should be configured for production
    # Example: SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/kpis_db'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}