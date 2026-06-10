@admin_bp.route('/admin/export_prescriptions_pdf')
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
