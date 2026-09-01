from database import db

class Users_MFA(db.Model):
    __tablename__ = 'tblConsolidatedUsers'
    __bind_key__ = 'mfa_db'
    id = db.Column(db.Integer, primary_key=True)
    OASId = db.Column(db.String(50), nullable=False)
    EmployeeId = db.Column(db.String(50), nullable=True)
    EmployeeName = db.Column(db.String(90), nullable=False)
    EmailAddress = db.Column(db.String(90), nullable=True)
    Password = db.Column(db.String(255), nullable=False)
    SecretKey  = db.Column(db.String(30), nullable=True, unique=True)
    Status = db.Column(db.String(1), nullable=False)
    LoginStatus = db.Column(db.String(50), nullable=False)

    def __init__ (self, OASId, EmployeeId, EmployeeName, EmailAddress, Password, Status):
        self.OASId = OASId
        self.EmployeeId = EmployeeId
        self.EmployeeName = EmployeeName
        self.EmailAddress = EmailAddress
        self.Password = Password
        self.Status = Status

    def to_dict(self):
        return {
            "id": self.id,
            "OASId": self.OASId,
            "EmployeeId": self.EmployeeId,
            "EmployeeName": self.EmployeeName,
            "EmailAddress": self.EmailAddress,
            "Status": self.Status
        }