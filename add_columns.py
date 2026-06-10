from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        # Add delivery_otp and delivery_otp_expiry columns to order table
        db.session.execute(text("ALTER TABLE \"order\" ADD COLUMN delivery_otp VARCHAR(6)"))
        db.session.execute(text("ALTER TABLE \"order\" ADD COLUMN delivery_otp_expiry DATETIME"))
        db.session.commit()
        print("Columns added successfully!")
    except Exception as e:
        print(f"Error adding columns: {e}")
        db.session.rollback()
