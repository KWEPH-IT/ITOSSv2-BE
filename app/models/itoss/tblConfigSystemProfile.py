from database import db
from datetime import datetime, timedelta
import pytz

philippines_tz = pytz.timezone('Asia/Manila')

class SystemProfile(db.Model):
    __tablename__ = 'tblConfigSystemProfile'
    SystemId = db.Column(db.Integer, primary_key=True)
    SystemName = db.Column(db.String(150), nullable=False)
    SystemAlias = db.Column(db.String(60), nullable=False)
    SourceCodeServer = db.Column(db.String(50), nullable=False)
    DBServerName = db.Column(db.String(60), nullable=False)
    DBName = db.Column(db.String(60), nullable=False)
    DBUsername = db.Column(db.String(30), nullable=False)
    DBPassword = db.Column(db.String(30), nullable=False)
    DBType = db.Column(db.String(10), nullable=False)
    DBTableName = db.Column(db.String(50), nullable=True)
    DBTableIdentifier = db.Column(db.String(50), nullable=True)
    DBPasswordColName = db.Column(db.String(20), nullable=True)
    DBStatusColName = db.Column(db.String(20), nullable=True)
    FieldsToRemove = db.Column(db.String(1000), nullable=True)

    SourceCodePath = db.Column(db.String(200), nullable=True)
    BackupPath = db.Column(db.String(200), nullable=True)
    ScheduleType = db.Column(db.String(15), nullable=True)
    ScheduleTime = db.Column(db.Time, nullable=True)
    BackupDay = db.Column(db.Integer, nullable=True)

    Remarks = db.Column(db.String(300), nullable=True)
    Status = db.Column(db.String(1), nullable=False)
    CreatedBy = db.Column(db.String(80), nullable=False)
    DateCreated = db.Column(db.DateTime, default=lambda: datetime.now(philippines_tz))
    ModifiedBy = db.Column(db.String(80), nullable=True)
    DateModified = db.Column(db.String(50), nullable=True)

    def __init__ (self, SystemName, SystemAlias, SourceCodeServer, DBServerName, DBName, DBUsername, DBPassword, DBType, CreatedBy, Status, **kwargs):
        self.SystemName = SystemName
        self.SystemAlias = SystemAlias
        self.SourceCodeServer = SourceCodeServer
        self.DBServerName = DBServerName
        self.DBName = DBName
        self.DBUsername = DBUsername
        self.DBPassword = DBPassword
        self.DBType = DBType
        self.CreatedBy = CreatedBy
        self.Status = Status

        for key, value in kwargs.items():
            setattr(self, key, value)


    def to_dict(self):
        return {
            "SystemId": self.SystemId,
            "SystemName": self.SystemName,
            "SystemAlias": self.SystemAlias,
            "SourceCodeServer": self.SourceCodeServer,
            "DBServerName": self.DBServerName,
            "DBName": self.DBName,
            "DBUsername": self.DBUsername,
            "DBPassword": self.DBPassword,
            "DBTableName": self.DBTableName,
            "DBType": self.DBType,
            "DBTableIdentifier": self.DBTableIdentifier,
            "DBPasswordColName": self.DBPasswordColName,
            "DBStatusColName": self.DBStatusColName,
            "FieldsToRemove": self.FieldsToRemove,
            
            "SourceCodePath": self.SourceCodePath,
            "BackupPath": self.BackupPath,
            "ScheduleType": self.ScheduleType,
            "ScheduleTime": self.ScheduleTime.isoformat() if self.ScheduleTime else None,
            "BackupDay": self.BackupDay,

            "Remarks": self.Remarks,
            "Status": self.Status,
            "CreatedBy": self.CreatedBy,
            "DateCreated": self.DateCreated,
            "ModifiedBy": self.ModifiedBy,
            "DateModified": self.DateModified
        }
