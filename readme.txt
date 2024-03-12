### HOW TO RUN THE BONEWEB APPLICATION ###
python boneweb.py
# You may try also in the root folder if you rename boneweb.py to app.py and change some file path configuration for module imports.
flask run

# Make sure required Python dependcies are installed (at least)
Flask
Flask-SocketIO
Adafruit-BBIO

## To avoid websocket connection errors in WSGI environment, install:
pip install eventlet gevent
# Running using gunicorn
gunicorn -k eventlet -w 1 myapp:app
# or
gunicorn -k gevent -w 1 myapp:app

