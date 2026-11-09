from database import db
from datetime import datetime, timedelta
import pytz
from datetime import datetime


philippines_tz = pytz.timezone('Asia/Manila')


class BackupSystemFolder(db.Model):
    __tablename__ = 'tblBackupSystemFolder'
    SystemId = db.Column(db.Integer, primary_key=True)
    SystemNo = db.Column(
        db.Integer,
        db.ForeignKey('tblConfigSystemProfile.SystemId'),
        nullable=True
    )
    FolderPath = db.Column(db.String(300), nullable=True)
    FileBackupAction = db.Column(db.String(10), nullable=True)
    SourceCodeBackupAction = db.Column(db.String(10), nullable=True)
   
    def __init__ (self, SystemNo, FolderPath, FileBackupAction, SourceCodeBackupAction):
        self.SystemNo = SystemNo
        self.FolderPath = FolderPath
        self.FileBackupAction = FileBackupAction
        self.SourceCodeBackupAction = SourceCodeBackupAction


    def to_dict(self):
        return {
            "SystemId": self.SystemId,
            "SystemNo": self.SystemNo,
            "FolderPath": self.FolderPath,
            "FileBackupAction": self.FileBackupAction,
            "SourceCodeBackupAction": self.SourceCodeBackupAction
        }
    
    