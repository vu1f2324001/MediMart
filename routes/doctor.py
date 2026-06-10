from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Prescription, User
from datetime import datetime
from utils import send_email

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if not current_user.is_doctor:
        flash('Access denied!')
        return redirect(url_for('main.home'))

    all_prescriptions = Prescription.query.all()
    pending_count = len([p for p in all_prescriptions if p.status == 'Pending'])
    approved_count = len([p for p in all_prescriptions if p.status == 'Approved'])
    rejected_count = len([p for p in all_prescriptions if p.status == 'Rejected'])

    # Filtering
    search = request.args.get('search', '')
    status_filter = request.args.get('status', 'all')
    date_filter = request.args.get('date', '')

    prescriptions = all_prescriptions
    if search:
        prescriptions = [p for p in prescriptions if search.lower() in p.user.email.lower()]
    if status_filter != 'all':
        prescriptions = [p for p in prescriptions if p.status == status_filter]
    if date_filter:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        prescriptions = [p for p in prescriptions if p.submitted_at.date() == filter_date]

    return render_template('doctor.html', prescriptions=prescriptions, pending_count=pending_count, approved_count=approved_count, rejected_count=rejected_count, search=search, status_filter=status_filter, date_filter=date_filter)

@doctor_bp.route('/doctor_approve/<int:prescription_id>', methods=['POST'])
@login_required
def doctor_approve(prescription_id):
    if not current_user.is_doctor:
        flash('Access denied!')
        return redirect(url_for('main.home'))
    
    prescription = Prescription.query.get_or_404(prescription_id)
    prescription.status = 'Doctor Approved'
    prescription.doctor_id = current_user.id
    prescription.reviewed_at = datetime.utcnow()
    prescription.doctor_notes = request.form.get('notes', '')
    db.session.commit()
    
    flash('Prescription approved successfully!')
    return redirect(url_for('doctor.doctor_dashboard'))

@doctor_bp.route('/doctor_reject/<int:prescription_id>', methods=['POST'])
@login_required
def doctor_reject(prescription_id):
    if not current_user.is_doctor:
        flash('Access denied!')
        return redirect(url_for('main.home'))
    
    prescription = Prescription.query.get_or_404(prescription_id)
    prescription.status = 'Rejected'
    prescription.doctor_id = current_user.id
    prescription.reviewed_at = datetime.utcnow()
    prescription.rejection_reason = request.form.get('notes', '')
    db.session.commit()
    
    # Send rejection email to user
    user = prescription.user
    send_email(
        to_email=user.email,
        subject='Prescription Rejected',
        body=f"Dear {user.email},\n\nYour prescription has been rejected by the doctor.\n\nReason: {prescription.rejection_reason}\n\nPlease contact support if you have any questions.\n\n- Pharma Team"
    )
    flash('Prescription rejected and email sent to user.', 'danger')
    
    return redirect(url_for('doctor.doctor_dashboard'))
