from app import app, db, User
from dotenv import load_dotenv

load_dotenv()

with app.app_context():
    admin_user = User.query.filter_by(email='admin@pharma.com').first()
    print('Admin user exists:', admin_user is not None)
    if admin_user:
        print('Admin details:', admin_user.email, admin_user.is_admin)
    else:
        print('No admin user found. Creating one...')
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(app)
        admin = User(
            email='admin@pharma.com',
            phone='admin123',
            password=bcrypt.generate_password_hash('admin123').decode('utf-8'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
