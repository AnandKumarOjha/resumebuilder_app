from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required, current_user
from app import db
from app.models import PersonalInfo, ResumeRole, Experience, Education, Skill
from app.forms import PersonalInfoForm, ResumeRoleForm, ExperienceForm, EducationForm, SkillForm

dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard.route('/')
@login_required
def index():
    personal_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
    roles = ResumeRole.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/index.html', personal_info=personal_info, roles=roles)

@dashboard.route('/personal-info', methods=['GET', 'POST'])
@login_required
def personal_info():
    info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
    form = PersonalInfoForm(obj=info)
    
    if form.validate_on_submit():
        if not info:
            info = PersonalInfo(user_id=current_user.id)
            db.session.add(info)
        
        info.first_name = form.first_name.data
        info.last_name = form.last_name.data
        info.phone = form.phone.data
        info.address = form.address.data
        info.linkedin = form.linkedin.data
        info.portfolio = form.portfolio.data
        
        db.session.commit()
        flash('Personal information updated successfully!', 'success')
        return redirect(url_for('dashboard.index'))
        
    return render_template('dashboard/personal_info.html', form=form)

@dashboard.route('/role/new', methods=['GET', 'POST'])
@login_required
def create_role():
    form = ResumeRoleForm()
    if form.validate_on_submit():
        role = ResumeRole(
            user_id=current_user.id,
            role_name=form.role_name.data,
            summary=form.summary.data
        )
        db.session.add(role)
        db.session.commit()
        flash(f'Role "{role.role_name}" created successfully!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=role.id))
    return render_template('dashboard/role_form.html', form=form, title="Create New Job Role")

@dashboard.route('/role/<int:role_id>')
@login_required
def role_detail(role_id):
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard.index'))
    personal_info = PersonalInfo.query.filter_by(user_id=current_user.id).first()
    return render_template('dashboard/role_detail.html', role=role, personal_info=personal_info)

@dashboard.route('/role/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = ResumeRoleForm(obj=role)
    if form.validate_on_submit():
        role.role_name = form.role_name.data
        role.summary = form.summary.data
        db.session.commit()
        flash(f'Role "{role.role_name}" updated!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=role.id))
    return render_template('dashboard/role_form.html', form=form, title=f"Edit Role: {role.role_name}")

@dashboard.route('/role/<int:role_id>/delete', methods=['POST'])
@login_required
def delete_role(role_id):
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id == current_user.id:
        db.session.delete(role)
        db.session.commit()
        flash('Role deleted.', 'info')
    return redirect(url_for('dashboard.index'))

# --- Experience CRUD ---
@dashboard.route('/role/<int:role_id>/experience/add', methods=['GET', 'POST'])
@login_required
def add_experience(role_id):
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        return redirect(url_for('dashboard.index'))
    
    form = ExperienceForm()
    if form.validate_on_submit():
        exp = Experience(
            role_id=role.id,
            company=form.company.data,
            job_title=form.job_title.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            description=form.description.data
        )
        db.session.add(exp)
        db.session.commit()
        flash('Experience added!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=role.id))
    return render_template('dashboard/item_form.html', form=form, title=f"Add Experience for {role.role_name}")

@dashboard.route('/experience/<int:exp_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_experience(exp_id):
    exp = db.get_or_404(Experience, exp_id)
    if exp.role.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = ExperienceForm(obj=exp)
    if form.validate_on_submit():
        exp.company = form.company.data
        exp.job_title = form.job_title.data
        exp.start_date = form.start_date.data
        exp.end_date = form.end_date.data
        exp.description = form.description.data
        db.session.commit()
        flash('Experience updated!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=exp.role_id))
    return render_template('dashboard/item_form.html', form=form, title=f"Edit Experience: {exp.job_title}")

@dashboard.route('/experience/<int:exp_id>/delete', methods=['POST'])
@login_required
def delete_experience(exp_id):
    exp = db.get_or_404(Experience, exp_id)
    role_id = exp.role_id
    if exp.role.user_id == current_user.id:
        db.session.delete(exp)
        db.session.commit()
        flash('Experience removed.', 'info')
    return redirect(url_for('dashboard.role_detail', role_id=role_id))

# --- Education CRUD ---
@dashboard.route('/role/<int:role_id>/education/add', methods=['GET', 'POST'])
@login_required
def add_education(role_id):
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        return redirect(url_for('dashboard.index'))
    
    form = EducationForm()
    if form.validate_on_submit():
        edu = Education(
            role_id=role.id,
            institution=form.institution.data,
            degree=form.degree.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(edu)
        db.session.commit()
        flash('Education added!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=role.id))
    return render_template('dashboard/item_form.html', form=form, title=f"Add Education for {role.role_name}")

@dashboard.route('/education/<int:edu_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_education(edu_id):
    edu = db.get_or_404(Education, edu_id)
    if edu.role.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('dashboard.index'))
    
    form = EducationForm(obj=edu)
    if form.validate_on_submit():
        edu.institution = form.institution.data
        edu.degree = form.degree.data
        edu.start_date = form.start_date.data
        edu.end_date = form.end_date.data
        db.session.commit()
        flash('Education updated!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=edu.role_id))
    return render_template('dashboard/item_form.html', form=form, title=f"Edit Education: {edu.degree}")

@dashboard.route('/education/<int:edu_id>/delete', methods=['POST'])
@login_required
def delete_education(edu_id):
    edu = db.get_or_404(Education, edu_id)
    role_id = edu.role_id
    if edu.role.user_id == current_user.id:
        db.session.delete(edu)
        db.session.commit()
        flash('Education removed.', 'info')
    return redirect(url_for('dashboard.role_detail', role_id=role_id))

# --- Skill CRUD ---
@dashboard.route('/role/<int:role_id>/skill/add', methods=['GET', 'POST'])
@login_required
def add_skill(role_id):
    role = db.get_or_404(ResumeRole, role_id)
    if role.user_id != current_user.id:
        return redirect(url_for('dashboard.index'))
    
    form = SkillForm()
    if form.validate_on_submit():
        skill = Skill(role_id=role.id, skill_name=form.skill_name.data.strip())
        db.session.add(skill)
        db.session.commit()
        flash('Skill added!', 'success')
        return redirect(url_for('dashboard.role_detail', role_id=role.id))
    return render_template('dashboard/item_form.html', form=form, title=f"Add Skill for {role.role_name}")

@dashboard.route('/skill/<int:skill_id>/delete', methods=['POST'])
@login_required
def delete_skill(skill_id):
    skill = db.get_or_404(Skill, skill_id)
    role_id = skill.role_id
    if skill.role.user_id == current_user.id:
        db.session.delete(skill)
        db.session.commit()
        flash('Skill removed.', 'info')
    return redirect(url_for('dashboard.role_detail', role_id=role_id))