from database import db
from app.models.itoss.tblConfigSystemProfile import SystemProfile
from flask import jsonify, request, g
from app.services.jwt_validator import token_required
from datetime import datetime
import pytz
# Philippine timezone
ph_tz = pytz.timezone("Asia/Manila")

# Current PH time
now_ph = datetime.now(ph_tz)

# Format to YYYY-MM-DD
formatted_date = now_ph.strftime("%Y-%m-%d")

@token_required
def fetchAllSystems():
    try:
        systems = SystemProfile.query.all()

        if not systems:
            return jsonify({"error": "No systems found"}), 404  # Not Found is more appropriate

        return jsonify([system.to_dict() for system in systems]), 200

    except Exception as e:
        import traceback
        print("=== ERROR CREATING CATEGORIES ===")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
        # return jsonify({"error": f"Error fetching systems: {str(e)}"}), 500

@token_required
def createNewProfile():
     
    data = request.json
    # Get username from the decoded token
    current_user = g.payload['username']
    status = "1"
    
    valid_fields = {col.name for col in SystemProfile.__table__.columns}
    filtered_data = {k: v for k, v in data.items() if k in valid_fields}

    existing = SystemProfile.query.filter(SystemProfile.SystemName == filtered_data.get("SystemName")).first()
    if existing:
        return jsonify({"error": "System name already exists"}), 409

    system = SystemProfile(**filtered_data, CreatedBy=current_user, Status = status)
    db.session.add(system)
    db.session.commit()


    return jsonify({"message": "System profile created", "creator": current_user}), 200

@token_required
def updateProfile():
    try:
        data = request.get_json()
        SystemId = data.get("SystemId")

        system = SystemProfile.query.get(SystemId)
        if not system:
            return jsonify({"message": "System profile not found"}), 404

        updating_fields = [
            "SystemName", "SystemAlias", "SourceCodeServer", "DBServerName", "DBName",
            "DBUsername", "DBPassword", "DBTableName", "DBType", "DBTableIdentifier",
            "DBPasswordColName", "DBStatusColName", "FieldsToRemove", "Remarks", "Status", "SourceCodePath",
            "BackupPath", "ScheduleType", "ScheduleTime", "BackupDay"
        ]

        for field in updating_fields:
            if field in data:
                setattr(system, field, data[field])

        system.ModifiedBy = g.payload['username']
        system.DateModified = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S") 
        db.session.commit()

        return jsonify({"message": "System profile updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()  # see full error in logs
        return jsonify({
            "message": "Error updating system profile",
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500
        

