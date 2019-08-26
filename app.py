from flask import Flask, jsonify, request
from multiprocessing import Process, Pool
import pyrebase
import requests
import time
import uuid

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

def download_file_from_url(url, id):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        size = int(r.headers.get('content-length'))
        db.child(id).set({ 'size': size, 'done': 0 })
        if r.status_code==200:
            with open(local_filename, 'wb') as f:
                dl=0
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    dl+=len(chunk)
                    if (dl*100/size)%10==0:
                        db.child(id).update({ 'done': dl })

app = Flask(__name__)
@app.route('/download')
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
    obj['remaining'] = obj['size'] - obj['done']
    obj['status'] = 'completed' if obj['remaining']==0 else 'downloading'
    return jsonify(obj)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
