import docker
import sqlite3
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Constants and configs
os_version_data = {
        'Ubuntu': ['18.04', '20.04'],
        'Debian': ['9', '10'],
        'Windows': ['10', '11']
    }

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this in production
socketio = SocketIO(app)

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


@app.route('/', methods=['GET', 'POST'])
def index():
  if 'username' in session:
    return render_template('index.html', os_version_data=os_version_data)

  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username, ))
    record = cursor.fetchone()
    conn.close()
    if record and check_password_hash(record[1], password):
      session['username'] = username
      return redirect(url_for('index'))
    conn.close()
    
  return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template('signup.html')

@socketio.on('start_container')
def start_container(data):
  image = data.get('image', '')
  version = data.get('version', '')
  session_id = request.sid
  full_image = f"{image}:{version}"

  logging.info(f'Request to start {full_image} container')

  if image not in VALID_IMAGES or version not in VALID_IMAGES[image]:
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


@socketio.on('stop_container')
def stop_container():
  session_id = request.sid

  if session_id in containers:
    try:
      container = containers[session_id]
      container.stop()
      container.remove()
      del containers[session_id]
      logging.info(
        f'Stopped and removed container: {container.id} for session: {session_id}')
    except Exception as e:
      logging.error(f'Failed to stop and remove container: {e}')
  else:
    logging.warning(f'No container found for session: {session_id}')


if __name__ == '__main__':
  socketio.run(app)