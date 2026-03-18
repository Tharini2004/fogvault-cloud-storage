"""
FogVault: Securing Cloud Storage with Fog Computing
Authors: K. Guru Sathvik, Preethi M., Samarth V.H., Tharini G.
Institution: Nagarjuna College of Engineering & Technology
Academic Year: 2025-26
Guide: Rashmi P Karchi
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from dotenv import load_dotenv
from fogvault_logic import FogVaultLogic

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fogvault-secret-key-2025')

# Initialize FogVault logic
fog = FogVaultLogic()

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'xlsx', 'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email    = request.form.get('email')
        result = fog.register_user(username, password, email)
        if result['success']:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result['message'], 'error')
    return render_template('login.html', mode='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        result = fog.authenticate_user(username, password)
        if result['success']:
            session['username'] = username
            session['user_id']  = result['user_id']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.', 'error')
    return render_template('login.html', mode='login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    files = fog.get_user_files(session['user_id'])
    return render_template('dashboard.html', files=files, username=session['username'])

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_data = file.read()
            result = fog.upload_file(
                user_id=session['user_id'],
                filename=filename,
                file_data=file_data
            )
            if result['success']:
                flash(f'File "{filename}" uploaded successfully! ✅', 'success')
                fog.log_action(session['user_id'], 'upload', filename, 'success')
                return redirect(url_for('dashboard'))
            else:
                flash(f'Upload failed: {result["message"]}', 'error')
    return render_template('upload.html', username=session['username'])

@app.route('/download/<file_id>')
def download(file_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    result = fog.download_file(file_id, session['user_id'])
    if result['success']:
        fog.log_action(session['user_id'], 'download', result['filename'], 'success')
        return result['response']
    else:
        flash('Download failed or access denied.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete/<file_id>', methods=['POST'])
def delete(file_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    result = fog.delete_file(file_id, session['user_id'])
    if result['success']:
        flash('File deleted successfully.', 'success')
        fog.log_action(session['user_id'], 'delete', file_id, 'success')
    else:
        flash('Delete failed.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    logs = fog.get_audit_logs(session['user_id'])
    return render_template('history.html', logs=logs, username=session['username'])

@app.route('/api/status')
def status():
    """API endpoint to check fog node and cloud status"""
    return jsonify({
        'fog_node': 'online',
        'cloud_storage': fog.check_cloud_status(),
        'timestamp': datetime.utcnow().isoformat()
    })

# ─────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
