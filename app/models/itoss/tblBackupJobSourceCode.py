from database import db
from datetime import datetime, timedelta
import pytz

philippines_tz = pytz.timezone('Asia/Manila')

class SystemProfile(db.Model):
    __tablename__ = 'tblBackJobSourceCode'
    SystemId = db.Column(db.Integer, primary_key=True)
    SystemName = db.Column(db.String(150), nullable=False)
    StartTime = db.Column(db.Time, nullable=True)
    EndTime = db.Column(db.Time, nullable=True)
    Status = db.Column(db.String(50), nullable=False)
    FilesCopied = db.Column(db.String, nullable=True)
    FilesSkipped = db.Column(db.BigInteger, nullable=True)
    TotalSize = db.Column(db.BigInteger, nullable=False)
    ErrorMessage = db.Column(db.Text, nullable=True)
    LogPath = db.Column(db.Text, nullable=True)
    DateCreated = db.Column(db.DateTime, default=lambda: datetime.now(philippines_tz))
    
    def __init__ (self, SystemName, StartTime, EndTime, Status, **kwargs):
        self.SystemName = SystemName
        self.StartTime = StartTime
        self.EndTime = EndTime
        self.Status = Status


    def to_dict(self):
        return {
            "SystemId": self.SystemId,
            "SystemName": self.SystemName,
            "StartTime": self.StartTime,
            "EndTime": self.EndTime,
            "Status": self.Status,
            "FilesCopied": self.FilesCopied,
            "FilesSkipped": self.FilesSkipped,
            "TotalSize": self.TotalSize,
            "ErrorMessage": self.ErrorMessage,
            "LogPath": self.LogPath,
            "DateCreated": self.DateCreated,
        }