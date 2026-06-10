from app import app, db, User
from dotenv import load_dotenv

load_dotenv()

with app.app_context():
    doctor_user = User.query.filter_by(email='doctor@pharma.com').first()
    print('Doctor user exists:', doctor_user is not None)
    if doctor_user:
        print('Doctor details:', doctor_user.email, doctor_user.is_doctor)
    else:
        print('No doctor user found. Creating one...')
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(app)
        doctor = User(
            email='doctor@pharma.com',
            phone='9876543210',
            password=bcrypt.generate_password_hash('doctor123').decode('utf-8'),
            is_doctor=True,
            is_verified=True
        )
        db.session.add(doctor)
        db.session.commit()
        print('Doctor user created successfully!')
