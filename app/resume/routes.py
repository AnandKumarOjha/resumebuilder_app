import io
import re
from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file, abort
from flask_login import login_required, current_user
from app import db
from app.models import ResumeRole, PersonalInfo
from app.resume.pdf_generator import generate_pdf

resume = Blueprint('resume', __name__)

@resume.route('/download/pdf/<int:role_id>')
@login_required
def download_pdf(role_id):
    """
    Download route per Phase 3 & Phase 4 specifications:
    Checks if current_user.is_premium:
      - If True, renders the template and serves the PDF file.
      - If False, redirects to the checkout/payment page.
    """
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        abort(403)

    # Phase 4: Monetization paywall check
    if not current_user.is_premium:
        flash('PDF downloads require an active PRO / Premium membership. Please upgrade below to download unlimited PDF resumes.', 'warning')
        return redirect(url_for('payments.upgrade', role_id=role.id))

    template_name = request.args.get('template', 'simple').lower()
    template_file = 'resume/modern_template.html' if template_name == 'modern' else 'resume/simple_template.html'
    
    personal_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
    
    html_content = render_template(
        template_file,
        role=role,
        personal_info=personal_info,
        user=current_user
    )

    try:
        pdf_data = generate_pdf(html_content)
    except Exception as e:
        flash(f'Failed to generate PDF: {str(e)}', 'danger')
        return redirect(url_for('dashboard.role_detail', role_id=role.id))

    # Sanitize role name for file attachment name
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', role.role_name)
    filename = f"{safe_name}_Resume.pdf"

    return send_file(
        io.BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@resume.route('/preview/<int:role_id>')
@login_required
def preview_resume(role_id):
    """
    In-browser preview of the generated resume template.
    Allows students to preview layout before downloading.
    """
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        abort(403)

    template_name = request.args.get('template', 'simple').lower()
    template_file = 'resume/modern_template.html' if template_name == 'modern' else 'resume/simple_template.html'
    
    personal_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
    
    resume_html = render_template(
        template_file,
        role=role,
        personal_info=personal_info,
        user=current_user
    )

    return render_template(
        'resume/preview.html',
        role=role,
        personal_info=personal_info,
        template_name=template_name,
        resume_html=resume_html
    )
