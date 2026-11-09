from flask import Blueprint
backup_bp = Blueprint("backup", __name__)
from app.handlers.backup.backup_handler import systems, backup_start, backup_finish, status, runs, run_log

#TESTING API
backup_bp.route("/source-backup/test-system", methods=["GET"])(systems)
backup_bp.route("/source-backup/start", methods=["POST"])(backup_start)
backup_bp.route("/source-backup/finish/<job_id>", methods=["PUT"])(backup_finish)
backup_bp.route("/source-backup/status", methods=["GET"])(status)
backup_bp.route("/source-backup/runs", methods=["GET"])(runs)
backup_bp.route("/source-backup/runs/<run_id>/log", methods=["GET"])(run_log)

