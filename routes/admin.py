from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from flask_login import login_required, current_user
from models import db, Medicine, Order, Offer, User, Prescription
from utils import send_email, generate_otp, send_delivery_otp_email, send_prescription_delivery_otp_email
from werkzeug.utils import secure_filename
import os
from config import Config
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from sqlalchemy.orm import joinedload

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        if 'add_offer' in request.form:
            title = request.form['title']
            desc = request.form['description']
            discount = int(request.form['discount'])
            valid_until = datetime.strptime(request.form['valid_until'], '%Y-%m-%d')
            offer = Offer(title=title, description=desc, discount=discount, valid_until=valid_until)
            db.session.add(offer)
            db.session.commit()
            flash("✅ Offer added!")
        elif 'add_prescription' in request.form:
            user_id = int(request.form['patient'])
            doctor_id = int(request.form['doctor'])
            medicine = request.form['medicine']
            dosage = request.form['dosage']
            approval_status = request.form['approval_status']
            date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            prescription = Prescription(
                user_id=user_id,
                doctor_id=doctor_id,
                medicine=medicine,
                dosage=dosage,
                status=approval_status,
                submitted_at=date,
                reviewed_at=datetime.utcnow() if approval_status == 'Approved' else None
            )
            db.session.add(prescription)
            db.session.commit()
            flash("✅ Prescription added!")
        else:
            medicine_name = request.form['medicine_name']
            name = request.form['name']
            med_type = request.form['type']
            age_group = request.form['age_group']
            category = request.form['category']
            price = float(request.form['price'])
            discount = int(request.form.get('discount', 0))
            stock = int(request.form['stock'])
            description = request.form.get('description', '')
            ingredients = request.form.get('ingredients', '')
            usage = request.form.get('usage', '')

            # Combine description, ingredients, and usage
            full_description = description
            if ingredients:
                full_description += f"\n\nIngredients: {ingredients}"
            if usage:
                full_description += f"\n\nUsage: {usage}"

            image_file = request.files['image']
            if image_file and image_file.filename:
                filename = secure_filename(image_file.filename)
                image_path = os.path.join('static/uploads', filename)
                image_file.save(image_path)
                image_url = '/static/uploads/' + filename
            else:
                image_url = ''

            new_med = Medicine(
                medicine_name=medicine_name,
                name=name,
                type=med_type,
                age_group=age_group,
                category=category,
                price=price,
                discount=discount,
                stock=stock,
                image=image_url,
                description=full_description
            )
            db.session.add(new_med)
            db.session.commit()
            flash('✅ Medicine added!')

    meds = Medicine.query.all()
    # Add discounted_price to each medicine dict
    medicines_with_discount = []
    for med in meds:
        discounted_price = med.price * (1 - med.discount / 100)
        medicines_with_discount.append({
            'medicine': med,
            'discounted_price': discounted_price
        })

    total_meds = Medicine.query.count()
    total_orders = Order.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    total_prescriptions = Prescription.query.count()
    # Get all distinct order statuses
    distinct_statuses = db.session.query(Order.status).distinct().all()
    status_labels = [status[0] for status in distinct_statuses] if distinct_statuses else ['Pending', 'Processing', 'Shipped', 'Delivered']

    # Calculate sales and counts by status
    from sqlalchemy import func
    sales_data = []
    order_counts = []
    for status in status_labels:
        sales = db.session.query(func.sum(Order.total)).filter(Order.status == status).scalar() or 0
        count = Order.query.filter_by(status=status).count()
        sales_data.append(sales)
        order_counts.append(count)

    # For backward compatibility, keep individual variables if needed
    pending_orders = order_counts[status_labels.index('Pending')] if 'Pending' in status_labels else 0
    processing_orders = order_counts[status_labels.index('Processing')] if 'Processing' in status_labels else 0
    shipped_orders = order_counts[status_labels.index('Shipped')] if 'Shipped' in status_labels else 0
    delivered_orders = order_counts[status_labels.index('Delivered')] if 'Delivered' in status_labels else 0

    pending_sales = sales_data[status_labels.index('Pending')] if 'Pending' in status_labels else 0
    processing_sales = sales_data[status_labels.index('Processing')] if 'Processing' in status_labels else 0
    shipped_sales = sales_data[status_labels.index('Shipped')] if 'Shipped' in status_labels else 0
    delivered_sales = sales_data[status_labels.index('Delivered')] if 'Delivered' in status_labels else 0
    # Split offers into active and expired for admin view
    today = datetime.utcnow().date()
    offers_active = Offer.query.filter(Offer.valid_until >= today).order_by(Offer.id.desc()).all()
    offers_expired = Offer.query.filter(Offer.valid_until < today).order_by(Offer.id.desc()).all()
    offers = offers_active
    orders = Order.query.options(joinedload(Order.user), joinedload(Order.medicine)).order_by(Order.id.desc()).all()
    prescriptions = Prescription.query.order_by(Prescription.id.desc()).all()
    pending_prescriptions = Prescription.query.filter_by(status='Doctor Approved').order_by(Prescription.id.desc()).limit(5).all()
    users = User.query.filter_by(is_admin=False, is_doctor=False).all()
    doctors = User.query.filter_by(is_doctor=True).all()

    return render_template('admin_dashboard.html',
        medicines=medicines_with_discount,
        total_meds=total_meds,
        total_orders=total_orders,
        total_users=total_users,
        total_prescriptions=total_prescriptions,
        pending_orders=pending_orders,
        processing_orders=processing_orders,
        shipped_orders=shipped_orders,
        delivered_orders=delivered_orders,
        pending_sales=pending_sales,
        processing_sales=processing_sales,
        shipped_sales=shipped_sales,
        delivered_sales=delivered_sales,
        status_labels=status_labels,
        sales_data=sales_data,
        order_counts=order_counts,
        offers=offers,
        offers_active=offers_active,
        offers_expired=offers_expired,
        orders=orders,
        prescriptions=prescriptions,
        pending_prescriptions=pending_prescriptions,
        users=users,
        doctors=doctors
    )

