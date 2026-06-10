import os
from app import db, User
from dotenv import load_dotenv

load_dotenv()

def delete_admin_user():
    admin_email = "admin@pharma.com"
    admin_user = User.query.filter_by(email=admin_email).first()
    if admin_user:
        db.session.delete(admin_user)
        db.session.commit()
        print(f"Deleted admin user with email: {admin_email}")
    else:
        print(f"No admin user found with email: {admin_email}")

if __name__ == "__main__":
    from app import app
    with app.app_context():
        delete_admin_user()
