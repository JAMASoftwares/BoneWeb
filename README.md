# BoneWeb
Python Flask/Flask SocketIO web server and client to control GPIO pins of the Beaglebone Black. System status information, CPU and RAM usage, analog-in voltage streaming through websocket connection to client. General system information easily accessible through this website.


### HOW TO RUN THE BONEWEB APPLICATION ###
`python boneweb.py`
You may try also in the root folder if you rename boneweb.py to app.py and change some file path configuration for module imports.
`flask run`

Make sure required Python dependcies are installed (at least)
- `pip install Flask`
- `pip install Flask_SocketIO`
- `pip install Adafruit_BBIO`

To avoid websocket connection errors in WSGI environment, install:
- `pip install eventlet gevent`
Running using gunicorn
- `gunicorn -k eventlet -w 1 myapp:app`
or
- `gunicorn -k gevent -w 1 myapp:app`
