from database import db

class MFA_Sessions(db.Model):
    __tablename__ = 'tblSessions'
    __bind_key__ = 'mfa_db'
    id = db.Column(db.Integer, primary_key=True)
    OASId = db.Column(db.String(50), nullable=False)
    SessionToken = db.Column(db.String(200), nullable=False)
    ExpirationTime = db.Column(db.String(100), nullable=False)
    SystemName = db.Column(db.String(50), nullable=False)

    def __init__ (self, OASId, SessionToken, ExpirationTime, SystemName):
        self.OASId = OASId
        self.SessionToken = SessionToken
        self.ExpirationTime = ExpirationTime
        self.SystemName = SystemName

    def to_dict(self):
        return {
            "id": self.id,
            "OASId": self.OASId,
            "SessionToken": self.SessionToken,
            "ExpirationTime": self.ExpirationTime,
            "SystemName": self.SystemName
        }