### HOW TO RUN THE BONEWEB APPLICATION ###
python boneweb.py

# Make sure required Python dependcies are installed (at least)
Flask
Flask-SocketIO
Adafruit-BBIO

## To avoid websocket connection errors in WSGI environment install:
pip install eventlet gevent
# Running using gunicorn
gunicorn -k eventlet -w 1 myapp:app
# or
gunicorn -k gevent -w 1 myapp:app

## !IMPORTANT
1. VIRTUAL ENVIRONMENTS CANNOT BE USED because Adafruit_BBIO works only in the root directory
2. If you use flask as below you have to reconfigure import paths in app.py
    flask run
3. Also, when running successfully using "flask run", the page is not available via browser
    http://127.0.0.1:5000 (produces page not found error)

# Useful commands (remove folders)
rm -rf <directory>
