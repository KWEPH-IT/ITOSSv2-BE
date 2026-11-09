import os
from datetime import datetime, timedelta, time
from pathlib import Path
from flask import jsonify, request, abort
from database import db
from app.models.itoss.tblBackupJobSourceCode import SourceCodeBackup, now_ph
from app.models.itoss.tblConfigSystemProfile import SystemProfile
from app.services.jwt_validator import token_required
from app.services.machine_token_validator import service_token_required



WARN_DAYS = int(os.getenv("WARN_DAYS", 32))
FAIL_DAYS = int(os.getenv("FAIL_DAYS", 40))
STALE_RUNNING_HOURS = int(os.getenv("STALE_RUNNING_HOURS", 6))


@service_token_required
def systems():
    rows = SystemProfile.query.filter_by(Status=1).order_by(SystemProfile.SystemName).all()
    return jsonify([r.to_dict() for r in rows])

@service_token_required
def backup_start():
    data = request.json

    SystemName = data.get("SystemName")

    new_job = SourceCodeBackup(SystemName=SystemName, StartTime=now_ph().time(), EndTime=None, Status="Running", TotalSize=0)
    db.session.add(new_job) 
    db.session.commit()
    return jsonify(id=new_job.SystemId), 201


@service_token_required
def backup_finish(job_id):
    job = db.get_or_404(SourceCodeBackup, job_id)
    if job.Status != "Running":
        return jsonify(error="This run was already finished"), 409
 
    data = request.get_json(silent=True) or {}
    job.EndTime = now_ph().time()
    job.Status = data.get("Status", "Failed")
    job.FilesCopied = str(data.get("FilesCopied", 0))
    job.FilesSkipped = data.get("FilesSkipped", 0)
    job.TotalSize = int(data.get("TotalSize", 0))
    job.ErrorMessage = data.get("ErrorMessage") or None
    job.LogText = data.get("LogText")
    db.session.commit()
    return jsonify(ok=True)



@service_token_required
def status():
    out = []
    active_systems = SystemProfile.query.filter_by(SystemAlias='LogMI', Status=1).order_by(SystemProfile.SystemName).first()
 
    for s in active_systems:
        last = SourceCodeBackup.query.filter_by(SystemName=s.SystemName).order_by(SourceCodeBackup.DateCreated.desc()).first()
        info = {"name": s.SystemName, "sourcePath": s.SourcePath, "backupPath": s.BackupPath,
                "lastRun": last.to_dict() if last else None, "ageDays": None}
 
        if not last:
            info.update(status="failed", message="No backup has been reported yet")
        elif last.Status == "Running":
            hours = (now_ph() - last.DateCreated).total_seconds() / 3600
            if hours > STALE_RUNNING_HOURS:
                info.update(status="failed", message="Backup appears stuck (still Running after several hours)")
            else:
                info.update(status="warning", message="Backup is currently running")
        else:
            age = (now_ph() - last.DateCreated).total_seconds() / 86400
            info["ageDays"] = round(age, 1)
            if last.Status != "Success":
                info.update(status="failed", message="Last backup failed")
            elif age > FAIL_DAYS:
                info.update(status="failed", message=f"No backup in over {FAIL_DAYS} days")
            elif age > WARN_DAYS:
                info.update(status="warning", message="Backup is overdue")
            else:
                info.update(status="ok", message="Up to date")
        out.append(info)
 
    return jsonify({"checkedAt": now_ph().isoformat(timespec="seconds"), "systems": out})


# Run history + log
# ---------------------------------------------------------------

@token_required
def runs():
    q = SourceCodeBackup.query
    a = request.args
    if a.get("system"):
        q = q.filter(SourceCodeBackup.SystemName == a["system"])
    if a.get("status"):
        q = q.filter(SourceCodeBackup.Status == a["status"])
    if a.get("days"):
        q = q.filter(SourceCodeBackup.DateCreated >= now_ph() - timedelta(days=int(a["days"])))
    rows = q.order_by(SourceCodeBackup.DateCreated.desc()).limit(min(int(a.get("limit", 100)), 500)).all()
    return jsonify([r.to_dict() for r in rows])
 
 

@token_required
def run_log(run_id):
    run = db.get_or_404(SourceCodeBackup, run_id)
    if not run.LogText:
        abort(404, "No log stored for this run")
    return jsonify(log=run.LogText)