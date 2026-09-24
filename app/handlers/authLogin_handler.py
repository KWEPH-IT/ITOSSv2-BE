from flask import jsonify, request,  current_app, g, redirect, session, Response
from database import db
from app.models.itoss.tblUsers import Users
from app.models.kweph_mfa.tblConsolidated import Users_MFA
from app.models.kweph_mfa.tblSessions import MFA_Sessions
from app.services.encryption_services import hash_password
from sqlalchemy import and_, text
from app.services.jwt_validator import token_required
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
import base64
import secrets
import os
import jwt
ph_timezone = ZoneInfo("Asia/Manila")

BASE_LOG_FOLDER = "./app/logs"

def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    hash_pass = hash_password(password)
    stat = 1

    try:
        itoss_user = Users.query.filter(Users.EmployeeId == username).first()
        if itoss_user:

            user = Users_MFA.query.filter(
                and_ (
                    Users_MFA.EmployeeId == username,  
                    Users_MFA.Password == hash_pass
                    #Users_MFA.Status == stat
                )
            ).first()

            if user:
                
                #FOR MFA

                 # Generate session token
                session_token = generate_session_token()

                # Create MFA session
                create_mfa_session(
                    user.OASId,
                    session_token,
                    "ITOSSv2"
                )

                frontend_origin = request.headers.get("Origin")
                frontend_host = frontend_origin.lower().strip()

                if frontend_host.endswith("kwephilippines.ztna.safous.com"):
                    mfa_base_url = "https://mfa.kwephilippines.ztna.safous.com/"
                else:
                    mfa_base_url = "https://mfa.kwephilippines.ph/"

                if not frontend_origin:
                    return jsonify({
                        "message": "Unable to determine frontend origin",
                        "status": "error"
                    }), 400

                # Base64 values
                encrypted_oas_id = base64.b64encode(
                    user.OASId.encode("utf-8")
                ).decode("utf-8")

                system_name = base64.b64encode(
                    b"ITOSSv2"
                ).decode("utf-8")

                encrypted_token = base64.b64encode(
                    session_token.encode("utf-8")
                ).decode("utf-8")

                # Build MFA URL
                redirect_url = (
                    f"{mfa_base_url}"
                    f"?x={encrypted_oas_id}"
                    f"&s={system_name}"
                    f"&t={encrypted_token}"
                )

                return jsonify({
                    "message": "Credentials valid. MFA verification required.",
                    "status": "mfa_required",
                    "mfa_url": redirect_url
                }), 200
            else:
                return jsonify({"message": "MFA : Invalid credentials!", "status": "error"}), 401
        else:
            return jsonify({"message": "ITOSS : User does not exist!", "status": "error"}), 404
    except Exception as e:
        db.session.rollback()
        import traceback
        print("=== ERROR REQUEST ===")
        traceback.print_exc()
        return jsonify({"message": str(e), "status": "error"}), 500

@token_required
def protected_token():
    #print(">>> ROUTE HIT")

    return jsonify({
        "message": "Token is valid!",
        "user": g.payload['username']
    }), 200
    
def test_db_connection():
    try:
        # Simple raw SQL query  
        result = db.session.execute(text("SELECT 1")).scalar()
        return jsonify({"db_connection": "success", "result": result})
    except Exception as e:
        return jsonify({"db_connection": "failed", "error": str(e)}), 500
    

@token_required
def validatePass():
    user = g.payload['user_id']
    data = request.json
    password = data.get('password')
    hash_pass = hash_password(password)

    confirm = Users_MFA.query.filter(
        and_(
            Users_MFA.id == user,
            Users_MFA.Password == hash_pass
        )
    ).first()
    if confirm:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Invalid password"}), 401
    


@token_required
def logout():
    response = jsonify({
        "message": "Logged out successfully!",
        "status": "success"
    })

    response.delete_cookie(
        "access_token",
        httponly=True,
        secure=True,
        samesite="None"
    )

    return response, 200