@admin_bp.route('/delete_medicine/<int:med_id>', methods=['POST'])
@login_required
def delete_medicine(med_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))
    med = Medicine.query.get(med_id)
    if med:
        # Check if there are any orders for this medicine
        if Order.query.filter_by(medicine_id=med_id).first():
            flash("Cannot delete medicine as it has associated orders.")
            return redirect(url_for('admin.admin_dashboard'))
        db.session.delete(med)
        db.session.commit()
        flash(f"{med.name} deleted!")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/delete_offer/<int:offer_id>', methods=['POST'])
@login_required
def delete_offer(offer_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))
    offer = Offer.query.get_or_404(offer_id)
    db.session.delete(offer)
    db.session.commit()
    flash("✅ Offer deleted!")
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/edit_offer/<int:offer_id>', methods=['GET', 'POST'])
@login_required
def edit_offer(offer_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    offer = Offer.query.get_or_404(offer_id)

    if request.method == 'POST':
        offer.title = request.form['title']
        offer.description = request.form['description']
        offer.discount = int(request.form['discount'])
        offer.valid_until = datetime.strptime(request.form['valid_until'], '%Y-%m-%d')
        db.session.commit()
        flash("✅ Offer updated successfully!")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/edit_offer.html', offer=offer)

@admin_bp.route('/orders')
@login_required
def view_orders():
    if not current_user.is_admin:
        return redirect(url_for('main.home'))
    orders = Order.query.options(joinedload(Order.user), joinedload(Order.medicine)).order_by(Order.id.desc()).all()

    # Build status labels and sales/order counts to support charts in the template
    from sqlalchemy import func
    distinct_statuses = db.session.query(Order.status).distinct().all()
    status_labels = [status[0] for status in distinct_statuses] if distinct_statuses else ['Pending', 'Processing', 'Shipped', 'Delivered']

    sales_data = []
    order_counts = []
    for status in status_labels:
        sales = db.session.query(func.sum(Order.total)).filter(Order.status == status).scalar() or 0
        count = Order.query.filter_by(status=status).count()
        sales_data.append(sales)
        order_counts.append(count)

    return render_template('admin_orders.html', orders=orders, status_labels=status_labels, sales_data=sales_data, order_counts=order_counts)

@admin_bp.route('/update_order_status/<int:order_id>', methods=['GET', 'POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    order = Order.query.get(order_id)
    if order:
        if request.method == 'POST':
            new_status = request.form['status']
        else:
            new_status = request.args.get('status')

        # If status is being set to 'delivered', generate and send OTP
        if new_status.lower() == 'delivered':
            otp = generate_otp()
            order.delivery_otp = otp
            order.delivery_otp_expiry = datetime.utcnow() + timedelta(hours=24)
            user = User.query.get(order.user_id)
            if user and user.email:
                send_delivery_otp_email(user.email, otp)
            flash('OTP sent to customer for delivery confirmation!')
        else:
            order.status = new_status

        db.session.commit()

        # जर status 'Rejected' असेल तर ईमेल पाठवा
        if new_status == 'Rejected':
            user = User.query.get(order.user_id)
            if user and user.email:
                send_email(
                    to_email=user.email,
                    subject='Order Rejected ❌',
                    body=f"Dear {user.email},\n\nWe're sorry to inform you that your order #{order.id} has been rejected.\n\n- Pharma Team"
                )
        flash('Order status updated!')
    return redirect(url_for('admin.view_orders'))

@admin_bp.route('/edit_medicine/<int:med_id>', methods=['GET', 'POST'])
@login_required
def edit_medicine(med_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    medicine = Medicine.query.get_or_404(med_id)

    if request.method == 'POST':
        medicine.medicine_name = request.form['medicine_name']
        medicine.name = request.form['name']
        medicine.type = request.form['type']
        medicine.age_group = request.form['age_group']
        medicine.category = request.form['category']
        medicine.price = float(request.form['price'])
        medicine.discount = int(request.form.get('discount', 0))
        medicine.stock = int(request.form['stock'])
        description = request.form.get('description', '')
        ingredients = request.form.get('ingredients', '')
        usage = request.form.get('usage', '')

        # Combine description, ingredients, and usage
        full_description = description
        if ingredients:
            full_description += f"\n\nIngredients: {ingredients}"
        if usage:
            full_description += f"\n\nUsage: {usage}"

        medicine.description = full_description

        image_file = request.files.get('image')
        if image_file and image_file.filename:
            filename = secure_filename(image_file.filename)
            image_path = os.path.join('static/uploads', filename)
            image_file.save(image_path)
            medicine.image = '/static/uploads/' + filename

        db.session.commit()
        flash('Medicine updated successfully!')
        return redirect(url_for('admin.admin_dashboard'))

    # For GET, render the edit form with current data
    # Split description into parts if needed
    description = medicine.description or ''
    ingredients = ''
    usage = ''
    if '\n\nIngredients:' in description:
        parts = description.split('\n\nIngredients:')
        description = parts[0]
        remaining = parts[1]
        if '\n\nUsage:' in remaining:
            ing_usage = remaining.split('\n\nUsage:')
            ingredients = ing_usage[0].strip()
            usage = ing_usage[1].strip()
        else:
            ingredients = remaining.strip()
    elif '\n\nUsage:' in description:
        parts = description.split('\n\nUsage:')
        description = parts[0]
        usage = parts[1].strip()

    return render_template('edit_medicine.html', medicine=medicine, description=description, ingredients=ingredients, usage=usage)

@admin_bp.route('/create-admin')
def create_admin():
    admin_user = User.query.filter_by(email='admin@pharma.com').first()
    if admin_user:
        return "Admin already exists! Email: admin@pharma.com, Password: admin123"
    else:
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        hashed_pw = bcrypt.generate_password_hash("admin123").decode('utf-8')

        admin = User(
            email="admin@pharma.com",
            phone="1234567890",
            password=hashed_pw,
            is_admin=True,
            otp=None,
            otp_expiry=None,
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()

        return "Admin created successfully! Email: admin@pharma.com, Password: admin123"

@admin_bp.route('/create-doctor')
def create_doctor():
    doctor_user = User.query.filter_by(email='doctor@pharma.com').first()
    if doctor_user:
        return "Doctor already exists! Email: doctor@pharma.com, Password: doctor123"
    else:
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        hashed_pw = bcrypt.generate_password_hash("doctor123").decode('utf-8')

        doctor = User(
            email="doctor@pharma.com",
            phone="9876543210",
            password=hashed_pw,
            is_doctor=True,
            otp=None,
            otp_expiry=None,
            is_verified=True
        )
        db.session.add(doctor)
        db.session.commit()

        return "Doctor created successfully! Email: doctor@pharma.com, Password: doctor123"

@admin_bp.route('/prescriptions')
@login_required
def admin_prescriptions():
    if not current_user.is_admin:
        return redirect(url_for('main.home'))
    prescriptions = Prescription.query.filter_by(status='Doctor Approved').all()
    return render_template('admin_prescriptions.html', prescriptions=prescriptions)

@admin_bp.route('/verify/<int:prescription_id>', methods=['POST'])
@login_required
def admin_verify(prescription_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))
    prescription = Prescription.query.get_or_404(prescription_id)
    action = request.form.get('action')
    if action == 'approve':
        prescription.admin_id = current_user.id
        prescription.status = 'Approved'
        prescription.reviewed_at = datetime.utcnow()
        flash('Prescription approved by admin.')
    elif action == 'reject':
        prescription.status = 'Rejected'
        prescription.admin_id = current_user.id
        prescription.reviewed_at = datetime.utcnow()
        # Send rejection email
        user = User.query.get(prescription.user_id)
        if user and user.email:
            send_email(
                to_email=user.email,
                subject='Prescription Rejected ❌',
                body=f"Dear {user.email},\n\nWe're sorry to inform you that your prescription #{prescription.id} has been rejected by the admin.\n\n- Pharma Team"
            )
        flash('Prescription rejected by admin.')
    db.session.commit()
    return redirect(url_for('admin.admin_dashboard'))
@admin_bp.route('/update_prescription_status/<int:prescription_id>', methods=['GET', 'POST'])
@login_required
def update_prescription_status(prescription_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    prescription = Prescription.query.get(prescription_id)
    if prescription:
        if request.method == 'POST':
            new_status = request.form['status']
        else:
            new_status = request.args.get('status')

        # If status is being set to 'delivered', generate and send OTP
        if new_status.lower() == 'delivered':
            otp = generate_otp()
            prescription.delivery_otp = otp
            prescription.delivery_otp_expiry = datetime.utcnow() + timedelta(hours=24)
            prescription.status = 'Awaiting OTP Verification'
            user = User.query.get(prescription.user_id)
            if user and user.email:
                send_prescription_delivery_otp_email(user.email, otp)
            flash('OTP sent to patient for prescription delivery confirmation!')
        else:
            prescription.status = new_status

        prescription.admin_id = current_user.id
        prescription.reviewed_at = datetime.utcnow()
        db.session.commit()

        # Send email based on status (only for non-delivered statuses)
        if new_status.lower() != 'delivered':
            user = User.query.get(prescription.user_id)
            if user and user.email:
                if new_status == 'Approved':
                    send_email(
                        to_email=user.email,
                        subject='Prescription Approved ✅',
                        body=f"Dear {user.email},\n\nYour prescription #{prescription.id} has been approved by the admin.\n\n- Pharma Team"
                    )
                elif new_status == 'Rejected':
                    send_email(
                        to_email=user.email,
                        subject='Prescription Rejected ❌',
                        body=f"Dear {user.email},\n\nWe're sorry to inform you that your prescription #{prescription.id} has been rejected by the admin.\n\n- Pharma Team"
                    )
        flash('Prescription status updated!')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/export_prescriptions_pdf')

@login_required

def export_prescriptions_pdf():

    if not current_user.is_admin:

        return redirect(url_for('main.home'))



    prescriptions = Prescription.query.order_by(Prescription.id.desc()).all()



    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    elements = []



    data = [['ID', 'Patient', 'Doctor', 'Medicine', 'Dosage', 'Status', 'Date']]

    for p in prescriptions:

        data.append([

            str(p.id),

            p.user.email,

            p.doctor.email,

            p.medicine,

            p.dosage,

            p.status,

            p.submitted_at.strftime('%Y-%m-%d')

        ])



    table = Table(data)

    table.setStyle(TableStyle([

        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),

        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),

        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),

        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),

        ('FONTSIZE', (0, 0), (-1, 0), 14),

        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),

        ('GRID', (0, 0), (-1, -1), 1, colors.black)

    ]))



    elements.append(table)

    doc.build(elements)



    buffer.seek(0)

    response = make_response(buffer.getvalue())

    response.headers['Content-Type'] = 'application/pdf'

    response.headers['Content-Disposition'] = 'attachment; filename=prescriptions.pdf'

    return response

