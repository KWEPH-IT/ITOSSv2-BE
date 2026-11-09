import os
from functools import wraps
from flask import request, jsonify

SERVICE_TOKEN = os.getenv("MACHINE_TOKEN")

def service_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get("X-Service-Token") != SERVICE_TOKEN:
            return jsonify({"message": "Invalid service token"}), 401
        return f(*args, **kwargs)
    return decorated