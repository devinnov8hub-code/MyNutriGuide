from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db

onboarding = Blueprint('onboarding', __name__)

@onboarding.route('/onboarding', methods=['GET', 'POST'])
@login_required
def onboarding_flow():
    if current_user.onboarding_complete:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        try:
            current_user.age = request.form.get('age', type=int)
            current_user.gender = request.form.get('gender')
            current_user.allergies = request.form.get('allergies')
            current_user.dietary_preferences = request.form.get('dietary_preferences')
            current_user.chronic_conditions = request.form.get('chronic_conditions')
            current_user.medications = request.form.get('medications')
            current_user.medical_history = request.form.get('medical_history')
            
            current_user.onboarding_complete = True
            db.session.commit()
            
            flash('Onboarding completed successfully!')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}')
            return redirect(url_for('onboarding.onboarding_flow'))

    return render_template('onboarding.html')
