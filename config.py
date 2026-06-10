# config.py
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = 'mysecret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'pharma.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

load_dotenv()


EMAIL_ADDRESS = 'akshadavalkunde40@gmail.com'
EMAIL_PASSWORD = 'qggb usmr hgjr fgze'
ADMIN_EMAIL = 'admin@pharama.com'

EMAIL_USER = EMAIL_ADDRESS
EMAIL_PASS = EMAIL_PASSWORD
