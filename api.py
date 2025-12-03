from flask import Blueprint, request, jsonify, session, url_for
from flask_login import login_required, current_user
from analysis import analyze_image_vision, generate_audio, save_temp_image, save_temp_audio
import uuid
import json

api = Blueprint('api', __name__)

@api.route('/api/upload', methods=['POST'])
@login_required
def upload_image():
    data = request.get_json()
    
    if not data or 'image_data' not in data:
        return jsonify({'error': 'No image data provided'}), 400
        
    image_data = data['image_data']
    
    # 1. Save image locally for display
    filename = f"{uuid.uuid4()}.jpg"
    saved_filename = save_temp_image(image_data, filename)
    
    if not saved_filename:
        return jsonify({'error': 'Failed to save image'}), 500

    # 2. Prepare user profile
    user_profile = {
        'allergies': current_user.allergies,
        'chronic_conditions': current_user.chronic_conditions,
        'dietary_preferences': current_user.dietary_preferences,
        'medications': current_user.medications
    }
    
    # 3. Analyze with OpenAI Vision (GPT-4o)
    analysis_text = analyze_image_vision(image_data, user_profile)

    json_analysis = json.loads(analysis_text)
    
    
    voice_response = json_analysis.get('voice_response', None)
    
    # 4. Generate Audio with ElevenLabs
    audio_base64 = generate_audio(voice_response)
    audio_filename = None
    if audio_base64:
        audio_filename = f"{uuid.uuid4()}.mp3"
        save_temp_audio(audio_base64, audio_filename)
    
    # 5. Store result in session
    session['last_scan_image'] = saved_filename
    session['last_scan_text'] = analysis_text
    session['last_scan_audio_filename'] = audio_filename
    
    return jsonify({
        'success': True,
        'redirect_url': url_for('main.breakdown')
    })
