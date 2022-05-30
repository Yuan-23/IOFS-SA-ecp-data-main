from flask import Flask
from flask_socketio import SocketIO,emit
app = Flask(__name__)
app.config['SECRET_KEY'] = 'adio*nfionasdfoin23nrjtnejkasnf-knalasdjfkn3o4ntoqij'
socketio = SocketIO(app)

from app import views
from app import utilities
from app import CoreModules
from app import plugins