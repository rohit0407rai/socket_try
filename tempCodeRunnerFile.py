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
        socketio.emit('pose_data', {'left_counter': left_counter, 'right_counter': right_counter, 'frame': frame})