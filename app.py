from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_migrate import Migrate
from config import Config
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import random, smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, ADMIN_EMAIL
from models import db, User, Medicine, Order, Offer


def send_order_email(user_email, order_details):
    msg = EmailMessage()
    msg['Subject'] = '📦 New Order Placed'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ADMIN_EMAIL
    msg.set_content(f'''
Hello Admin,

A new order has been placed!

👤 Customer: {user_email}
🛍️ Order Summary:
{order_details}

Please check the admin dashboard for full details.

Thanks,
Your Website Bot 🤖
''')

    # Send email via Gmail SMTP
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

app = Flask(__name__)
app.config.from_object(Config)
# In development, disable caching of static files so updates appear immediately
if app.debug or app.config.get('ENV') == 'development':
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Email config
EMAIL_USER = app.config.get('EMAIL_USER', 'akshadavalkunde40@gmail.com')
EMAIL_PASS = app.config.get('EMAIL_PASS', 'qggb usmr hgjr fgze')

db.init_app(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Jinja filter to append file mtime as cache-busting query param for local static files
def version_filter(path):
    try:
        if not path:
            return ''
        rel = path.lstrip('/') if path.startswith('/') else path
        full_path = os.path.join(os.getcwd(), rel)
        mtime = int(os.path.getmtime(full_path))
        return f"{path}?v={mtime}"
    except Exception:
        return path

app.jinja_env.filters['version'] = version_filter

# Register blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.doctor import doctor_bp

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(doctor_bp)

# ------------------ Login Manager ------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



def send_email(to_email, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [to_email], msg.as_string())
    except Exception as e:
        print('Email Error:', e)

# ------------------ Routes ------------------
@app.route('/')
def home():
    search_query = request.args.get('search', '')
    if search_query:
        medicines = Medicine.query.filter(Medicine.name.ilike(f'%{search_query}%')).all()
    else:
        medicines = Medicine.query.all()
    offers = Offer.query.all()
    return render_template('home.html', medicines=medicines, offers=offers)

@app.route('/place_order', methods=['POST'])
@login_required
def place_order():
    # 1. Save order to DB
    order = Order(user_id=current_user.id, status='Pending')
    db.session.add(order)
    db.session.commit()

    # 2. Send email to admin
    order_details = f'Order ID: {order.id}, Items: {len(cart_items)}'
    send_order_email(current_user.email, order_details)

    flash('Your order has been placed!', 'success')
    return redirect(url_for('my_orders'))

@app.route('/category/<category>')
def category_filter(category):
    medicines = Medicine.query.filter(Medicine.category.ilike(f"%{category}%")).all()
    offers = Offer.query.all()
    return render_template('home.html', medicines=medicines, offers=offers)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        phone = request.form['phone']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        # Check if email or phone already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered!')
            return redirect(url_for('register'))
        if User.query.filter_by(phone=phone).first():
            flash('Phone number already used!')
            return redirect(url_for('register'))
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
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, [email], msg.as_string())
        except Exception as e:
            print('OTP Email Error:', e)
            flash('Failed to send OTP email. Please try again.')
            db.session.delete(user)
            db.session.commit()
            return redirect(url_for('register'))
        session['pending_user_id'] = user.id
        flash('OTP sent to your email. Please verify.')
        return redirect(url_for('verify_otp'))
    return render_template('register.html')

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if 'pending_user_id' not in session:
        flash('No registration in progress.')
        return redirect(url_for('register'))
    user = User.query.get(session['pending_user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('register'))
    if request.method == 'POST':
        otp_input = request.form['otp']
        if user.otp == otp_input and user.otp_expiry > datetime.utcnow():
            user.is_verified = True
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            session.pop('pending_user_id', None)
            flash('Registration complete! You can now log in.')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP.')
    return render_template('verify_otp.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Logged in successfully')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out!')
    return redirect(url_for('login'))



@app.route('/add_to_cart/<int:med_id>', methods=['POST'])
@login_required
def add_to_cart(med_id):
    quantity = int(request.form['quantity'])
    cart = session.get('cart', {})
    cart[str(med_id)] = cart.get(str(med_id), 0) + quantity
    session['cart'] = cart
    flash('Item added to cart!')
    return redirect(url_for('home'))

@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for med_id, qty in cart.items():
        med = Medicine.query.get(int(med_id))
        if med:
            discounted_price = med.price * (1 - med.discount / 100)
            subtotal = discounted_price * qty
            items.append({'medicine': med, 'quantity': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', items=items, total=total)

@app.route('/clear_cart')
@login_required
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared!')
    return redirect(url_for('cart'))




@app.route('/myorders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    return render_template('my_orders.html', orders=orders)

@app.route('/order', methods=['GET'])
@login_required
def order_page():
    medicines = Medicine.query.all()
    return render_template('order.html', medicines=medicines)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found!')
            return redirect(url_for('forgot_password'))
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.utcnow() + timedelta(minutes=10)
        user.otp = otp
        user.otp_expiry = otp_expiry
        db.session.commit()
        # Send OTP to email
        try:
            msg = MIMEText(f'Your OTP for password reset is: {otp}')
            msg['Subject'] = 'Pharma Password Reset OTP'
            msg['From'] = EMAIL_USER
            msg['To'] = email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.sendmail(EMAIL_USER, [email], msg.as_string())
        except Exception as e:
            print('OTP Email Error:', e)
            flash('Failed to send OTP email. Please try again.')
            return redirect(url_for('forgot_password'))
        session['reset_user_id'] = user.id
        flash('OTP sent to your email. Please verify.')
        return redirect(url_for('reset_password_otp'))
    return render_template('forgot_password.html')

@app.route('/reset_password_otp', methods=['GET', 'POST'])
def reset_password_otp():
    if 'reset_user_id' not in session:
        flash('No password reset in progress.')
        return redirect(url_for('forgot_password'))
    user = User.query.get(session['reset_user_id'])
    if not user:
        flash('User not found.')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        otp_input = request.form['otp']
        new_password = request.form['new_password']
        if user.otp == otp_input and user.otp_expiry > datetime.utcnow():
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.otp = None
            user.otp_expiry = None
            db.session.commit()
            session.pop('reset_user_id', None)
            flash('Password reset successful! You can now log in.')
            return redirect(url_for('login'))
        else:
            flash('Invalid or expired OTP.')
    return render_template('reset_password_otp.html')

@app.route('/create-admin')
def create_admin():
    from flask_bcrypt import Bcrypt
    bcrypt = Bcrypt(app)
    hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')

    admin = User(
        email="admin@pharma.com",
        phone="admin",
        password=hashed_pw,
        is_admin=True,
        otp=None,
        otp_expiry=None,
        is_verified=True
    )
    db.session.add(admin)
    db.session.commit()

    return "✅ Admin User Created!"
# ------------------ Init ------------------
if __name__ == '__main__':
    load_dotenv()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=3000, debug=True)
