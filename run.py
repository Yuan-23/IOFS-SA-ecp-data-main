
from app import app,socketio

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=5000)
    # in this way will enables socketIO==
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
