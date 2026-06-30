from app import app
from models import db, Prescription

with app.app_context():
    total = Prescription.query.count()
    print(f"Total prescriptions: {total}") 
