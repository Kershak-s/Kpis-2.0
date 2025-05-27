import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-aleatoria'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'

class ProductionConfig(Config):
    DEBUG = False
    # Para PostgreSQL en producción:
    # SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/dbname'
    # O para seguir con SQLite:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///users.db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}