from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, Medicine, Order, Offer, Prescription
import os
from werkzeug.utils import secure_filename
from utils import send_order_email

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Handle POST request logic here
        flash('POST request received!')
        return redirect(url_for('main.home'))

    # Existing GET logic
    search_query = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    brand_filter = request.args.get('brand', '')

    medicines_query = Medicine.query

    if search_query:
        medicines_query = medicines_query.filter(
            (Medicine.name.ilike(f'%{search_query}%')) |
            (Medicine.medicine_name.ilike(f'%{search_query}%'))
        )

    if category_filter:
        medicines_query = medicines_query.filter(Medicine.category.ilike(f'%{category_filter}%'))

    if brand_filter:
        medicines_query = medicines_query.filter(Medicine.name.ilike(f'%{brand_filter}%'))

    medicines = medicines_query.all()
    offers = Offer.query.all()

    return render_template('home.html', medicines=medicines, offers=offers)

@main_bp.route('/category/<category>')
def category_filter(category):
    medicines = Medicine.query.filter(Medicine.category.ilike(f"%{category}%")).all()
    offers = Offer.query.all()
    return render_template('home.html', medicines=medicines, offers=offers)

@main_bp.route('/add_to_cart/<int:med_id>', methods=['POST'])
@login_required
def add_to_cart(med_id):
    quantity = int(request.form['quantity'])
    cart = session.get('cart', {})
    cart[str(med_id)] = cart.get(str(med_id), 0) + quantity
    session['cart'] = cart
    flash('Item added to cart!')
    return redirect(url_for('main.home'))

@main_bp.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    items = []
    total = 0
    for med_id, qty in cart.items():
        med = Medicine.query.get(int(med_id))
        if med:
            items.append({'medicine': med, 'quantity': qty, 'subtotal': med.price * qty})
            total += med.price * qty
    return render_template('cart.html', items=items, total=total)

@main_bp.route('/clear_cart')
@login_required
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared!')
    return redirect(url_for('main.cart'))

