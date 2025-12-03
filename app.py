from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from config import Config
from models import db, User
import json
from werkzeug.utils import secure_filename
import os
import uuid
from PIL import Image

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login = LoginManager(app)
    login.login_view = 'auth.login'

    @login.user_loader
    def load_user(id):
        return db.session.get(User, int(id))

    # Register Blueprints
    from auth import auth as auth_bp
    app.register_blueprint(auth_bp)

    from onboarding import onboarding as onboarding_bp
    app.register_blueprint(onboarding_bp)

    from api import api as api_bp
    app.register_blueprint(api_bp)

    # Main Blueprint for core routes
    from flask import Blueprint
    main = Blueprint('main', __name__)

    @main.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('main.dashboard'))
        return redirect(url_for('auth.login'))

    @main.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @main.route('/scan')
    @login_required
    def scan():
        return render_template('scan.html')

    @main.route('/.well-known/appspecific/com.chrome.devtools.json')
    def devtools_config():
        config = {
            "name": "R4I DevTools Extension",
            "version": "1.0",
            "description": "DevTools extension for R4I application",
            "devtools_page": url_for('static', filename='devtools.html', _external=True)
        }
        return json.dumps(config), 200, {'Content-Type': 'application/json'}

    @main.route('/breakdown')
    @login_required
    def breakdown():
        image_filename = session.get('last_scan_image')
        analysis_text = session.get('last_scan_text')
        audio_filename = session.get('last_scan_audio_filename')

        if analysis_text is None:
            analysis_text = '{}'
        
        try:
            analysis_data = json.loads(analysis_text)
        except (json.JSONDecodeError, TypeError):
            analysis_data = {
                'product_name': 'Unknown Product',
                'warnings': [],
                'summary': analysis_text if analysis_text != '{}' else 'No analysis data available.'
            }
            
        return render_template('breakdown.html', 
                             image_filename=image_filename, 
                             analysis=analysis_data,
                             audio_filename=audio_filename)

    @main.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            try:
                current_user.age = request.form.get('age', type=int)
                current_user.gender = request.form.get('gender')
                current_user.allergies = request.form.get('allergies')
                current_user.dietary_preferences = request.form.get('dietary_preferences')
                current_user.chronic_conditions = request.form.get('chronic_conditions')
                current_user.medications = request.form.get('medications')
                current_user.medical_history = request.form.get('medical_history')
                
                # Handle Profile Picture
                if 'profile_picture' in request.files:
                    file = request.files['profile_picture']
                    if file and file.filename:
                        filename = secure_filename(file.filename)
                        name_without_ext = os.path.splitext(filename)[0]
                        unique_filename = f"{uuid.uuid4().hex}_{name_without_ext}.webp"
                        
                        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
                        os.makedirs(upload_folder, exist_ok=True)
                        
                        image = Image.open(file)
                        file_path = os.path.join(upload_folder, unique_filename)
                        image.save(file_path, 'WEBP')
                        
                        current_user.profile_picture = unique_filename

                db.session.commit()
                flash('Profile updated successfully!')
                return redirect(url_for('main.profile'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred: {str(e)}')
        
        return render_template('profile.html')

    @main.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        if request.method == 'POST':
            # In a real app, you might update the .env file or a config file here
            # For now, we'll just flash a message that it's read-only in this demo
            flash('System prompt is currently managed via environment variables.')
            return redirect(url_for('main.settings'))
        
        current_prompt = app.config.get('OPENAI_SYSTEM_PROMPT', '')
        return render_template('settings.html', system_prompt=current_prompt)

    app.register_blueprint(main)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
