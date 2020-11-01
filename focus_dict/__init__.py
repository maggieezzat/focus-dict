from flask import Flask
from focus_dict.config import Config
from flask_mongoengine import MongoEngine

app = Flask(__name__, static_url_path="/static")
app.config.from_object(Config)

db = MongoEngine()
db.init_app(app)

from focus_dict import routes