@main_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash('Cart is empty!')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        address = request.form.get('address')
        if not address:
            flash('Please provide a delivery address!', 'error')
            return render_template('checkout.html', items=[], total=0)

        prescription_filename = None
        if 'prescription' in request.files:
            file = request.files['prescription']
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join('static/uploads', filename)
                os.makedirs('static/uploads', exist_ok=True)
                file.save(filepath)
                prescription_filename = filename

        order_details_list = []
        for med_id_str, qty in cart.items():
            med_id = int(med_id_str)
            medicine = Medicine.query.get(med_id)
            if medicine and medicine.stock >= qty:
                discounted_price = medicine.price * (1 - medicine.discount / 100)
                subtotal = discounted_price * qty
                order = Order(
                    user_id=current_user.id,
                    medicine_id=med_id,
                    quantity=qty,
                    address=address,
                    prescription=prescription_filename,
                    status='Pending',
                    total=subtotal
                )
                db.session.add(order)

                # Update stock
                medicine.stock -= qty
                if medicine.stock < 0:
                    medicine.stock = 0

                order_details_list.append(f"{medicine.name} x{qty} - ₹{subtotal} (Original: ₹{medicine.price * qty}, Discount: {medicine.discount}%)")

        db.session.commit()

        # Send email to admin
        order_details = f'New Order from {current_user.email}\nAddress: {address}\nItems:\n' + '\n'.join(order_details_list)
        if prescription_filename:
            order_details += f'\nPrescription: {prescription_filename}'
        send_order_email('admin@pharma.com', order_details)  # Assuming admin email

        # Clear cart
        session.pop('cart', None)
        flash('✅ Order placed successfully!')
        return redirect(url_for('main.my_orders'))

    # GET request
    items = []
    total = 0
    for med_id, qty in cart.items():
        med = Medicine.query.get(int(med_id))
        if med:
            discounted_price = med.price * (1 - med.discount / 100)
            subtotal = discounted_price * qty
            items.append({'medicine': med, 'quantity': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('checkout.html', items=items, total=total)

@main_bp.route('/myorders')
@login_required
def my_orders():
    orders_raw = Order.query.filter_by(user_id=current_user.id).order_by(Order.id.desc()).all()
    prescriptions = Prescription.query.filter_by(user_id=current_user.id).order_by(Prescription.id.desc()).all()

    orders = []
    for order in orders_raw:
        med = Medicine.query.get(order.medicine_id)
        if med:
            order_data = {
                'order': order,
                'medicines': [{'image': med.image, 'name': med.name, 'quantity': order.quantity}]
            }
            orders.append(order_data)

    prescription_orders = []
    for prescription in prescriptions:
        prescription_data = {
            'prescription': prescription,
            'type': 'prescription'
        }
        prescription_orders.append(prescription_data)

    # Combine and sort by date (most recent first)
    all_items = orders + prescription_orders
    all_items.sort(key=lambda x: x['order'].ordered_at if 'order' in x else x['prescription'].submitted_at, reverse=True)

    return render_template('my_orders.html', orders=orders, prescriptions=prescriptions, all_items=all_items)

@main_bp.route('/order', methods=['GET'])
@login_required
def order_page():
    medicines = Medicine.query.all()
    return render_template('order.html', medicines=medicines)

@main_bp.route('/place_order', methods=['POST'])
@login_required
def place_order():
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('main.cart'))

    address = request.form.get('address')
    if not address:
        flash('Please provide a delivery address!', 'error')
        return redirect(url_for('main.checkout'))

    prescription_filename = None
    if 'prescription' in request.files:
        file = request.files['prescription']
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join('static/uploads', filename)
            os.makedirs('static/uploads', exist_ok=True)
            file.save(filepath)
            prescription_filename = filename

    orders = []
    order_details_list = []
    grand_total = 0
    for med_id_str, quantity in cart.items():
        med_id = int(med_id_str)
        med = Medicine.query.get(med_id)
        if med and med.stock >= quantity:
            discounted_price = med.price * (1 - med.discount / 100)
            subtotal = discounted_price * quantity
            order = Order(
                user_id=current_user.id,
                medicine_id=med_id,
                quantity=quantity,
                address=address,
                prescription=prescription_filename,
                status='Pending',
                total=subtotal
            )
            db.session.add(order)
            orders.append(order)
            order_details_list.append(f"{med.name} x{quantity} - ₹{subtotal} (Original: ₹{med.price * quantity}, Discount: {med.discount}%)")
            grand_total += subtotal

            # Update stock
            med.stock -= quantity
            if med.stock < 0:
                med.stock = 0

    db.session.commit()

    # Send email to admin
    order_details = f'New Order(s) from {current_user.email}\nAddress: {address}\nGrand Total: ₹{grand_total}\nItems:\n' + '\n'.join(order_details_list)
    if prescription_filename:
        order_details += f'\nPrescription: {prescription_filename}'
    send_order_email('admin@pharma.com', order_details)  # Assuming admin email

    # Clear cart
    session['cart'] = {}
    flash(f'Your order(s) have been placed successfully! Order ID(s): {[o.id for o in orders]}', 'success')
    return redirect(url_for('main.my_orders'))

@main_bp.route('/upload_prescription', methods=['GET', 'POST'])
@login_required
def upload_prescription():
    if request.method == 'POST':
        file = request.files['prescription']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join('static/uploads', filename)
            os.makedirs('static/uploads', exist_ok=True)
            file.save(filepath)
            prescription = Prescription(
                user_id=current_user.id,
                file_path=filename,
                disease=request.form.get('disease'),
                symptoms=request.form.get('symptoms'),
                prescription_details=request.form.get('prescription_details'),
                address=request.form.get('address')
            )
            db.session.add(prescription)
            db.session.commit()
            flash('Prescription uploaded successfully!')
            return redirect(url_for('main.home'))
    return render_template('upload_prescription.html')
