#!/bin/bash

# Start Flask app in the background
#python app.py &
flask run &

# Save the Flask app's PID so we can kill it later
FLASK_PID=$!

# Give Flask a moment to start up
sleep 1

# Open Firefox to the Flask app's URL
open -a Firefox http://localhost:5000/

# Wait for the user to press a key before exiting
read -n 1 -s -r -p "Press any key to stop the Flask app..."

# Kill the Flask app when the user presses a key
kill $FLASK_PID

