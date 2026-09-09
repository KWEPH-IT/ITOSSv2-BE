from database import db
from app.models.itoss.tblTransApprovalLevel import TicketApproval
from app.models.itoss.tblConfigTicketCategApprover import TicketApproverLevel
from app.models.itoss.tblTransTickets import Tickets
from app.models.itoss.tblTransTicketMessage import TicketMessage
from app.models.hris.vwAtKWE import vwAtKWE
from flask import jsonify, request, g
from app.services.jwt_validator import token_required
from app.services.email_sending import send_email
from datetime import datetime
import pytz
# Philippine timezone
ph_tz = pytz.timezone("Asia/Manila")

# Current PH time
now_ph = datetime.now(ph_tz)

# Format to YYYY-MM-DD
formatted_date = now_ph.strftime("%Y-%m-%d")

@token_required
def approval_history():
    approvals = TicketApproval.query.all()
    if not approvals:
            return jsonify({"error": "No approvals found"}), 404  # Not Found is more appropriate

    return jsonify([approval.to_dict() for approval in approvals]), 200

@token_required
def approveTicket():
    try:
        data = request.get_json()

        ticketno = data.get("TicketNumber")
        requestType = data.get("RequestType")
        requestName = data.get("RequestName")
        requestorName = data.get("RequestorName")

        current_user = g.payload["emp_id"]
        current_username = g.payload["username"]

        approve = Tickets.query.filter(Tickets.TicketNumber == ticketno).first()
        if not approve: 
            return jsonify({"message": "No ticket number found!"}), 404
        
        nextLevel = approve.CurrentLevel + 1

        config = TicketApproverLevel.query.filter(
            TicketApproverLevel.CategoryId == requestType,
            TicketApproverLevel.LevelNo == nextLevel
        ).all()

        if not config:
            return jsonify({"message": "Approver level configuration not found!"}), 404
        

        for conf in config:
            if conf.ApproverType == "Dynamic Superior": 
                if current_user == approve.ISId: 
                    next_status = conf.Description
                    next_level = conf.LevelNo
                    break
            elif conf.ApproverType == "Dynamic Manager": 
                if current_user == approve.DHId: 
                    next_status = conf.Description
                    next_level = conf.LevelNo
                    break
            elif conf.ApproverType == "Specific User": 
                if current_user == conf.ApproverValue: 
                    next_status = conf.Description
                    next_level = conf.LevelNo
                    break
        
        status = next_status
        approve.CurrentLevel = next_level
        approve.Status = status

        #------------------SPECIAL CASE--------------------------
        #----------------------UAS-------------------------------
        if requestType == 17 and status == "Approved By IT Manager":
           approve.AssignedTo = 'K656' 
        
        #------------------APPROVAL HISTORY----------------------
        new_history = TicketApproval(
            TicketNumber = ticketno,
            ApprovalLevel= nextLevel,
            ApproverId = current_user,
            Action = next_status,
            Remarks = next_status
        )

        db.session.add(new_history)

        #------------------MESSAGE-------------------------------
        remarks = f"Approved {ticketno}"
        new_message = TicketMessage(
            TicketNumber=ticketno,
            EmployeeId=current_user,
            SenderName=current_username,
            Status=next_status,
            Message=remarks
        )

        db.session.add(new_message)
        db.session.commit()

        #----------------------EMAIL SENDING---------------------------------------------
        receiver = None
        nextLevelApprover = approve.CurrentLevel + 1

        configNext = TicketApproverLevel.query.filter(
            TicketApproverLevel.CategoryId == requestType,
            TicketApproverLevel.LevelNo == nextLevelApprover
        ).first()
        if configNext:

            if configNext.ApproverType == "Dynamic Superior":
                next_approver = approve.ISId
                get_ISEmail = vwAtKWE.query.filter_by(EmployeeId = next_approver).first()
                if get_ISEmail:
                    receiver = get_ISEmail.EmailAddress

            elif configNext.ApproverType == "Dynamic Manager":
                next_approver = approve.DHId
                get_DHEmail = vwAtKWE.query.filter_by(EmployeeId = next_approver).first()
                if get_DHEmail:
                    receiver = get_DHEmail.EmailAddress

            elif configNext.ApproverType == "Specific User":
                next_approver = configNext.ApproverValue
                get_Email = vwAtKWE.query.filter_by(EmployeeId = next_approver).first()
                if get_Email:
                    receiver = get_Email.EmailAddress

            real_receiver = receiver
            if receiver:
                # receiver = "reginamaye.banadera@kwe.com"
                receiver = real_receiver
                subject = f"For Approval: ITOSS Request [{formatted_date}]"
                html = f"""
                    <html>
                    <body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Arial, sans-serif;">

                        <table width="100%" cellpadding="0" cellspacing="0" style="padding:30px 0;">
                        <tr>
                            <td align="center">

                            <table width="600" cellpadding="0" cellspacing="0"
                                style="background:#ffffff; border-radius:10px; overflow:hidden;">

                                <!-- Header -->
                                <tr>
                                <td style="background:#1677ff; padding:20px;">
                                    <h2 style="margin:0; color:#ffffff; font-size:18px;">
                                    IT Support Notification
                                    </h2>
                                </td>
                                </tr>

                                <!-- Content -->
                                <tr>
                                <td style="padding:25px; color:#333333; font-size:14px; line-height:1.6;">

                                    <p>Hello,</p>

                                    <p>
                                    This is an automated reminder for a pending request in the
                                    Information Technology Online Support System.
                                    </p>

                                    <!-- Request Details -->
                                    <table width="100%" cellpadding="0" cellspacing="0"
                                        style="margin:20px 0; border:1px solid #f0f0f0; border-radius:8px;">

                                        <tr>
                                            <td colspan="2"
                                                style="background:#fafafa; padding:12px 15px; font-weight:bold; font-size:14px;">
                                                Request Details
                                            </td>
                                        </tr>

                                        <tr>
                                            <td style="padding:12px 15px; width:35%; color:#666;">
                                                Ticket No.
                                            </td>
                                            <td style="padding:12px 15px; font-weight:600;">
                                                {ticketno}
                                            </td>
                                        </tr>

                                        <tr style="background:#fcfcfc;">
                                            <td style="padding:12px 15px; color:#666;">
                                                Request Type
                                            </td>
                                            <td style="padding:12px 15px;">
                                                {requestName}
                                            </td>

                                        </tr>
                                            <td style="padding:12px 15px; color:#666;">
                                                Requestor
                                            </td>
                                            <td style="padding:12px 15px;">
                                                {requestorName}
                                            </td>
                                        <tr>

                                        </tr>

                                        <tr style="background:#fcfcfc;">
                                            <td style="padding:12px 15px; color:#666;">
                                                Status
                                            </td>
                                            <td style="padding:12px 15px;">
                                                <span style="
                                                    background:#fff7e6;
                                                    color:#d48806;
                                                    padding:4px 10px;
                                                    border-radius:20px;
                                                    font-size:12px;
                                                    font-weight:bold;
                                                ">
                                                    {status}
                                                </span>
                                            </td>
                                        </tr>

                                    </table>

                                    <!-- Highlight -->
                                    <div style="
                                        background:#f5f8ff;
                                        border-left:4px solid #1677ff;
                                        padding:12px;
                                        margin:20px 0;
                                    ">
                                        Please log in to the system to review the request details.
                                    </div>

                                    <p>
                                    This is a system-generated email. Please do not reply directly
                                    to this message.
                                    </p>

                                    <br/>

                                    <p>
                                    Regards,<br/>
                                    <b>IT Support Team</b>
                                    </p>

                                </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                <td style="
                                    background:#f0f2f5;
                                    padding:15px;
                                    text-align:center;
                                    font-size:12px;
                                    color:#888;
                                ">
                                    © 2026 Information Technology Online Support System
                                </td>
                                </tr>

                            </table>

                            </td>
                        </tr>
                        </table>

                    </body>
                    </html>
                    """

                send_email(receiver, subject, html)

        else:
            receiver = "itsupport.kweph@kwe.com"
            subject = f"For Processing: ITOSS Request [{formatted_date}]"
            html = f"""
                <html>
                <body style="margin:0; padding:0; background-color:#f4f6f9; font-family:Arial, sans-serif;">

                    <table width="100%" cellpadding="0" cellspacing="0" style="padding:30px 0;">
                    <tr>
                        <td align="center">
                        <table width="600" cellpadding="0" cellspacing="0"
                            style="background:#ffffff; border-radius:10px; overflow:hidden;">

                            <!-- Header -->
                            <tr>
                            <td style="background:#1677ff; padding:20px;">
                                <h2 style="margin:0; color:#ffffff; font-size:18px;">
                                IT Support Notification
                                </h2>
                            </td>
                            </tr>

                            <!-- Content -->
                            <tr>
                            <td style="padding:25px; color:#333333; font-size:14px; line-height:1.6;">

                                <p>Hello IT Support Team,</p>

                                <p>
                                This is an automated reminder for a pending request in the
                                Information Technology Online Support System.
                                </p>

                                <!-- Request Details -->
                                <table width="100%" cellpadding="0" cellspacing="0"
                                    style="margin:20px 0; border:1px solid #f0f0f0; border-radius:8px;">

                                    <tr>
                                        <td colspan="2"
                                            style="background:#fafafa; padding:12px 15px; font-weight:bold; font-size:14px;">
                                            Request Details
                                        </td>
                                    </tr>

                                    <tr>
                                        <td style="padding:12px 15px; width:35%; color:#666;">
                                            Ticket No.
                                        </td>
                                        <td style="padding:12px 15px; font-weight:600;">
                                            {ticketno}
                                        </td>
                                    </tr>

                                    <tr style="background:#fcfcfc;">
                                        <td style="padding:12px 15px; color:#666;">
                                            Request Type
                                        </td>
                                        <td style="padding:12px 15px;">
                                            {requestName}
                                        </td>

                                    </tr>
                                        <td style="padding:12px 15px; color:#666;">
                                            Requestor
                                        </td>
                                        <td style="padding:12px 15px;">
                                            {requestorName}
                                        </td>
                                    <tr>

                                    </tr>

                                    <tr style="background:#fcfcfc;">
                                        <td style="padding:12px 15px; color:#666;">
                                            Status
                                        </td>
                                        <td style="padding:12px 15px;">
                                            <span style="
                                                background:#fff7e6;
                                                color:#d48806;
                                                padding:4px 10px;
                                                border-radius:20px;
                                                font-size:12px;
                                                font-weight:bold;
                                            ">
                                                {status}
                                            </span>
                                        </td>
                                    </tr>

                                </table>

                                <!-- Highlight -->
                                <div style="
                                    background:#f5f8ff;
                                    border-left:4px solid #1677ff;
                                    padding:12px;
                                    margin:20px 0;
                                ">
                                    Please log in to the system to review the request details.
                                </div>

                                <p>
                                This is a system-generated email. Please do not reply directly
                                to this message.
                                </p>

                                <br/>

                                <p>
                                Regards,<br/>
                                <b>IT Support Team</b>
                                </p>

                            </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                            <td style="
                                background:#f0f2f5;
                                padding:15px;
                                text-align:center;
                                font-size:12px;
                                color:#888;
                            ">
                                © 2026 Information Technology Online Support System
                            </td>
                            </tr>

                        </table>

                        </td>
                    </tr>
                    </table>

                </body>
                </html>
                """

            send_email(receiver, subject, html)
        return jsonify({"message": "Request successfully approved!"}), 200
    
    except Exception as e:
        db.session.rollback()
        import traceback
        print("=== ERROR APPROVING TICKET ===")
        traceback.print_exc()
        return jsonify({
            "error": str(e)
        }), 500
    
