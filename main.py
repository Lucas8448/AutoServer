import docker
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for, session
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Constants and configs
image_version_data = {
        'python': ['latest'],
        'Debian': ['9', '10'],
        'CentOS': ['8', '7'],
        'Fedora': ['34', '33', '32', '31'],
        'Arch': ['latest'],
        'Alpine': ['3.14', '3.13', '3.12', '3.11'],
        'Kali': ['latest'],
        'Parrot': ['latest'],
        'BlackArch': ['latest'],
        'Ubuntu-Mate': ['latest'],
        'Ubuntu-Studio': ['latest'],
        'Lubuntu': ['latest'],
        'Kubuntu': ['latest'],
        'Xubuntu': ['latest'],
        'Ubuntu-Budgie': ['latest'],
        'Ubuntu-Kylin': ['latest'],
        'Ubuntu-Unity': ['latest'],
        'Ubuntu-DDE': ['latest'],
    }

app = Flask(__name__)
app.secret_key = 'supersecretkey'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

logging.basicConfig(level=logging.INFO)

# SQLite3 Setup
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute(
  'CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
conn.commit()
conn.close()

# Docker client
client = docker.from_env()
containers = {}
authenticated_users = {}

@socketio.on('authenticate')
def handle_authenticate(data):
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username, ))
    record = cursor.fetchone()
    conn.close()

    if record and check_password_hash(record[1], password):
        authenticated_users[request.sid] = username
        logging.info("Sending auth_status with data:", {
                     'authenticated': True, 'username': username})
        emit('auth_status', {'authenticated': True, 'username': username})
    else:
        logging.info("Sending auth_status with data:", {
                     'authenticated': False})
        emit('auth_status', {'authenticated': False})


@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in authenticated_users:
        del authenticated_users[request.sid]

@socketio.on('check_auth')
def handle_check_auth():
    if 'username' in session:
        emit('auth_status', {'authenticated': True, 'username': session['username']})
    else:
        emit('auth_status', {'authenticated': False}, status=401)

@socketio.on('signup')
def handle_signup(data):
    username = data['username']
    password = data['password']
    hashed_password = generate_password_hash(password)

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',(username, hashed_password))
    conn.commit()
    conn.close()

    emit('signup_status', {'success': True})

@socketio.on('login')
def handle_login(data):
    username = data['username']
    password = data['password']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    record = cursor.fetchone()
    conn.close()

    if record and check_password_hash(record[1], password):
        emit('login_status', {'success': True, 'username': username})
    else:
        emit('login_status', {'success': False})

@socketio.on('image_version_data')
def handle_request_image_version_data():
    emit('image_version_data', image_version_data)

@socketio.on('get_active_containers')
def get_active_containers():
    session_id = request.sid
    if session_id in containers:
        emit('active_containers', containers[session_id])

@socketio.on('start_container')
def start_container(data):
  image = data.get('image', '').lower()
  version = data.get('version', '')
  session_id = request.sid
  full_image = f"{image}:{version}"

  logging.info(f'Request to start {full_image} container')

  if image not in image_version_data or version not in image_version_data[image]:
    logging.warning(f'Invalid container image: {full_image}')
    return

  if session_id in containers:
    logging.warning(f'Container already running for session: {session_id}')
    return

  try:
    container = client.containers.run(
      full_image, detach=True, command="tail -f /dev/null")
    containers[session_id] = container
    logging.info(
      f'Started {full_image} container: {container.id} for session: {session_id}')
  except Exception as e:
    logging.error(f'Failed to start container: {e}')
  if session_id not in containers:
      containers[session_id] = []
  containers[session_id].append({
      'id': container.id,
      'image': image,
      'version': version
  })
  emit('active_containers', containers[session_id])


@socketio.on('stop_container')
def stop_container(data):
    container_id = data.get('id', '')
    session_id = request.sid
    if session_id in containers:
        for container_info in containers[session_id]:
            if container_info['id'] == container_id:
                try:
                    container = client.containers.get(container_id)
                    container.stop()
                    container.remove()
                    containers[session_id].remove(container_info)
                    emit('active_containers', containers[session_id])
                    logging.info(
                        f'Stopped and removed container: {container.id} for session: {session_id}')
                    return
                except Exception as e:
                    logging.error(f'Failed to stop and remove container: {e}')
                    return


if __name__ == '__main__':
  socketio.run(app)