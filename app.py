from flask import Flask, jsonify, request, send_file
from multiprocessing import Process, Pool
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug import secure_filename
import pyrebase
import requests
import uuid
import time
import socket
import os

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

download_processes = dict()
CHUNK_SIZE = 8192
PORT = os.getenv('PORT') if os.getenv('PORT')!=None else 5000

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
    del download_processes[id]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '.' 
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
    download_processes[download_id] = proc
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

@app.route('/control', methods=['POST'])
def control():
    download_id = request.args.get('id')
    action = str(request.args.get('action')).lower()    #pause/resume/stop
    if download_id in download_processes:
        if action=='pause':
            pid = download_processes[download_id].pid;
            download_processes[download_id].suspend()
            return { 'message': 'Pausing download' }
        elif action=='resume':
            download_processes[download_id].resume()
            return { 'message': 'Resuming download' }
        elif action=='stop':
            download_processes[download_id].terminate()
            del download_processes[download_id]
            return { 'message': 'Stopped download' }
        else:
            return { 'error': 'Invalid action. Accepted operations: pause/resume/stop' }

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        file.save(filename)
        download_url = 'http://'+socket.gethostbyname(socket.gethostname())+':'+str(PORT)+'/'+filename
        download_id = str(uuid.uuid4()).replace('-','')
        db.child(download_id).set({ 'name': filename, 'size': os.path.getsize(filename), 'done': os.path.getsize(filename), 'status': 'completed', 'remaining': 0 })
        return { 'id':  download_id }

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
