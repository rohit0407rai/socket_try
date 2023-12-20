import base64
import os

import cv2
import numpy as np
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import mediapipe as mp
from flask_cors import CORS

app = Flask(__name__, static_folder="static")
CORS(app, origins="*")
socketio = SocketIO(app,cors_allowed_origins="*")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


def base64_to_image(base64_string):
    image_data = base64.b64decode(base64_string.split(',')[1])
    nparr = np.frombuffer(image_data, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


@socketio.on("connect")
def test_connect():
    print("Connected")
    emit("my response", {"data": "Connected"})


# @socketio.on("img")
# def rec_image(image):
#     print("started")
#     # Decode the base64-encoded image data
#     image = base64_to_image(image)

#     gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

#     frame_resized = cv2.resize(gray, (640, 360))

#     encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

#     result, frame_encoded = cv2.imencode(".jpg", frame_resized, encode_param)

#     processed_img_data = base64.b64encode(frame_encoded).decode()

#     b64_src = "data:image/jpg;base64,"
#     processed_img_data = b64_src + processed_img_data

#     emit("processed_image", processed_img_data)


# @app.route("/")
# def index():
#     return render_template("main.html")


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Curl counter variables for left and right hands
left_counter = 0
left_stage = None
left_prev_stage = None

right_counter = 0
right_stage = None
right_prev_stage = None

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle



@socketio.on('image')
def receive_image(image_data):
    image = base64_to_image(image_data)

    global left_counter, right_counter, left_stage, left_prev_stage, right_stage, right_prev_stage

    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        # Make detection
        results = pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        try:
            landmarks = results.pose_landmarks.landmark

            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            shoulder1 = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                        landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbow1 = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wrist1 = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                    landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

            angle_left = calculate_angle(shoulder, elbow, wrist)
            angle_right = calculate_angle(shoulder1, elbow1, wrist1)

            # Curl counter logic for left hand
            if angle_left > 160:
                left_stage = "down"
            if (angle_left < 30) and left_stage == 'down' and left_prev_stage != 'up':
                left_stage = "up"
                left_counter += 1
                print(f"Left Counter: {left_counter}")

            # Curl counter logic for right hand
            if angle_right > 160:
                right_stage = "down"
            if (angle_right < 30) and right_stage == 'down' and right_prev_stage != 'up':
                right_stage = "up"
                right_counter += 1
                print(f"Right Counter: {right_counter}")

            left_prev_stage = left_stage
            right_prev_stage = right_stage

        except Exception as e:
            print(f"Error: {e}")

        # Render curl counter
        cv2.rectangle(image, (0, 0), (225, 73), (245, 117, 16), -1)

        # Rep data
        cv2.putText(image, 'RIGHT REPS', (15, 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, str(left_counter),
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.putText(image, 'LEFT REPS', (15, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(image, str(right_counter),
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2, cv2.LINE_AA)

        # Render detections
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                  mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                  mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))

        ret, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()
        img_data = base64.b64encode(frame).decode()
        b64_src = "data:image/jpg;base64,"
        processed_img_data = b64_src + img_data
        socketio.emit('pose_data', {'left_counter': left_counter, 'right_counter': right_counter, 'frame': processed_img_data})
# Import statements ...

@app.route("/generate_frames", methods=["POST"])
def trigger_generate_frames():
    socketio.emit('image')  # Emit the 'cprocess' event to trigger generate_frames
    return "Frames generation triggered"

# Other route and function definitions ...

if __name__ == "__main__":
    # Use a different port if 5000 is already in use
    port = int(os.environ.get("PORT", 5000))

    # Use '127.0.0.1' instead of '0.0.0.0' for local development
    host = '127.0.0.1'

    # Set debug to True for development and allow_unsafe_werkzeug to suppress the runtime error
    socketio.run(app, debug=False, port=port, host=host, allow_unsafe_werkzeug=True,log_output=True)
