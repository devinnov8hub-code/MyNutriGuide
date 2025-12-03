from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
from config import Config
from models import db, User
import json

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
    app.run(debug=True, port=5005, host='0.0.0.0')
