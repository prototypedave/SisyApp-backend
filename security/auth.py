from functools import wraps
from flask import g, jsonify
from ..services.auth import get_session_from_token
from flask import request

def get_bearer_token():
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:].strip()
    if not token:
        return None

    return token


def require_auth(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return jsonify({"message": "Authentication required."}), 401

        session = get_session_from_token(token)
        if session is None:
            return jsonify({"message": "Authentication required."}), 401

        user = session.user
        if user is None:
            return jsonify({"message": "Authentication required."}), 401

        if not user.is_active:
            return jsonify({"message": "Authentication required."}), 401

        g.current_user = user
        g.current_session = session

        return view_function(*args, **kwargs)

    return wrapper