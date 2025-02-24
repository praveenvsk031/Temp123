from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import cv2
from werkzeug.utils import secure_filename
from deepfake_detector import DeepFakeDetector
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this to a secure secret key in production

# Configure upload folders
UPLOAD_FOLDER = 'static/uploads'
FRAME_FOLDER = 'static/frames'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAME_FOLDER, exist_ok=True)

# Load the model
try:
    detector = DeepFakeDetector("model.keras")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    detector = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        logger.debug("Analyze endpoint called")
        
        if 'video' not in request.files:
            logger.error("No video file in request")
            return jsonify({'error': 'No video file uploaded'}), 400
        
        video_file = request.files['video']
        
        if video_file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No selected file'}), 400

        if not allowed_file(video_file.filename):
            logger.error(f"Invalid file type: {video_file.filename}")
            return jsonify({'error': 'Invalid file type. Allowed types: mp4, avi, mov, wmv'}), 400

        # Save uploaded video
        video_filename = secure_filename(video_file.filename)
        video_path = os.path.join(UPLOAD_FOLDER, video_filename)
        logger.debug(f"Saving video to: {video_path}")
        video_file.save(video_path)

        # Extract first frame
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            logger.error("Could not read video frame")
            os.remove(video_path)  # Clean up
            return jsonify({'error': 'Could not read video frame'}), 400

        # Save frame for display
        frame_filename = f"frame_{video_filename}.jpg"
        frame_path = os.path.join(FRAME_FOLDER, frame_filename)
        logger.debug(f"Saving frame to: {frame_path}")
        cv2.imwrite(frame_path, frame)

        if detector is None:
            logger.error("Detector not initialized")
            return jsonify({'error': 'Detector not initialized'}), 500

        # Get prediction
        try:
            result, confidence = detector.predict_frame(frame)
            logger.debug(f"Prediction result: {result}, confidence: {confidence}")
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return jsonify({'error': 'Error during prediction'}), 500

        # Clean up
        os.remove(video_path)

        return jsonify({
            'prediction': result,
            'confidence': confidence,
            'frame': frame_filename
        })

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)