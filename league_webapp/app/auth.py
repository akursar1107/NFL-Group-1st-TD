"""
Authentication routes - login, logout, password management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from . import db
from .models import User
from .forms import LoginForm, ChangePasswordForm, SetPasswordForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by username
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Your account has been deactivated. Please contact an administrator.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Check if user needs to set initial password
        if not user.password_hash:
            flash('Please set your password first.', 'info')
            return redirect(url_for('auth.set_password', user_id=user.id))
        
        # Log the user in
        login_user(user, remember=form.remember_me.data)
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        flash(f'Welcome back, {user.display_name or user.username}!', 'success')
        
        # Redirect to next page or home
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('main.index'))
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password for logged-in user"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.change_password'))
        
        # Set new password
        current_user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Your password has been changed successfully.', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/set-password/<int:user_id>', methods=['GET', 'POST'])
def set_password(user_id):
    """Set initial password (for users migrated without passwords)"""
    user = User.query.get_or_404(user_id)
    
    # Only allow if user has no password set
    if user.password_hash:
        flash('Password already set. Please use login.', 'info')
        return redirect(url_for('auth.login'))
    
    form = SetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        
        flash('Password set successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/set_password.html', form=form, user=user)