@admin_bp.route('/verify_delivery_otp/<int:order_id>', methods=['POST'])
@login_required
def verify_delivery_otp(order_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    order = Order.query.get_or_404(order_id)
    otp_input = request.form.get('otp')

    if not order.delivery_otp or not order.delivery_otp_expiry:
        flash('No OTP found for this order.')
        return redirect(url_for('admin.admin_dashboard'))

    if datetime.utcnow() > order.delivery_otp_expiry:
        flash('OTP has expired.')
        return redirect(url_for('admin.admin_dashboard'))

    if otp_input == order.delivery_otp:
        order.status = 'Delivered'
        order.delivery_otp = None  # Clear OTP after successful verification
        order.delivery_otp_expiry = None
        db.session.commit()
        flash('Delivery confirmed successfully!')
    else:
        flash('Invalid OTP. Please try again.')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/verify_prescription_delivery_otp/<int:prescription_id>', methods=['POST'])
@login_required
def verify_prescription_delivery_otp(prescription_id):
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    prescription = Prescription.query.get_or_404(prescription_id)
    otp_input = request.form.get('otp')

    if not prescription.delivery_otp or not prescription.delivery_otp_expiry:
        flash('No OTP found for this prescription.')
        return redirect(url_for('admin.admin_dashboard'))

    if datetime.utcnow() > prescription.delivery_otp_expiry:
        flash('OTP has expired.')
        return redirect(url_for('admin.admin_dashboard'))

    if otp_input == prescription.delivery_otp:
        prescription.status = 'Delivered'
        prescription.delivery_otp = None  # Clear OTP after successful verification
        prescription.delivery_otp_expiry = None
        db.session.commit()
        flash('Prescription delivery confirmed successfully!')
    else:
        flash('Invalid OTP. Please try again.')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/bulk_delete_medicines', methods=['POST'])
@login_required
def bulk_delete_medicines():
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    medicine_ids = request.form.getlist('medicine_ids')
    if not medicine_ids:
        flash('No medicines selected for deletion.')
        return redirect(url_for('admin.admin_dashboard'))

    deleted_count = 0
    for med_id in medicine_ids:
        med = Medicine.query.get(int(med_id))
        if med:
            # Check if there are any orders for this medicine
            if Order.query.filter_by(medicine_id=int(med_id)).first():
                flash(f"Cannot delete {med.name} as it has associated orders.")
                continue
            db.session.delete(med)
            deleted_count += 1

    db.session.commit()
    if deleted_count > 0:
        flash(f'Successfully deleted {deleted_count} medicine(s)!')
    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/export_medicines')
@login_required
def export_medicines():
    if not current_user.is_admin:
        return redirect(url_for('main.home'))

    ids = request.args.getlist('ids')
    if ids:
        medicines = Medicine.query.filter(Medicine.id.in_([int(id) for id in ids])).all()
    else:
        medicines = Medicine.query.all()

    # Create CSV content
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Medicine Name', 'Brand Name', 'Type', 'Category', 'Price', 'Discount', 'Stock', 'Description'])

    for med in medicines:
        writer.writerow([
            med.id,
            med.medicine_name,
            med.name,
            med.type,
            med.category,
            med.price,
            med.discount,
            med.stock,
            med.description.replace('\n', ' ').replace('\r', '')  # Clean description
        ])

    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=medicines.csv'
    return response

