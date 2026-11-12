
from functools import wraps
from flask import request, jsonify, current_app, g
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.cookies.get("access_token")

        if not token:
            current_app.logger.warning(
                "AUTH FAILED: access_token cookie missing. "
                "Path=%s Origin=%s",
                request.path,
                request.headers.get("Origin")
            )

            return jsonify({
                "message": "Token is missing!",
                "error": "MISSING_COOKIE"
            }), 401

        try:
            g.payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=["HS256"],
                audience="itoss-client",
                issuer="ITOSSv2"
            )

            current_app.logger.info(
                "AUTH SUCCESS: EmployeeId=%s",
                g.payload.get("emp_id")
            )

        except jwt.ExpiredSignatureError:
            current_app.logger.warning("AUTH FAILED: JWT expired")

            return jsonify({
                "message": "Token has expired!",
                "error": "TOKEN_EXPIRED"
            }), 401

        except jwt.InvalidAudienceError:
            current_app.logger.error("AUTH FAILED: Invalid audience")
            return jsonify({
                "message": "Invalid audience!",
                "error": "INVALID_AUDIENCE"
            }), 403

        except jwt.InvalidIssuerError:
            current_app.logger.error("AUTH FAILED: Invalid issuer")
            return jsonify({
                "message": "Invalid issuer!",
                "error": "INVALID_ISSUER"
            }), 403

        except jwt.InvalidTokenError as e:
            current_app.logger.error(
                "AUTH FAILED: Invalid JWT - %s", repr(e)
            )

            return jsonify({
                "message": "Invalid token!",
                "error": "INVALID_TOKEN"
            }), 403

        except Exception:
            current_app.logger.exception(
                "AUTH FAILED: Unexpected token validation error"
            )

            return jsonify({
                "message": "Token validation failed",
                "error": "VALIDATION_ERROR"
            }), 403

        return f(*args, **kwargs)

    return decorated
