# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_doctor = db.Column(db.Boolean, default=False)
    otp = db.Column(db.String(6), nullable=True)
    otp_expiry = db.Column(db.DateTime, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_name = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    age_group = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Integer, default=0)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow)
    address = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.String(200), nullable=True)
    total = db.Column(db.Float, nullable=True)
    delivery_otp = db.Column(db.String(6), nullable=True)
    delivery_otp_expiry = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='orders')
    medicine = db.relationship('Medicine', backref='orders')

class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    discount = db.Column(db.Integer, nullable=False)
    valid_until = db.Column(db.DateTime, nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    med_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref='carts')
    medicine = db.relationship('Medicine', backref='cart_items')

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_path = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected, Awaiting OTP Verification, Delivered
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    disease = db.Column(db.String(200), nullable=True)
    symptoms = db.Column(db.Text, nullable=True)
    prescription_details = db.Column(db.Text, nullable=True)
    address = db.Column(db.Text, nullable=True)
    doctor_notes = db.Column(db.Text, nullable=True)
    medicine = db.Column(db.String(200), nullable=True)
    dosage = db.Column(db.String(100), nullable=True)
    delivery_otp = db.Column(db.String(6), nullable=True)
    delivery_otp_expiry = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', foreign_keys=[user_id], backref='prescriptions')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='reviewed_prescriptions')
    admin = db.relationship('User', foreign_keys=[admin_id], backref='approved_prescriptions')
