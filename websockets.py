from flask import Flask
from flask_socketio import SocketIO, emit
import time
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('query')
def handle_query(data):
    print(data)
    weather_data = {
        "type": "weather",
        "content": "It's sunny today!"
    }
    emit('response', weather_data)
    time.sleep(10)
    
    news_data = {
        "type": "news",
        "content": "Latest news update here!"
    }
    emit('response', news_data)
    time.sleep(10)
    
    other_data = {
        "type": "other",
        "content": "Other type of data!"
    }
    emit('response', other_data)


@socketio.on('print')
def handle_query(data):
    # check if data is a json
    try:
        data = json.loads(data)
    except:
        return
    print(data["openAIKey"])
    # check if it open ai key is not null
    if data['openAIKey'] is None or data['openAIKey'] == "":
        print("no open ai key")
        return
    if data['mnenonic'] is None or data['mnenonic'] == "":
        print("no memonic")
        return
    print(data)


if __name__ == '__main__':
    socketio.run(app)
