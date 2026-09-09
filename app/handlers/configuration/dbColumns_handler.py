from database import db
from app.models.itoss.tblConfigDBColumns import DBColumns
from app.models.itoss.tblConfigSystemProfile import SystemProfile
from sqlalchemy import create_engine, Table, Column, String, MetaData
import pyodbc
from flask import jsonify, request, g
from app.services.jwt_validator import token_required
from datetime import datetime
import pytz
import mysql.connector


# Philippine timezone
ph_tz = pytz.timezone("Asia/Manila")

# Current PH time
now_ph = datetime.now(ph_tz)

@token_required
def fetchAllDBColumns(sa):
    columns = DBColumns.query.filter(DBColumns.SystemAlias == sa).order_by(DBColumns.DBColumn.asc()).all()
    return jsonify([column.to_dict() for column in columns])

@token_required
def UpdateDBColumn(id):
    try:
        data = request.get_json()

        column = DBColumns.query.get(id)
        if not column:
            return jsonify({"message": "Database column not found"}), 404

        updating_fields = [
            "Description", "ColGroup", "Status"
        ]

        for field in updating_fields:
            if field in data:
                setattr(column, field, data[field])

        column.ModifiedBy = g.payload['username']
        column.DateModified = datetime.now(ph_tz).strftime("%Y-%m-%d %H:%M:%S") 
        db.session.commit()

        return jsonify({"message": "Column details has been successfully updated!"}), 200
    
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()  # see full error in logs
        return jsonify({
            "message": "Error updating column profile",
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500
    

@token_required
def get_columns(system):
    if system.DBType == "MSSQL":
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={system.DBServerName};"
            f"DATABASE={system.DBName};"
            f"UID={system.DBUsername};"
            f"PWD={system.DBPassword}"
        )
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{system.DBTableName}'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return columns

    elif system.DBType == "MySQL":
        conn = mysql.connector.connect(
            host=system.DBServerName,
            database=system.DBName,
            user=system.DBUsername,
            password=system.DBPassword
        )
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{system.DBTableName}'
              AND TABLE_SCHEMA = '{system.DBName}'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return columns

    else:
        raise Exception("Unsupported DB Type")

@token_required
def refetchDBColumns(sa, current_user=None):
    try:
        current_user = g.payload['username']
        system = SystemProfile.query.filter_by(SystemAlias=sa).first()

        if not system:
            return jsonify({"error": "Invalid System Alias"}), 404

        # Get columns from DB (MSSQL or MySQL)
        db_columns = get_columns(system)

        # Convert comma string to list
        fields_to_remove = (
            system.FieldsToRemove.split(",") if system.FieldsToRemove else []
        )
        fields_to_remove = [x.strip().lower() for x in fields_to_remove]

        # Remove unwanted fields
        filtered_columns = [
            col for col in db_columns 
            if col.lower() not in fields_to_remove
        ]

        # Fetch existing columns for this alias
        existing_cols = {
            x.DBColumn.lower()
            for x in DBColumns.query.filter_by(SystemAlias=sa).all()
        }

        inserted_count = 0

        # Insert new columns (skip duplicates)
        for col in filtered_columns:
            if col.lower() in existing_cols:
                continue  # skip existing column

            new_entry = DBColumns(
                SystemAlias=sa,
                DBColumn=col,
                ImportedBy=current_user,
                Status=0
            )
            db.session.add(new_entry)
            inserted_count += 1

        db.session.commit()

        return jsonify({
            "message": "Refetch completed",
            "inserted": inserted_count,
            "skipped": len(filtered_columns) - inserted_count,
            "total_columns": len(filtered_columns)
        }), 200

    except Exception as e:
        db.session.rollback()
        print("Error in refetchDBColumns:", str(e))
        return jsonify({"error": str(e)}), 500