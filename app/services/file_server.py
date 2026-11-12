import os
from flask import send_from_directory

# UPLOAD_FOLDER = os.path.join(
#     os.getcwd(),
#     "app",
#     "uploads"
# )

UPLOAD_FOLDER = os.getenv(
    "UPLOAD_FOLDER",
    "/data/uploads"
)

def uploaded_file(filename):
    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )