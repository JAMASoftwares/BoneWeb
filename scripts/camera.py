from cv2 import VideoCapture, imencode, imwrite
from cv2 import CAP_PROP_FRAME_WIDTH, CAP_PROP_FRAME_HEIGHT
import os
from datetime import datetime
import shutil # For copying files
from flask import current_app
from PIL import Image

# Replace the below URL with your IP camera's URL
rtsp_stream_url = 'rtsp://admin:admin@194.197.66.163:8554/1/h264major'
# snapshot_uri = 'http://194.197.66.163/jpgimage/1/image.jpg'
snapshot_uri = 'http://admin:hikivisio18@192.168.1.64/ISAPI/Streaming/channels/101/picture'

def generate_frames():
    cap = VideoCapture(rtsp_stream_url)
    cap.set(CAP_PROP_FRAME_WIDTH, 640)
    cap.set(CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        success, frame = cap.read()  # Read the camera frame
        if not success:
            break
        else:
            ret, buffer = imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Concat frame one by one and show result


def capture_image():
    cap = VideoCapture(rtsp_stream_url)  # Capture from the default camera
    
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("Failed to capture image")
        return
    
    # Save original image
    temp_org_path = os.path.join(current_app.config['CAPTURES_FOLDER'], 'temp_original.jpg')
    imwrite(temp_org_path, frame)
    
    return temp_org_path


def save_image():
    img_type = 'original'
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    src_path = os.path.join(current_app.config['CAPTURES_FOLDER'], f'temp_{img_type}.jpg')
    dest_path = os.path.join(current_app.config['CAPTURES_FOLDER'], f'{img_type}_{timestamp}.jpg')
    shutil.copy(src_path, dest_path)
    image = Image.open(dest_path)
    image.thumbnail((300, 200))
    thumbnail_path = os.path.join(current_app.config['THUMBNAILS_FOLDER'], f'{img_type}_{timestamp}.jpg')
    image.save(thumbnail_path)
