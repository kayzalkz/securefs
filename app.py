import os
import base64
import cv2
import numpy as np
from flask import Flask, request, render_template, send_file, url_for, jsonify, redirect, session
import qrcode
from io import BytesIO
import logging
from datetime import datetime
import secrets

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024 * 1024  # 1 GB max file size
app.config['PROFILE_FOLDER'] = 'static/profile'
app.secret_key = secrets.token_hex(16)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Ensure the upload and profile folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROFILE_FOLDER'], exist_ok=True)

# Load the face detection cascade classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@app.route('/')
def home():
    if 'face_verified' in session:
        return redirect(url_for('index'))
    return render_template('face_scan.html')

@app.route('/face_scan')
def face_scan():
    if 'face_verified' in session:
        return redirect(url_for('index'))
    return render_template('face_scan.html')

@app.route('/verify_face', methods=['POST'])
def verify_face():
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) > 0:
            # Generate a unique filename with unit name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unit_name = secrets.token_hex(4)  # Generate a random 4-character hex string as unit name
            filename = f"captured_face_{unit_name}_{timestamp}.jpg"
            filepath = os.path.join(app.config['PROFILE_FOLDER'], filename)
            
            # Save the captured image
            cv2.imwrite(filepath, image)
            app.logger.info(f"Face detected and image saved as {filename}")
            
            # Set session variable to indicate successful face verification
            session['face_verified'] = True
            
            return jsonify({'success': True, 'redirect': url_for('index'), 'filename': filename})
        else:
            app.logger.info("No face detected")
            return jsonify({'success': False, 'error': 'No face detected'}), 400

    except Exception as e:
        app.logger.error(f"Error in verify_face: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/index')
def index():
    if 'face_verified' not in session:
        return redirect(url_for('face_scan'))
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'face_verified' not in session:
        return redirect(url_for('face_scan'))
    
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        file_url = url_for('download_file', filename=file.filename, _external=True)
        qr_url = url_for('get_qr', data=file_url, _external=True)
        return render_template('success.html', file_url=file_url, qr_url=qr_url)

@app.route('/download/<filename>')
def download_file(filename):
    if 'face_verified' not in session:
        return redirect(url_for('face_scan'))
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route('/qr')
def get_qr():
    data = request.args.get('data', '')
    img = qrcode.make(data)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

if __name__ == '__main__':
    # Check if SSL certificate and key files exist
    cert_file = 'cert.pem'
    key_file = 'key.pem'

    if os.path.exists(cert_file) and os.path.exists(key_file):
        app.run(debug=True, host='0.0.0.0', port=5000, ssl_context=(cert_file, key_file))
    else:
        print("SSL certificate files not found. Please generate them first.")
        print("Run the following command to generate self-signed certificates:")
        print("openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365")
        exit(1)
