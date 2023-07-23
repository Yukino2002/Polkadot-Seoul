from flask import Flask
from flask_socketio import SocketIO, emit
import time
import json
from datetime import datetime, timedelta
import pytz

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
    print(data)
    # check if it open ai key is not null
    if data['openAIKey'] is None or data['openAIKey'] == "":
        print("no open ai key")
        return
    if data['mnenonic'] is None or data['mnenonic'] == "":
        print("no memonic")
        return
    
    payload = dict()
    payload['prompt'] = data['prompt'] + "nisoo"
    session = {
    'user': {
        'name': 'Sybil AI',
        'email': data['session']['user']['email'],
        'image': 'https://i.imgur.com/usI3OTw.png'
        }
    }
    payload['session'] = session
    payload['chatId'] = data['chatId']
    
    now_utc = datetime.now(pytz.timezone('UTC')) + timedelta(seconds=2)
    payload['createdAt'] = now_utc.isoformat()
    emit('response', payload)


if __name__ == '__main__':
    socketio.run(app)
