from database import db
from app.models.itoss.tblConfigTicketCategories import TicketCategory
from app.models.itoss.tblConfigTicketCustomFields import TicketCustomFields
from app.models.itoss.tblConfigTicketCategApprover import TicketApproverLevel
from app.models.itoss.tblConfigTicketAssignment import TicketAssignment
from flask import jsonify, request, g
from app.services.jwt_validator import token_required
from datetime import datetime
import pytz
import json
from sqlalchemy import text
# Philippine timezone
ph_tz = pytz.timezone("Asia/Manila")

# Current PH time
now_ph = datetime.now(ph_tz)

# Format to YYYY-MM-DD
formatted_date = now_ph.strftime("%Y-%m-%d")

@token_required
def fetchAllTicketCateg():
    try:
        print("here")
        categs = TicketCategory.query.all()

        if not categs:
            return jsonify({"error": "No ticket categories found"}), 404  # Not Found is more appropriate
     
        return jsonify([categ.to_dict() for categ in categs]), 200

    except Exception as e:
        import traceback
        print("=== ERROR FETCHING CATEGORIES ===")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
    

@token_required
def createTicketCateg():
    try:
        data = request.get_json()

        name = data.get("name")
        parent_id = data.get("ParentId")
        inhouse = data.get("Inhouse")
        description = data.get("Description")
        IsSNConnected = data.get("IsSNConnected")
        custom_fields = data.get("CustomFields", [])
        approvers = data.get("ApproverLevel", [])
        assignments = data.get("Assignment", [])
        current_user = g.payload['username']

        #CreateCategory 
        category = TicketCategory(Name=name, ParentId=parent_id, IsSNConnected=IsSNConnected, Inhouse=inhouse, Description=description, CreatedBy=current_user)

        db.session.add(category)
        db.session.flush()  # get category.SystemId

        category_id = category.SystemId

        for field in custom_fields:
            static_options = field.get('StaticOptions')

            new_field = TicketCustomFields(
                CategoryId = category_id,
                FieldName = field.get("FieldName"),
                FieldType = field.get("FieldType"),
                FieldLabel = field.get("FieldLabel"),
                ValueMode = field.get("ValueMode"),
                IsGroup = field.get("IsGroup"),
                GroupName = field.get("GroupName"),
                IsRepeatable = field.get("IsRepeatable"),
                SelectSourceType = field.get("SelectSourceType"),
                TableName = field.get("TableName"),
                LabelColumn = field.get("LabelColumn"),
                ValueColumn = field.get("ValueColumn"),
                StaticOptions = json.dumps(static_options),
                CreatedBy=current_user
            )
            db.session.add(new_field)

        for approver in approvers:
            new_approver = TicketApproverLevel(
                CategoryId = category_id,
                LevelNo = approver.get("LevelNo"),
                ApproverType = approver.get("ApproverType"),
                ApproverValue = approver.get("ApproverValue"),
                Description = approver.get("Description"),
                CreatedBy = current_user
            )
            db.session.add(new_approver)

        for assignment in assignments:
            new_assignment = TicketAssignment(
                CategoryId=category_id,
                EmployeeId=assignment.get("AssignmentId"),
                EmployeeName=assignment.get("AssignmentName"),
                EmailAddress=assignment.get("AssignmentEmail"),
                CreatedBy = current_user
            )
            db.session.add(new_assignment)

        db.session.commit()

        return jsonify({
            "message": "Ticket category created successfully!"
        }), 200
    
    except Exception as e:
        import traceback
        print("=== ERROR CREATING CATEGORIES ===")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
    
