from flask import Flask, jsonify, request, send_file
from multiprocessing import Process, Pool
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import pyrebase
import requests
import uuid
import time

firebaseConfig = {
    "apiKey": "AIzaSyDo5jCdYbKahPl4hekGz5QzEQwoaTkFIbU",
    "authDomain": "soilkart-3d137.firebaseapp.com",
    "databaseURL": "https://soilkart-3d137.firebaseio.com",
    "projectId": "soilkart-3d137",
    "storageBucket": "soilkart-3d137.appspot.com",
    "messagingSenderId": "968338824712",
    "appId": "1:968338824712:web:2e7677773b7474a0"
}
firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

CHUNK_SIZE = 8192

def download_file_from_url(url, id):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        size = int(r.headers.get('content-length'))
        db.child(id).set({ 'name': local_filename, 'size': size, 'done': 0 })
        if r.status_code==200:
            with open(local_filename, 'wb') as f:
                dl=0
                start_time = int(time.time())
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    end_time = int(time.time()) - start_time
                    f.write(chunk)
                    dl+=len(chunk)
                    if (dl*100/size)%10==0:
                        db.child(id).update({ 'done': dl })
                    start_time = end_time

app = Flask(__name__)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per minute"],
)

@app.route('/download', methods=['POST'])
def download():
    remote_url = request.args.get('url')
    download_id = str(uuid.uuid4()).replace('-','')
    proc = Process(target=download_file_from_url, args=(remote_url, download_id))
    proc.start()
    return { 'id': download_id }

@app.route('/status')
def status():
    download_id = request.args.get('id')
    obj = (db.child(download_id).get()).val()
    obj['remaining'] = obj['size']-obj['done']
    obj['status'] = 'completed' if obj['remaining']==0 else 'downloading'
    return jsonify(obj)

@app.route('/file')
def get_file():
    download_id = request.args.get('id')
    obj = (db.child(download_id).get()).val()
    local_filename = obj['name']
    return send_file(local_filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
