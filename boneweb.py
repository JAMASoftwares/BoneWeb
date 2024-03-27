import re, os
import psutil
from flask import Flask, render_template, request, session, send_from_directory, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from threading import Lock
from datetime import datetime

# Assuming __init__.py and scripts are properly set up
from __init__ import GPIO_DICT_P9, GPIO_DICT_P8, AIN_DICT
from scripts.readin import readPinValuesInt, readPinValues
from scripts.sysinfo import get_cpu_info_as_dict, get_disk_info_as_dict, get_net_info_as_dict
from scripts.camera import capture_image, save_image

#########
# SETUP #
#########
app = Flask(__name__, static_url_path='/static')
CORS(app, resources={r"/hls/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'secret!'
app.config['CAPTURES_FOLDER'] = 'captures'
app.config['THUMBNAILS_FOLDER'] = os.path.join(app.config['CAPTURES_FOLDER'], 'thumbnails')
# Ensure the captures and thumbnails folders exist
os.makedirs(app.config['CAPTURES_FOLDER'], exist_ok=True)
os.makedirs(app.config['THUMBNAILS_FOLDER'], exist_ok=True)

socketio = SocketIO(app, debug=True, cors_allowed_origins='*')

# Global variables to track background tasks
sensor_task_running = False
cpuram_task_running = False
background_thread_lock = Lock()

def get_current_datetime():
    """Get current date and time."""
    return datetime.now().strftime("%M:%S")

####################
# BACKGROUND TASKS #
####################
def handle_background_threads(sensors=False):
    # Handle background tasks for connected clients
    global sensor_task_running, cpuram_task_running
    
    with background_thread_lock:
        # Start sensor values background task if not already running
        if not sensor_task_running and sensors:
            sensor_task_running = True
            socketio.start_background_task(sensor_values_background_thread)
        # Start CPU-RAM background task if not already running
        if not cpuram_task_running:
            cpuram_task_running = True
            socketio.start_background_task(cpu_ram_background_thread)

def sensor_values_background_thread():
    """Background task for reading sensor values."""
    global sensor_task_running
    print("Sensor values background task started.")
    while sensor_task_running:
        pins = list(AIN_DICT.keys())
        pin_volts = readPinValuesInt(pins)
        data = {'labels': pins, 'values': [v for _, v in pin_volts]}
        socketio.emit('sensor_data', {"date": get_current_datetime(), 'data': data})
        socketio.sleep(1)
        
def cpu_ram_background_thread():
    """Background task for CPU and RAM usage."""
    global cpuram_task_running
    print("CPU-RAM usage background task started.")
    while cpuram_task_running:
        # Reading CPU and RAM usage
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        socketio.emit('cpuram_data', {'cpu_usage': cpu_usage, 'ram_usage': ram_usage})
        socketio.sleep(3)  # Adjust sleep time as needed

############
# SocketIO #
############
@socketio.on('connect')
def on_connect():
    """Handle client connection."""
    client_id = request.sid
    client_name = request.args.get('clientName', 'Unknown')
    client_type = request.args.get('clientType', 'Default')
    device_info = request.args.get('deviceInfo', 'Unknown')
    print(f"Client connected: {client_name} (Session ID: {client_id}) {device_info}")
    # Storing client name in session for possible later use
    session['client_name'] = client_name
    # Ensure necessary background tasks are running
    if client_type == 'sensors':
        handle_background_threads(sensors=True)
    else:
        handle_background_threads()
    

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection."""
    client_id = request.sid
    client_name = session.get('client_name', 'Unknown Client')  # Retrieving client name from session
    print(f"Client disconnected: {client_name} (Session ID: {client_id})")

################ 
# HTTP ROUTING #
################
@app.route("/")
def index():
    # Read Pin States
    # P9
    gpioDataP9 = {}

    for key, values in GPIO_DICT_P9.items():
        f = open(values["path"] + "/value", "r")
        value = f.read()[:-1]
        f.close()
        f = open(values["path"] + "/direction", "r")
        direction = f.read()[:-1]
        f.close()
        gpioDataP9[key] = (direction, values["io"], value, values["switch"])
    # P8
    gpioDataP8 = {}
    for key, values in GPIO_DICT_P8.items():
        f = open(values["path"] + "/value", "r")
        value = f.read()[:-1]
        f.close()
        f = open(values["path"] + "/direction", "r")
        direction = f.read()[:-1]
        f.close()
        gpioDataP8[key] = (direction, values["io"], value, values["switch"])

    templateData = {}
    templateData["P9"] = gpioDataP9
    templateData["P8"] = gpioDataP8

    return render_template("index.html", result=templateData)


@app.route("/<deviceName>/<action>")
def action(deviceName, action):
    print(deviceName, action)
    if re.match(r"P9", deviceName):
        gpio_path = GPIO_DICT_P9[deviceName]["path"]
    elif re.match(r"P8", deviceName):
        gpio_path = GPIO_DICT_P8[deviceName]["path"]
    else:
        print(f'Trying to use path "{deviceName}/{action}" in @app.route("/<deviceName>/<action>")')

    if deviceName == bool(re.fullmatch(r"P9_\d{1,2}", deviceName)):
        actuator = deviceName
        print("Actuator set: " + str(actuator))

    # On/Off functions are not used (localhost:8020/P9_14/on)
    templateData = {"pin": deviceName}
    if action == "on":
        print("Alert: Action 'on' not available")
        # f.write("1")
    if action == "io":
        f = open(gpio_path + "/direction", "r")
        io_state = str(f.read()[:-1])
        io_state = "in" if io_state == "out" else "out"
        templateData["state"] = io_state
        f.close()
        f = open(gpio_path + "/direction", "w")
        f.write(io_state)
        f.close()
        if io_state == "out":
            f = open(gpio_path + "/value", "w")
            f.write("0")
            f.close()
    if action == "toggle":
        f = open(gpio_path + "/value", "r")
        pin_state = int(f.read()[:-1])
        pin_state = str(int(not pin_state))
        templateData["state"] = pin_state
        f.close()
        f = open(gpio_path + "/value", "w")
        f.write(pin_state)
        f.close()

    return templateData
    # return render_template("index.html", result=templateData)


@app.route("/voltage/ain")
def voltage():
    pins = list(AIN_DICT.keys())
    print("Reading Voltages: ", pins)
    pin_volts = readPinValues(pins)
    templateData = {"volts": pin_volts}

    return templateData


@app.route("/voltage/chart")
def voltage_chart():
    pins = list(AIN_DICT.keys())
    print("Reading Voltages: ", pins)
    pin_volts = readPinValuesInt(pins)

    templateData = {
        'labels': pins,
        'values': [v for p, v in pin_volts]
    }

    return templateData

@app.route("/sysinfo_json")
def get_sysinfo():
    cpu_info = get_cpu_info_as_dict()
    disk_info = get_disk_info_as_dict()
    net_info = get_net_info_as_dict()
    print("Getting system info...")

    templateData = {
        'cpu_info': cpu_info,
        'dev_info': disk_info,
        'net_info': net_info
    }

    return templateData

@app.route("/sysinfo")
def sysinfo():
    cpu_info = get_cpu_info_as_dict()
    disk_info = get_disk_info_as_dict()
    net_info = get_net_info_as_dict()
    print("Getting system info...")
    dict3D = {
        'cpu_info': cpu_info,
        'dev_info': disk_info,
        'net_info': net_info
    }
    # Assuming dict3D is your 3D dictionary
    # Preprocess dict3D to determine column headers for each layer
    headers_per_layer = {}
    for layer_key, layer_value in dict3D.items():
        for item in layer_value.values():
            if isinstance(item, dict):
                headers_per_layer[layer_key] = list(item.keys())
                break  # Here you can use 'break' since this is Python code

    # Render your template, passing both the original dictionary and the preprocessed headers
    return render_template('sysinfo.html', dict3D=dict3D, headers_per_layer=headers_per_layer)

@app.route('/webcam')
def webcam():
    return render_template('webcam.html')

@app.route('/camera')
def camera():
    # This should end sensor readings to save resources for image processing
    handle_background_threads(sensors=False)
    # Capture new images upon navigating to the page
    image_path = capture_image()
    path_dict = {'org_path': image_path}
    thumbs = os.listdir(app.config['THUMBNAILS_FOLDER'])
    
    return render_template('camera.html', thumbnails=thumbs, paths=path_dict)

@app.route('/captures/<filename>')
def serve_capture(filename):
    return send_from_directory(app.config['CAPTURES_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def serve_thumbnail(filename):
    return send_from_directory(app.config['THUMBNAILS_FOLDER'], filename)

@app.route('/capture-image', methods=['POST'])
def capture_image_route():
    # Capture new images upon navigating to the page
    image_path = capture_image() 
    path_dict = {'org_path': image_path}
    # Assuming capture_images returns a dict with filenames of the captured images
    return path_dict

@app.route('/save-image', methods=['POST'])
def save_image_route():
    # Save temp image
    save_image()
    # Capture new images upon navigating to the page
    image_path = capture_image()
    path_dict = {'org_path': image_path}

    return path_dict

@app.route('/list_images')
def list_images():
    img_path = os.listdir(app.config['THUMBNAILS_FOLDER'])
    images = [f for f in img_path if f.endswith('.jpg')]
    images.sort(reverse=True)  # Show newest images first
    
    return jsonify(images=images)


@app.route('/hls/<path:filename>')
def serve_hls(filename):
    return send_from_directory('static/hls', filename)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8020, debug=True)

# if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=8020, debug=True)
