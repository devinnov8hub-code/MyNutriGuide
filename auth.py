from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime
from authlib.integrations.flask_client import OAuth
import uuid
import requests
import os

auth = Blueprint('auth', __name__)
oauth = OAuth()

def get_google_oauth_client():
    try:
        return oauth.create_client('google')
    except Exception:
        return None

@auth.record_once
def on_load(state):
    oauth.init_app(state.app)
    # Only register Google OAuth if credentials are provided
    if state.app.config.get('GOOGLE_CLIENT_ID') and state.app.config.get('GOOGLE_CLIENT_SECRET'):
        oauth.register(
            name='google',
            client_id=state.app.config['GOOGLE_CLIENT_ID'],
            client_secret=state.app.config['GOOGLE_CLIENT_SECRET'],
            server_metadata_url=state.app.config.get('GOOGLE_DISCOVERY_URL', 'https://accounts.google.com/.well-known/openid-configuration'),
            client_kwargs={
                'scope': 'openid email profile'
            }
        )

@auth.route('/login/google')
def google_login():
    google = get_google_oauth_client()
    if not google:
        flash('Google OAuth is not configured. Please contact the administrator.')
        return redirect(url_for('auth.login'))
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth.route('/auth/callback')
def google_callback():
    google = get_google_oauth_client()
    if not google:
        flash('Google OAuth is not configured. Please contact the administrator.')
        return redirect(url_for('auth.login'))
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback if userinfo is not in token
            user_info = google.get('https://openidconnect.googleapis.com/v1/userinfo').json()
            
        email = user_info.get('email')
        first_name = user_info.get('given_name')
        last_name = user_info.get('family_name')
        
        # Fallback to splitting 'name' if given_name/family_name are missing
        if not first_name and user_info.get('name'):
            name_parts = user_info.get('name').split(' ', 1)
            first_name = name_parts[0]
            if len(name_parts) > 1:
                last_name = name_parts[1]
        
        # Ensure we have strings
        first_name = first_name or ''
        last_name = last_name or ''
        picture_url = user_info.get('picture')
        
        if not email:
            flash('Could not retrieve email from Google.')
            return redirect(url_for('auth.login'))
            
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Create new user
            # Generate a random password since they use Google
            random_password = str(uuid.uuid4())
            user = User(first_name=first_name, last_name=last_name, email=email)
            user.set_password(random_password)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully via Google!')

        # Download and save profile picture if available and user has default
        if picture_url and (not user.profile_picture or user.profile_picture == 'default_profile.svg'):
            try:
                response = requests.get(picture_url)
                if response.status_code == 200:
                    # Generate filename
                    filename = f"{uuid.uuid4().hex}_google.jpg"
                    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    file_path = os.path.join(upload_folder, filename)
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                        
                    user.profile_picture = filename
                    db.session.commit()
            except Exception as e:
                # Log error but don't fail login
                print(f"Failed to download Google profile picture: {e}")
            
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        if not user.onboarding_complete:
            return redirect(url_for('onboarding.onboarding_flow'))
            
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        flash(f'Google login failed: {str(e)}')
        return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user is None or not user.check_password(password):
            flash('Invalid email or password')
            return redirect(url_for('auth.login'))
        
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        if not user.onboarding_complete:
            return redirect(url_for('onboarding.onboarding_flow'))
            
        return redirect(url_for('main.dashboard'))
        
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not email or not password or len(password) < 6:
            flash('Invalid input. Password must be at least 6 characters.')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match.')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return redirect(url_for('auth.register'))
            
        user = User(first_name=first_name, last_name=last_name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