@token_required
def declineTicket():
    try:
        data = request.get_json()

        ticketno = data.get("TicketNumber")
        reason = data.get("reason")

        current_user = g.payload["emp_id"]
        current_username = g.payload["username"]


        approve = Tickets.query.filter(Tickets.TicketNumber == ticketno).first()
        if not approve: 
            return jsonify({"message": "No ticket number found!"}), 404

        Status = "Declined"

        approve.CurrentLevel =  0
        approve.Status = Status

        #------------------APPROVAL HISTORY----------------------
        new_history = TicketApproval(
            TicketNumber = ticketno,
            ApprovalLevel= 0,
            ApproverId = current_user,
            Action = Status,
            Remarks = reason
        )

        db.session.add(new_history)

        #------------------MESSAGE-------------------------------
        remarks = f"Declined {ticketno}: {reason}"
        new_message = TicketMessage(
            TicketNumber=ticketno,
            EmployeeId=current_user,
            SenderName=current_username,
            Status=Status,
            Message=remarks
        )

        db.session.add(new_message)
        db.session.commit()

        return jsonify({"message": "Request successfully declined!"}), 200
    
    except Exception as e:
        db.session.rollback()
        import traceback
        print("=== ERROR DECLINING TICKET ===")
        traceback.print_exc()
        return jsonify({
            "error": str(e)
        }), 500