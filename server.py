from flask import Flask, request, jsonify, render_template
from PIL import Image
import io
import base64
import numpy as np
import cv2
import os
import pickle
import face_recognition_api
import face_recognition
from flask_cors import CORS
import subprocess
from imutils import face_utils
import dlib

app = Flask(__name__)
CORS(app)

# Load Dlib face detector and shape predictor
p = "models\shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(p)

# Load Face Recogniser classifier
classifier_filename = 'classifier.pkl'
if os.path.isfile(classifier_filename):
    with open(classifier_filename, 'rb') as f:
        (le, clf) = pickle.load(f)
else:
    print(f"Classifier '{classifier_filename}' does not exist.")
    quit()

# Initialize trackers
faceTrackers = {}
currentFaceID = 0
def track_faces(frame):
    global currentFaceID
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    tracked_faces = []

    # Update existing trackers
    for fid in list(faceTrackers.keys()):
        tracking_quality = faceTrackers[fid].update(frame)
        if tracking_quality < 7:
            del faceTrackers[fid]  # Remove poor quality trackers

    # Detect faces in every frame (or modify as needed)
    faces = detector(gray, 0)
    for rect in faces:
        matchedFid = None
        x_bar = (rect.left() + rect.right()) // 2
        y_bar = (rect.top() + rect.bottom()) // 2

        # Check for a matching tracker
        for fid in faceTrackers.keys():
            tracked_position = faceTrackers[fid].get_position()
            t_x = int(tracked_position.left())
            t_y = int(tracked_position.top())
            t_w = int(tracked_position.width())
            t_h = int(tracked_position.height())
            t_x_bar = t_x + t_w // 2
            t_y_bar = t_y + t_h // 2

            # Check for overlap
            if ((t_x <= x_bar <= (t_x + t_w)) and (t_y <= y_bar <= (t_y + t_h))):
                matchedFid = fid
                break

        if matchedFid is None:
            # Create a new tracker
            tracker = dlib.correlation_tracker()
            tracker.start_track(frame, rect)
            faceTrackers[currentFaceID] = tracker
            currentFaceID += 1

    # Collect tracked face positions
    for fid in faceTrackers.keys():
        tracked_position = faceTrackers[fid].get_position()
        tracked_faces.append((fid, (int(tracked_position.left()), int(tracked_position.top()),
                                    int(tracked_position.width()), int(tracked_position.height()))))

    return tracked_faces


