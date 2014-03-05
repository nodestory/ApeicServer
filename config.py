class Config(object):
    DEBUG = False
    TESTING = False

class ProductionConfig(Config):
	pass

class DevelopmentConfig(Config):
	DEBUG = True
	SQLALCHEMY_DATABASE_URI = 'mysql://linzy:yatingcj6@localhost/apeic'

class TestingConfig(Config):
    TESTING = True