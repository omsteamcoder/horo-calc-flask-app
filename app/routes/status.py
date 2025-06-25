from flask import Blueprint, jsonify
from flask_cors import cross_origin
import time
from datetime import datetime
import importlib

status_bp = Blueprint('status', __name__)

START_TIME = time.time()

@status_bp.route('/status', methods=['GET'])
@cross_origin()
def server_status():
    uptime_seconds = round(time.time() - START_TIME)
    return jsonify({
        "message": "Server is up and running",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_seconds": uptime_seconds,
        "flask_version": importlib.metadata.version("flask"),
    })