def logger():
    data = request.json
    employee_id = data.get('employeeId')
    action = data.get('action')
    details = data.get('details', '')

    # DATE TODAY
    today = datetime.now().strftime("%Y-%m-%d")

    # TIME NOW
    current_time = datetime.now().strftime("%H:%M:%S")

    # USER FOLDER
    user_folder = os.path.join(
        BASE_LOG_FOLDER,
        employee_id
    )

    os.makedirs(user_folder, exist_ok=True)

    # DAILY FILE
    log_file = os.path.join(
        user_folder,
        f"{today}.txt"
    )

    log_line = (
        f"[{current_time}] "
        f"{action} | "
        f"{details}\n"
    )

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(log_line)

    return jsonify({
        "success": True
    }), 200


def generate_session_token():
    token_data = secrets.token_bytes(24)
    return base64.b64encode(token_data).decode("utf-8")

def create_mfa_session(oas_id, token, system_name="ITOSSv2"):
    expiration_time = datetime.now(ph_timezone) + timedelta(hours=1)

    formatted_date = expiration_time.strftime("%b %d %Y %I:%M%p")
    formatted_date = formatted_date.replace(" 0", " ")

    # Convert only AM/PM to lowercase
    if formatted_date.endswith("AM"):
        formatted_date = formatted_date[:-2] + "am"
    elif formatted_date.endswith("PM"):
        formatted_date = formatted_date[:-2] + "pm"

    session = MFA_Sessions(
        OASId=oas_id,
        SessionToken=token,
        ExpirationTime=formatted_date,
        SystemName=system_name
    )

    db.session.add(session)
    db.session.commit()



#-------------------------------------------VALIDATE JWT TOKEN FROM MFA-----------------------------------------------#

def validate_MFA_token():
    try:
        frontend_url = os.getenv('FRONT_END_URL')
        JWT_SECRET = base64.b64decode(os.getenv('JWT_SECRET'))
        token = request.form.get("token", "") 

        if not token:
            return jsonify({
                "success": False,
                "message": "No token received."
            }), 400

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )

        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "message": "Token has expired."
            }), 401

        except jwt.InvalidTokenError as e:
            return jsonify({
                "success": False,
                "message": f"Invalid token: {str(e)}"
            }), 401


        oas_id = payload.get("userid")

        if not oas_id:
            oas_id = payload.get("user_id")

        if not oas_id:
            return jsonify({
                "success": False,
                "message": "Token is valid, but no OASId found."
            }), 401


        session["OASId"] = oas_id

         # --------------------------------------------------
        # GET ITOSS USER
        # --------------------------------------------------

        user = Users_MFA.query.filter(
            Users_MFA.OASId == oas_id
        ).first()

        if not user:
            return jsonify({
                "success": False,
                "message": "ITOSS user not found."
            }), 404

        itoss_user = Users.query.filter(
            Users.EmployeeId == user.EmployeeId
        ).first()

        if not itoss_user:
            return jsonify({
                "success": False,
                "message": "ITOSS user does not exist."
            }), 404

        # --------------------------------------------------
        # CREATE ITOSSv2 JWT
        # --------------------------------------------------

        access_token = jwt.encode(
            {
                "user_id": user.id,
                "emp_id": user.EmployeeId,
                "username": itoss_user.EmployeeName,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iss": "ITOSSv2",
                "aud": "itoss-client"
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

        # --------------------------------------------------
        # SET HTTPONLY COOKIE
        # --------------------------------------------------
        
        response = Response(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Redirecting...</title>
            </head>
            <body>
                <script>
                    window.location.replace(
                        "{frontend_url}/mfa-callback?status=success&user={user.EmployeeId}"
                    );
                </script>
            </body>
            </html>
            """,
            status=200,
            mimetype="text/html"
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="None",
            max_age=3600
        )

        return response

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500