@token_required
def updateTicketCateg():
    try:
        data = request.get_json()
        systemId = data.get('systemId')
        current_user = g.payload['username']
        custom_fields = data.get("CustomFields", [])
        approvers = data.get("ApproverLevel", [])
        assignments = data.get("Assignment", [])
        
        print("Approvers:", approvers)

        category = TicketCategory.query.filter(TicketCategory.SystemId == systemId).first()

        if not category:
            return jsonify({"error": "No category found"}), 404
        
        category.Name = data.get('name')
        category.ParentId = data.get('ParentId')
        category.Description = data.get('Description')
        category.IsSNConnected = data.get('IsSNConnected')
        category.Inhouse = data.get("Inhouse")
        category.Date_Modified = formatted_date
        category.Modified_By = current_user

        #Delete old custom fields
        TicketCustomFields.query.filter(TicketCustomFields.CategoryId == systemId).delete(synchronize_session=False)

        #Insert new custom fields
        for field in custom_fields:
            static_options = field.get('StaticOptions')
            new_field = TicketCustomFields(
                CategoryId = systemId,
                FieldName = field.get("FieldName"),
                FieldType = field.get("FieldType"),
                FieldLabel = field.get("FieldLabel"),
                ValueMode = field.get("ValueMode"),
                IsGroup = field.get("IsGroup"),
                GroupName = field.get("GroupName"),
                IsRepeatable = field.get("IsRepeatable"),
                SelectSourceType = field.get("SelectSourceType"),
                TableName = field.get("TableName"),
                LabelColumn = field.get("LabelColumn"),
                ValueColumn = field.get("ValueColumn"),
                StaticOptions = json.dumps(static_options),
                CreatedBy=current_user
            )
            db.session.add(new_field)

        #Delete old approvers
        TicketApproverLevel.query.filter(TicketApproverLevel.CategoryId == systemId).delete(synchronize_session=False)

        #Insert new approvers
        for approver in approvers:
            new_approver = TicketApproverLevel(
                CategoryId = systemId,
                LevelNo = approver.get("LevelNo"),
                ApproverType = approver.get("ApproverType"),
                ApproverValue = approver.get("ApproverValue"),
                Description = approver.get("Description"),
                CreatedBy = current_user
            )
            db.session.add(new_approver)

        #Delete old assignments
        TicketAssignment.query.filter(TicketAssignment.CategoryId == systemId).delete(synchronize_session=False)

        for assignment in assignments:
            new_assignment = TicketAssignment(
                CategoryId=systemId,
                EmployeeId=assignment.get("AssignmentId"),
                EmployeeName=assignment.get("AssignmentName"),
                EmailAddress=assignment.get("AssignmentEmail"),
                CreatedBy = current_user
            )
            db.session.add(new_assignment)

        db.session.commit()
        db.session.flush()

        return jsonify({
            "message": "Ticket category updated successfully!"
        }), 200
    except Exception as e:
        import traceback
        print("=== ERROR UPDATING CATEGORIES ===")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
    

def get_options():
    data = request.json
    table = data.get("TableName")
    value_col = data.get("ValueColumn")
    label_col = data.get("LabelColumn")

    

    
    if table == "vwAtKWE":
        query = text(f"SELECT {value_col} as value, {label_col} as label FROM {table} WHERE Tag = 'Active' order by {label_col} ")
        engine = db.engines["hris_db"]      # or db.get_engine(bind="hris_db")
    else:
        query = text(f"SELECT {value_col} as value, {label_col} as label FROM {table} order by {label_col}")
        engine = db.engine                  # default ITOSS database

    with engine.connect() as conn:
        result = conn.execute(query)
        options = [
            {"value": row.value, "label": row.label}
            for row in result
        ]

    # result = db.session.execute(query)

    # options = [{"value": row.value, "label": row.label} for row in result]
    print(f"Total options: {len(options)}")
    print(query)
    return jsonify(options)

@token_required
def fetchAllTicketApprover():
    try:
        approvers = TicketApproverLevel.query.all()

        if not approvers:
            return jsonify({"error": "No approver found"}), 404  # Not Found is more appropriate
     
        return jsonify([approver.to_dict() for approver in approvers]), 200
    except Exception as e:
        import traceback
        print("=== ERROR FETCHING APPROVERS ===")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500