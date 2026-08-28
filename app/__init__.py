import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from database import db
from app.services.encryption_services import generate_and_store_master_key

def create_app():
    app = Flask(__name__)
    load_dotenv()

    app.secret_key = os.getenv("FLASK_SECRET_KEY")

    # Configure the SQLAlchemy database URI
    db_user = os.getenv('GEN_DB_USER')
    db_password = os.getenv('GEN_DB_PASSWORD')
    db_host = os.getenv('GEN_DB_HOST')
    ilog_db_host = os.getenv('ILOG_DB_HOST')
    logmi_db_host = os.getenv('LOGMI_DB_HOST')
    itoss_db_name = os.getenv('ITOSS_DB_NAME')

    mysql_user = os.getenv('MYSQL_DB_USER')
    mysql_password = os.getenv('MYSQL_DB_PASSWORD')
    mysql_host = os.getenv('MYSQL_DB_HOST')
    gts_db_name = os.getenv('GTS_DB_NAME')


    db_driver = 'ODBC+Driver+17+for+SQL+Server'
    db_uri = f"mssql+pyodbc://{db_user}:{db_password}@{db_host}/{itoss_db_name}?driver={db_driver}"

    # Configure the second (MFA) database URI
    mfa_db_name = os.getenv('MFA_DB_NAME')  # Set this in your .env
    mfa_db_uri = f"mssql+pyodbc://{db_user}:{db_password}@{db_host}/{mfa_db_name}?driver={db_driver}"

    #Configure the third (HRIS) database URI
    hris_db_name = os.getenv('HRIS_DB_NAME')  # Set this in your .env
    hris_db_uri = f"mssql+pyodbc://{db_user}:{db_password}@{db_host}/{hris_db_name}?driver={db_driver}"

    #Configure the third (ILOG) database URI
    ilog_db_name = os.getenv('ILOG_DB_NAME')  # Set this in your .env
    ilog_db_uri = f"mssql+pyodbc://{db_user}:{db_password}@{ilog_db_host}/{ilog_db_name}?driver={db_driver}"

    #Configure the third (ACCSYS) database URI
    accsys_db_name = os.getenv('ACCSYS_DB_NAME')  # Set this in your .env
    accsys_db_uri = f"mssql+pyodbc://{db_user}:{db_password}@{db_host}/{accsys_db_name}?driver={db_driver}"

    #Configure the third (LOGMI) database URI
    logmi_db_name = os.getenv('LOGMI_DB_NAME')  # Set this in your .env
    logmi_db_uri = f"mssql+pyodbc://{db_user}:{db_password}@{logmi_db_host}/{logmi_db_name}?driver={db_driver}"

    #GTS PORTAL
    gts_db_uri = (f"mysql+pymysql://{mysql_user}:{mysql_password}"
        f"@{mysql_host}/{gts_db_name}"
    )


    SYSTEM_BIND_MAP = {
        "ITOSS": None,
        "MFA": "mfa_db",
        "HRIS": "hris_db",
        "I-Log": "ilog_db",
        "LOGMI": "logmi_db", 
        "AccSys": "accsys_db",
        "GTS": "gts_db",
    }
    
    app.config["SYSTEM_BIND_MAP"] = SYSTEM_BIND_MAP
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    # Configure the second database with SQLALCHEMY_BINDS
    app.config['SQLALCHEMY_BINDS'] = {
        'mfa_db': mfa_db_uri,  # Bind this URI to the 'mfa_db' key
        'hris_db': hris_db_uri, # Bind this URI to the 'hris_db' key
        'ilog_db': ilog_db_uri,
        'logmi_db' : logmi_db_uri,
        'accsys_db' : accsys_db_uri,
        'gts_db': gts_db_uri
    }

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = False  # Enable SQL logging
    app.config['SQLALCHEMY_POOL_RECYCLE'] = 3600  # Recycle connections to avoid timeouts
    
    # This will handle all the db connections
    db.init_app(app)


    #Import and register blueprints (routes)
    from app.routes.auth import auth_bp
    from app.routes.config_route import config_bp
    from app.routes.inv_route import inv_bp
    from app.routes.ticket_route import tick_bp

    # from app.routes.user import user_bp
    CORS(app,
     resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173", "https://itoss-uat.kwephilippines.ph", "https://itossv2.kwephilippines.ph"]}},
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(config_bp, url_prefix="/api")
    app.register_blueprint(inv_bp, url_prefix="/api")
    app.register_blueprint(tick_bp, url_prefix="/api")
    # app.register_blueprint(user_bp, url_prefix="/user")

    with app.app_context():
        db.create_all()
        generate_and_store_master_key()

    return app
