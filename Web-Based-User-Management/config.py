import os

#Global Config File
class config:
    debug = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://flaskuser:flaskpass@localhost/flaskdb"
    )

class dev_config(config):
    debug = True

class prod_config(config):
    debug = False