@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()  
        image_data = data['image']
        image_data = image_data.split(',')[1]  # Extracts the actual Base64-encoded image data
        image_bytes = base64.b64decode(image_data)  # Decodes the Base64-encoded image data into binary
        image = Image.open(io.BytesIO(image_bytes))  # Loads the binary data into a Pillow image object

        # Convert image to array and perform face recognition
        open_cv_image = np.array(image.convert('RGB'))  # Convert to NumPy array

        # Track faces
        tracked_faces = track_faces(open_cv_image)

        # Perform face recognition
        small_frame = cv2.resize(open_cv_image, (0, 0), fx=0.25, fy=0.25)
        face_locations = face_recognition_api.face_locations(small_frame)
        face_encodings = face_recognition_api.face_encodings(small_frame, face_locations)
        gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)  # Convert image to grayscale
        rects = detector(gray, 0)  # Detect faces using dlib's detector

        # Draw tracked face rectangles
        for fid, (x, y, w, h) in tracked_faces:
            cv2.rectangle(open_cv_image, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Blue for tracked faces

        for encoding, (top, right, bottom, left), rect in zip(face_encodings, face_locations, rects):
            # Get landmarks for the detected face
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            # Draw landmarks on the image
            for (x, y) in shape:
                cv2.circle(open_cv_image, (x, y), 2, (0, 255, 0), -1)

        predictions = []
        if len(face_encodings) > 0:
            closest_distances = clf.kneighbors(face_encodings, n_neighbors=1)
            is_recognized = [closest_distances[0][i][0] <= 0.5 for i in range(len(face_locations))]
            predictions = [(le.inverse_transform([int(pred)])[0].title() if rec else "Unknown", loc) for pred, loc, rec in
                           zip(clf.predict(face_encodings), face_locations, is_recognized)]

        # Draw rectangles around recognized faces
        for name, (top, right, bottom, left) in predictions:
            top *= 4  # Scale back up face locations since the frame was downscaled
            right *= 4
            bottom *= 4
            left *= 4

            #if name == "Unknown":
                # Draw a red rectangle for unknown faces
                #cv2.rectangle(open_cv_image, (left, top), (right, bottom), (0, 0, 255), 2)  # Red
            #else:
                # Draw a green rectangle for recognized faces
                #cv2.rectangle(open_cv_image, (left, top), (right, bottom), (0, 0, 255), 2)  # Green

            # Draw a label with the name below the face
            cv2.rectangle(open_cv_image, (left, bottom - 35), (right, bottom), (255, 0, 0), cv2.FILLED)  # Green background
            font = cv2.FONT_HERSHEY_DUPLEX  # Font for text
            font_scale = 1.5  # Scale for font size
            thickness = 2  # Thickness for bold effect
            text_color = (255, 255, 255)  # Dark gray text
            cv2.putText(open_cv_image, name, (left + 6, bottom - 6), font, font_scale, text_color, thickness)

        # Convert processed image back to PIL for response
        processed_image = Image.fromarray(open_cv_image)

        # Processed image creation
        buffer = io.BytesIO()
        processed_image.save(buffer, format="JPEG")
        processed_image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return jsonify({
            'processed_image': f'data:image/jpeg;base64,{processed_image_data}',
            'predictions': predictions
        })

    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/capture_unknown', methods=['POST'])
def capture_unknown():
    data = request.get_json()
    image_data = data['image']
    image_data = image_data.split(',')[1]  # Base64 decode
    image_bytes = base64.b64decode(image_data)
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to NumPy array
    open_cv_image = np.array(image.convert('RGB'))
    small_frame = cv2.resize(open_cv_image, (0, 0), fx=0.25, fy=0.25)

    # Find face locations and encodings
    face_locations = face_recognition.face_locations(small_frame)
    face_encodings = face_recognition.face_encodings(small_frame, face_locations)

    unknown_face_image = None

    if len(face_encodings) > 0:
        closest_distances = clf.kneighbors(face_encodings, n_neighbors=1)
        is_recognized = [closest_distances[0][i][0] <= 0.5 for i in range(len(face_locations))]

        for i, (loc, rec) in enumerate(zip(face_locations, is_recognized)):
            if not rec:  # Only for unknown faces
                top, right, bottom, left = loc
                top *= 4  # Scale up
                right *= 4
                bottom *= 4
                left *= 4

                unknown_face = open_cv_image[top:bottom, left:right]
                pil_unknown_face = Image.fromarray(unknown_face)
                buffer = io.BytesIO()
                pil_unknown_face.save(buffer, format="JPEG")
                unknown_face_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
                unknown_face_image = f'data:image/jpeg;base64,{unknown_face_image}'
                break  # Only capture one unknown face

    return jsonify({'unknown_face_image': unknown_face_image})

@app.route('/save_image', methods=['POST'])
def save_image():
    global clf, le  # Make classifier and label encoder global so they can be updated

    try:
        data = request.get_json()
        image_data = data['image'].split(',')[1]  
        username = data['username']
       
        directory = os.path.join('training-images', username)
        os.makedirs(directory, exist_ok=True)

        # Decode Base64 image data
        image_bytes = base64.b64decode(image_data)

        # Determine the filename and save 3 copies (e.g., anuj1.jpg, anuj2.jpg, anuj3.jpg)
        existing_files = os.listdir(directory)
        image_count = len(existing_files) + 1  # Count existing images for unique naming

        for i in range(1, 6):  # Save 3 copies
            image_filename = os.path.join(directory, f'{username}{image_count}_{i}.jpg')
            with open(image_filename, 'wb') as f:
                f.write(image_bytes)

        # Call the external Python scripts for creating encodings and training the model
        try:
            subprocess.run(['python3', 'create_encodings.py'])
            subprocess.run(['python3', 'train.py'])
            print('Scripts executed successfully')
            
            # Reload the classifier after training
            classifier_filename = 'classifier.pkl'
            if os.path.isfile(classifier_filename):
                with open(classifier_filename, 'rb') as f:
                    (le, clf) = pickle.load(f)
                print(f"Classifier reloaded successfully. Classes: {le.classes_}")

        except Exception as e:
            print(f'Error executing scripts or reloading model: {e}')
            return jsonify({'error': str(e)}), 500

        return jsonify({'message': 'Image saved and model updated successfully'}), 200
    except Exception as e:
        print(f'Error saving image: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
