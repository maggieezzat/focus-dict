from flask import Flask, session
from flask_session import Session
from focus_dict.config import Config
from flask_pymongo import PyMongo
import os

app = Flask(__name__, static_url_path="/static")
app.secret_key = os.urandom(24)
app.config.from_object(Config)
Session(app)
mongo = PyMongo(app)


from focus_dict import routes