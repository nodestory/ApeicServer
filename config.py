class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
	pass

class DevelopmentConfig(Config):
	DATABASE = '/cygdrive/c/Users/Linzy/aleic.db'
	DEBUG = True
	UPLOAD_FOLDER = 'logs'

class TestingConfig(Config):
    TESTING = True