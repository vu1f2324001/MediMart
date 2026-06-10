from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from utils import send_email
import random
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from config import EMAIL_USER, EMAIL_PASS

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = Bcrypt().generate_password_hash(request.form['password']).decode('utf-8')
        # Check if email or phone already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already used!')
            return redirect(url_for('auth.register'))
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        user = User(email=email, phone=phone, password=password, otp=otp, otp_expiry=otp_expiry, is_verified=False)
        db.session.add(user)
        db.session.commit()
        # Send OTP to email
        try:
            msg = MIMEText(f'Your OTP for registration is: {otp}')
            msg['Subject'] = 'Pharma Registration OTP'
            msg['From'] = EMAIL_USER
            msg['To'] = email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, [email], msg.as_string())
        except Exception as e:
            print('OTP Email Error:', e)
            flash('Failed to send OTP email. Please try again.')
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('auth.register'))
        session['pending_user_id'] = user.id
        flash('OTP sent to your email. Please verify.')
        return redirect(url_for('auth.verify_otp'))
    return render_template('register.html')

@auth_bp.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_user_id' not in session:
        flash('No registration in progress.')
        return redirect(url_for('auth.register'))
    user = User.query.get(session['pending_user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.register'))
    if request.method == 'POST':
        otp_input = request.form['otp']
        if user.otp == otp_input and user.otp_expiry > datetime.utcnow():
            user.is_verified = True
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            session.pop('pending_user_id', None)
            flash('Registration complete! You can now log in.')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid or expired OTP.')
    return render_template('verify_otp.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and Bcrypt().check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Logged in successfully')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found!')
            return redirect(url_for('auth.forgot_password'))
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        user.otp = otp
        user.otp_expiry = otp_expiry
        db.session.commit()
        # Send OTP to email
        try:
            msg = MIMEText(f'Your OTP for password reset is: {otp}')
            msg['Subject'] = 'Password Reset OTP'
            msg['From'] = EMAIL_USER
            msg['To'] = email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, [email], msg.as_string())
        except Exception as e:
            print('OTP Email Error:', e)
            flash('Failed to send OTP email. Please try again.')
            return redirect(url_for('auth.forgot_password'))
        session['reset_user_id'] = user.id
        flash('OTP sent to your email. Please verify.')
        return redirect(url_for('auth.verify_reset_otp'))
    return render_template('forgot_password.html')

@auth_bp.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if 'reset_user_id' not in session:
        flash('No password reset in progress.')
        return redirect(url_for('auth.forgot_password'))
    user = User.query.get(session['reset_user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        otp_input = request.form['otp']
        if user.otp == otp_input and user.otp_expiry > datetime.utcnow():
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            flash('OTP verified! You can now reset your password.')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('Invalid or expired OTP.')
    return render_template('verify_otp.html')

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        flash('No password reset in progress.')
        return redirect(url_for('auth.forgot_password'))
    user = User.query.get(session['reset_user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        new_password = request.form['new_password']
        user.password = Bcrypt().generate_password_hash(new_password).decode('utf-8')
        user.otp = None
        user.otp_expiry = None
        db.session.commit()
        session.pop('reset_user_id', None)
        flash('Password reset successful! You can now log in.')
        return redirect(url_for('auth.login'))
    return render_template('reset_password.html')
