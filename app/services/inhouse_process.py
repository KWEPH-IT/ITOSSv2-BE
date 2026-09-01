import traceback
from datetime import datetime
from urllib.parse import quote_plus

import pytz
from flask import current_app, g
from sqlalchemy import create_engine, text

from database import db
from app.models.itoss.tblConfigSystemProfile import SystemProfile
from app.models.hris.vwAtKWE import vwAtKWE
from app.services.jwt_validator import token_required


# ============================================================
# Philippine timezone
# ============================================================

ph_tz = pytz.timezone("Asia/Manila")


@token_required
def process_access(
    system_key,
    userId,
    emailAddress,
    OASId,
    modules,
    fields_value
):
    try:

        # ====================================================
        # Current Philippine date/time
        # ====================================================

        now_ph = datetime.now(ph_tz)

        formatted_datentime = now_ph.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ====================================================
        # Current logged-in user
        # ====================================================

        current_username = g.payload["username"]

        # ====================================================
        # Get system configuration
        # ====================================================

        system = SystemProfile.query.filter(
            SystemProfile.SystemAlias == system_key
        ).first()

        if not system:
            return {
                "success": False,
                "message": (
                    f"System configuration not found "
                    f"for {system_key}."
                )
            }

        tableName = system.DBTableName
        user_col = system.DBTableIdentifier

        # ====================================================
        # Get employee information
        # ====================================================

        user = vwAtKWE.query.filter(
            vwAtKWE.EmployeeId == userId
        ).first()

        if not user:
            return {
                "success": False,
                "message": (
                    f"Employee {userId} not found."
                )
            }

        # ====================================================
        # Convert modules list to dictionary
        #
        # Example:
        #
        # modules =
        # [
        #     {"ModuleName": "ModuleA"},
        #     {"ModuleName": "ModuleB"}
        # ]
        #
        # becomes:
        #
        # {
        #     "ModuleA": 1,
        #     "ModuleB": 1
        # }
        # ====================================================

        module_data = {
            module["ModuleName"]: 1
            for module in modules
        }

        # ====================================================
        # DATABASE CONFIGURATION
        # ====================================================

        bind_map = current_app.config["SYSTEM_BIND_MAP"]

        # ----------------------------------------------------
        # MSSQL
        # ----------------------------------------------------

        if system.DBType == "MSSQL":

            bind = bind_map.get(system_key)

            engine = db.get_engine(
                current_app,
                bind=bind
            )

            def quote_column(column):
                return f"[{column}]"

        # ----------------------------------------------------
        # MySQL
        # ----------------------------------------------------

        elif system.DBType == "MySQL":

            # Encode password in case it contains
            # special characters such as:
            #
            # @ # $ % & /
            #
            mysql_password = quote_plus(
                system.DBPassword
            )

            engine = create_engine(
                f"mysql+pymysql://"
                f"{system.DBUsername}:"
                f"{mysql_password}@"
                f"{system.DBServerName}/"
                f"{system.DBName}"
            )

            def quote_column(column):
                return f"`{column}`"

        # ----------------------------------------------------
        # Unsupported database type
        # ----------------------------------------------------

        else:

            return {
                "success": False,
                "message": (
                    f"Unsupported database type: "
                    f"{system.DBType}"
                )
            }

        # ====================================================
        # CHECK IF ACCOUNT ALREADY EXISTS
        # ====================================================

        query = text(f"""
            SELECT 1
            FROM {tableName}
            WHERE {quote_column("OASId")} = :user_id
        """)

        with engine.connect() as conn:

            result = conn.execute(
                query,
                {
                    "user_id": OASId
                }
            ).fetchone()

        # ====================================================
        # UPDATE EXISTING ACCOUNT
        # ====================================================

        if result:

            # ------------------------------------------------
            # If there are no modules, nothing to update
            # ------------------------------------------------

            if not module_data:

                return {
                    "success": True,
                    "action": "update",
                    "message": (
                        f"{system_key} account already exists. "
                        f"No modules to update."
                    )
                }

            # ------------------------------------------------
            # Prepare update data
            # ------------------------------------------------

            update_data = {
                **module_data,
                "user_id": OASId
            }

            # ------------------------------------------------
            # Build SET clause
            # ------------------------------------------------

            set_clause = ", ".join(
                f"{quote_column(col)} = :{col}"
                for col in module_data.keys()
            )

            query = text(f"""
                UPDATE {tableName}
                SET {set_clause}
                WHERE {quote_column("OASId")} = :user_id
            """)

            with engine.begin() as conn:

                conn.execute(
                    query,
                    update_data
                )

            return {
                "success": True,
                "action": "update",
                "message": (
                    f"{system_key} account "
                    f"updated successfully."
                )
            }

        # ====================================================
        # INSERT NEW ACCOUNT
        # ====================================================

        insert_data = {}

        # ====================================================
        # I-LOG
        # ====================================================

        if system_key == "I-Log":

            ilog_name = user.CompleteName.title()

            if user.Company == "KWE Philippines":

                company = (
                    "KINTETSU WORLD EXPRESS "
                    "(PHILIPPINES) INC."
                )

            else:

                company = user.Company

            areadept = (
                f"{user.Area.upper()} - "
                f"{user.Department.upper()}"
            )

            userGroup = "User"

            insert_data = {

                "EmailAddress": emailAddress,

                "EmployeeId": userId,

                "FullName": ilog_name,

                "Designation": user.Designation,

                "Company": company,

                "Area": user.Area.uppper(),

                "Department": user.Department.uppper(),

                "AreaDepartment": areadept,

                "UserGroup": userGroup,

                "Status": 1,

                "CreatedBy": current_username,

                "CreatedDate": formatted_datentime,

                "OASId": OASId,

                **module_data
            }

        # ====================================================
        # LOGMI
        # ====================================================

        elif system_key == "LOGMI":

            logmi_name = user.CompleteName.title()

            if user.Company == "KWE Philippines":

                company = (
                    "Kintetsu World Express "
                    "(Philippines) Inc."
                )

            else:

                company = user.Company

            userGroup = "User"

            # -----------------------------------------------
            # Copy module_data so we can add group columns
            # -----------------------------------------------

            logmi_module_data = {
                **module_data
            }

            # -----------------------------------------------
            # LOGMI module groups
            # -----------------------------------------------

            groups = [
                "whse",
                "rep",
                "transct",
                "trans",
                "pod",
                "misc",
                "config",
            ]

            for group in groups:

                if any(
                    module["ModuleName"]
                    .lower()
                    .startswith(group)
                    for module in modules
                ):

                    logmi_module_data[group] = 1

            insert_data = {

                "EmailAddress": emailAddress,

                "FullName": logmi_name,

                "Company": company,

                "Designation": user.Designation,

                "UserGroup": userGroup,

                "Status": 1,

                "CreatedBy": current_username,

                "CreatedDate": formatted_datentime,

                "OASId": OASId,

                **logmi_module_data
            }

        # ====================================================
        # ACCSYS
        # ====================================================

        elif system_key == "AccSys":

            accsys_name = user.CompleteName

            company = user.Company

            area = user.Area.title()

            userLevel = fields_value.get(
                "UserLevel"
            )

            allowedCA = fields_value.get(
                "UserAllowedCA"
            )

            userGroup = "User"

            insert_data = {

                "EmailAddress": emailAddress,

                "FullName": accsys_name,

                "Designation": user.Designation,

                "UserLevel": userLevel,

                "Company": company,

                "Department": user.Department.upper(),

                "ImmediateSuperior": (
                    user.ImmediateSupervisor
                ),

                "DepartmentHead": (
                    user.DepartmentHead
                ),

                "Area": area.title(),

                "UserGroup": userGroup,

                "AllowedCAAmount": allowedCA,

                "Status": 1,

                "CreatedBy": current_username,

                "CreatedDate": formatted_datentime,

                "OASId": OASId,

                **module_data
            }

        # ====================================================
        # TIPISIMS
        # ====================================================

        elif system_key == "TIPISIMS":

            sims_name = user.CompleteName.title()

            if user.Company == "KWE Philippines":

                company = (
                    "Kintetsu World Express "
                    "(Philippines) Inc."
                )

            else:

                company = user.Company

            xId = fields_value.get(
                "XId"
            )

            dept = fields_value.get(
                "Department",
                user.Department
            )

            userGroup = "User"

            insert_data = {

                "EmployeeId": userId,

                "XId": xId,

                "Username": xId,

                "FullName": sims_name,

                "Designation": user.Designation,

                "Company": company,

                "Department": dept,

                "UserGroup": userGroup,

                "Active": 1,

                "CreatedBy": current_username,

                "OASId": OASId,

                **module_data
            }

        # ====================================================
        # EAS
        # ====================================================

        elif system_key == "EAS":

            eas_name = user.CompleteName.title()

            userGroup = "Administrator"

            insert_data = {

                "Email_Address": emailAddress,

                "Full_Name": eas_name,

                "Designation": user.Designation,

                "UserGroup": userGroup,

                "Active": 1,

                "CreatedBy": current_username,

                "CreatedDate": formatted_datentime,

                "OASId": OASId,
            }

        # ====================================================
        # BILLSYS
        # ====================================================

        elif system_key == "BillSys":

            billsys_name = user.CompleteName

            company = user.Company

            area = user.Area.title()

            userGroup = "User"

            stat = "Active"

            insert_data = {

                "EmailAddress": emailAddress,

                "FullName": billsys_name,

                "Designation": user.Designation,

                "Company": company,

                "Department": user.Department,

                "Area": area,

                "UserGroup": userGroup,

                "Status": stat,

                "CreatedBy": current_username,

                "CreatedDate": formatted_datentime,

                "OASId": OASId,

                **module_data
            }

        # ====================================================
        # UNKNOWN SYSTEM
        # ====================================================

        else:

            return {
                "success": False,
                "message": (
                    f"Unsupported system key: "
                    f"{system_key}"
                )
            }

        # ====================================================
        # BUILD INSERT QUERY
        # ====================================================

        columns = ", ".join(
            quote_column(column)
            for column in insert_data.keys()
        )

        values = ", ".join(
            f":{column}"
            for column in insert_data.keys()
        )

        query = text(f"""
            INSERT INTO {tableName}
            ({columns})
            VALUES ({values})
        """)

        # ====================================================
        # EXECUTE INSERT
        # ====================================================

        with engine.begin() as conn:

            conn.execute(
                query,
                insert_data
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        return {
            "success": True,
            "action": "insert",
            "message": (
                f"{system_key} account "
                f"inserted successfully."
            )
        }

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as ex:

        print(
            "=== ERROR PROCESSING ACCESS ==="
        )

        traceback.print_exc()

        return {
            "success": False,
            "message": str(ex),
            "traceback": traceback.format_exc()
        }